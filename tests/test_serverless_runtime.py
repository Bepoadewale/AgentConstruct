from __future__ import annotations

import io
import json
from pathlib import Path

import pytest
from davdeploy import db, lambda_cognito_link, policy, security
from davdeploy.domain import PolicyResult
from davdeploy.lambda_policy import handler as policy_handler

ROOT = Path(__file__).resolve().parents[1]


def test_database_url_requires_complete_data_api_configuration(monkeypatch):
    monkeypatch.setenv("DAVDEPLOY_AURORA_CLUSTER_ARN", "arn:cluster")
    monkeypatch.delenv("DAVDEPLOY_DATABASE_SECRET_ARN", raising=False)
    with pytest.raises(RuntimeError, match="both cluster and secret"):
        db.database_url()


def test_data_api_engine_uses_arn_connect_arguments(monkeypatch):
    captured = {}
    monkeypatch.setenv("DAVDEPLOY_AURORA_CLUSTER_ARN", "arn:cluster")
    monkeypatch.setenv("DAVDEPLOY_DATABASE_SECRET_ARN", "arn:secret")
    monkeypatch.setenv("DAVDEPLOY_DATABASE_NAME", "controlplane")

    def fake_create_engine(url, **kwargs):
        captured.update(url=url, **kwargs)
        return object()

    monkeypatch.setattr(db, "create_engine", fake_create_engine)
    db.make_engine()
    assert captured["url"] == "postgresql+auroradataapi://:@/controlplane"
    assert captured["connect_args"] == {
        "aurora_cluster_arn": "arn:cluster",
        "secret_arn": "arn:secret",
    }
    assert captured["pool_pre_ping"] is False


def test_policy_lambda_preserves_approval_boundary():
    result = policy_handler(
        {
            "input": {
                "principal": {"subject": "u", "organization_id": "o"},
                "spec": {"environments": ["production"], "monthly_budget_usd": 100},
                "action": "DEPLOY",
            }
        },
        None,
    )
    assert result["result"]["result"] == PolicyResult.APPROVAL_REQUIRED


def test_policy_client_invokes_lambda_and_parses_decision(monkeypatch):
    class Lambda:
        def invoke(self, **kwargs):
            assert kwargs["FunctionName"] == "policy-arn"
            return {
                "Payload": io.BytesIO(
                    json.dumps(
                        {"result": {"result": "ALLOW", "reason": "tested"}}
                    ).encode()
                )
            }

    monkeypatch.setattr(policy.boto3, "client", lambda service: Lambda())
    client = policy.PolicyClient()
    client.function_arn = "policy-arn"
    decision = client._invoke_lambda({"safe": True})
    assert decision.result == PolicyResult.ALLOW


def test_cognito_linker_only_links_verified_google_identity(monkeypatch):
    calls = []

    class Cognito:
        def list_users(self, **kwargs):
            return {"Users": [{"Username": "native-user"}]}

        def admin_link_provider_for_user(self, **kwargs):
            calls.append(kwargs)

    monkeypatch.setattr(lambda_cognito_link.boto3, "client", lambda service: Cognito())
    event = {
        "triggerSource": "PreSignUp_ExternalProvider",
        "userPoolId": "pool",
        "userName": "Google_123",
        "request": {
            "userAttributes": {
                "email": "Person@example.com",
                "email_verified": "true",
            }
        },
        "response": {},
    }
    result = lambda_cognito_link.handler(event, None)
    assert calls[0]["DestinationUser"]["ProviderAttributeValue"] == "native-user"
    assert result["response"]["autoConfirmUser"] is True


def test_cognito_access_token_client_id_is_accepted_as_audience(monkeypatch):
    verifier = security.JwksIdentityVerifier("https://example.test/jwks", "issuer", "client")
    verifier.client = type(
        "Client", (), {"get_signing_key_from_jwt": lambda self, token: type("Key", (), {"key": "key"})()}
    )()
    monkeypatch.setattr(
        security.jwt,
        "decode",
        lambda *args, **kwargs: {
            "sub": "subject",
            "exp": 9999999999,
            "client_id": "client",
            "token_use": "id",
            "email": "person@example.com",
            "email_verified": True,
        },
    )
    claims = verifier.verify_claims("token")
    assert claims.email == "person@example.com"
    assert claims.email_verified is True


def test_cognito_access_token_is_rejected_when_identity_token_is_required(monkeypatch):
    verifier = security.JwksIdentityVerifier(
        "https://example.test/jwks",
        "https://cognito-idp.us-east-1.amazonaws.com/pool",
        "client",
    )
    verifier.client = type(
        "Client",
        (),
        {
            "get_signing_key_from_jwt": lambda self, token: type(
                "Key", (), {"key": "key"}
            )()
        },
    )()
    monkeypatch.setattr(
        security.jwt,
        "decode",
        lambda *args, **kwargs: {
            "sub": "subject",
            "exp": 9999999999,
            "client_id": "client",
            "token_use": "access",
        },
    )
    with pytest.raises(security.HTTPException) as error:
        verifier.verify_claims("token")
    assert error.value.status_code == 401


def test_serverless_stack_has_no_nat_gateway_or_lambda_vpc_attachment():
    terraform = (ROOT / "infrastructure/terraform/serverless-control-plane/main.tf").read_text()
    assert 'resource "aws_nat_gateway"' not in terraform
    assert 'resource "aws_internet_gateway"' not in terraform
    assert "vpc_config" not in terraform
    assert "enable_http_endpoint            = true" in terraform


def test_serverless_stack_keeps_google_secret_out_of_terraform_state():
    terraform_root = ROOT / "infrastructure/terraform/serverless-control-plane"
    contract = "\n".join(path.read_text() for path in terraform_root.glob("*.tf"))
    assert "google_client_secret" not in contract
    assert "aws_cognito_identity_provider" not in contract


def test_serverless_stack_pins_an_orderable_aurora_postgresql_version():
    variables = (
        ROOT / "infrastructure/terraform/serverless-control-plane/variables.tf"
    ).read_text()
    assert 'default     = "16.15"' in variables
    assert 'default     = "16.6"' not in variables
