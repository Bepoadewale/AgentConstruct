from __future__ import annotations

import pytest
from agentconstruct import security
from fastapi import HTTPException


class Membership:
    subject = "user-external"
    organization_id = "org-server"
    role = "developer"


class FakeQuery:
    def filter(self, *_args):
        return self

    def one_or_none(self):
        return Membership()


class FakeDb:
    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def query(self, *_args):
        return FakeQuery()


def test_external_identity_uses_server_membership_not_claimed_org_or_role(monkeypatch):
    monkeypatch.setattr(security, "SessionLocal", lambda: FakeDb())

    principal = security.principal_from_claims(
        {
            "sub": "user-external",
            "org": "attacker-org",
            "role": "administrator",
        },
        server_membership=True,
    )

    assert principal.subject == "user-external"
    assert principal.organization_id == "org-server"
    assert principal.role == "developer"


def test_external_identity_without_server_membership_is_denied(monkeypatch):
    class EmptyDb(FakeDb):
        def query(self, *_args):
            return type("EmptyQuery", (), {"filter": lambda self, *_: self, "one_or_none": lambda self: None})()

    monkeypatch.setattr(security, "SessionLocal", lambda: EmptyDb())

    with pytest.raises(HTTPException) as error:
        security.principal_from_claims({"sub": "unknown"}, server_membership=True)

    assert error.value.status_code == 403


def test_hosted_mode_requires_jwks_configuration(monkeypatch):
    monkeypatch.setenv("AGENTCONSTRUCT_HOSTED_MODE", "true")
    monkeypatch.delenv("AGENTCONSTRUCT_JWKS_URL", raising=False)

    with pytest.raises(HTTPException) as error:
        security.configured_verifier()

    assert error.value.status_code == 503
