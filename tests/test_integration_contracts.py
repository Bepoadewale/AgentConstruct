from __future__ import annotations

from agentconstruct.execution_profiles import execution_profile
from agentconstruct.integrations import FixtureAwsDiscovery, FixtureGitHubConnection


def test_github_fixture_models_reviewed_desired_state_and_webhook_contracts():
    github = FixtureGitHubConnection()
    pull_request = github.publish_reviewed_desired_state(
        "installation-1", "example/api", "desired/state.yaml", "safe fixture content"
    )
    assert pull_request.status == "SIMULATED"
    assert pull_request.required_checks == ("agentconstruct-plan", "agentconstruct-policy")
    webhook = github.validate_webhook("push", "delivery-1", "fixture-sha256=valid")
    assert webhook.verification == "SIMULATED_VALID"


def test_aws_fixture_byoc_contract_never_returns_credentials():
    aws = FixtureAwsDiscovery()
    contract = aws.role_contract("connection-123")
    session = aws.assume_scoped_role(contract, "local-product-token")
    assert contract.audience == "agentconstruct-byoc"
    assert session.session_reference.startswith("fixture-sts-session:")
    assert "no AWS access key" in session.credential_boundary


def test_execution_profiles_keep_kubernetes_specific_to_the_approved_profile():
    app_runner = execution_profile("aws-app-runner")
    eks = execution_profile("aws-eks-governed")
    assert app_runner.kubernetes_boundary == "not used"
    assert eks.delivery_kind == "kubernetes"
    assert "GitOps" in eks.gitops_boundary
