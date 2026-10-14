from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Protocol

import boto3
import jwt
from fastapi import Header, HTTPException


def local_signing_key() -> str:
    secret_arn = os.getenv("AGENTCONSTRUCT_LOCAL_SIGNING_KEY_SECRET_ARN")
    if secret_arn:
        return str(boto3.client("secretsmanager").get_secret_value(SecretId=secret_arn)["SecretString"])
    return os.getenv("AGENTCONSTRUCT_LOCAL_SIGNING_KEY", "local-development-only-change-me")


LOCAL_ISSUER = "agentconstruct-local"
LOCAL_AUDIENCE = "agentconstruct-api"


@dataclass(frozen=True)
class Principal:
    subject: str
    organization_id: str
    role: str


class IdentityVerifier(Protocol):
    """Converts a trusted bearer token into a tenant-bound principal."""

    def verify(self, token: str) -> Principal: ...


LOCAL_USERS = {
    "founder": ("user-founder", "org-demo", "developer"),
    "administrator": ("user-administrator", "org-demo", "administrator"),
    # Keep the earlier fixture so existing local execution evidence remains reproducible.
    "operator": ("user-operator", "org-demo", "operator"),
    "other-tenant": ("user-other", "org-other", "developer"),
}


def issue_local_token(username: str) -> str:
    if username not in LOCAL_USERS:
        raise HTTPException(401, "unknown local demo user")
    subject, organization_id, role = LOCAL_USERS[username]
    now = datetime.now(UTC)
    return jwt.encode(
        {
            "sub": subject,
            "org": organization_id,
            "role": role,
            "iss": LOCAL_ISSUER,
            "aud": LOCAL_AUDIENCE,
            "iat": now,
            "exp": now + timedelta(minutes=30),
        },
        local_signing_key(),
        algorithm="HS256",
    )


def principal_from_claims(payload: dict) -> Principal:
    role = payload["role"]
    if role not in {"developer", "operator", "administrator"}:
        raise HTTPException(403, "role not allowed")
    return Principal(subject=payload["sub"], organization_id=payload["org"], role=role)


class LocalIdentityVerifier:
    def verify(self, token: str) -> Principal:
        try:
            payload = jwt.decode(
                token,
                local_signing_key(),
                algorithms=["HS256"],
                issuer=LOCAL_ISSUER,
                audience=LOCAL_AUDIENCE,
                options={"require": ["sub", "org", "role", "exp"]},
            )
        except jwt.PyJWTError as error:
            raise HTTPException(401, "invalid signed identity") from error
        return principal_from_claims(payload)


class JwksIdentityVerifier:
    """Production adapter. It is not configured or called by the local demo."""

    def __init__(self, jwks_url: str, issuer: str, audience: str):
        self.client = jwt.PyJWKClient(jwks_url)
        self.issuer = issuer
        self.audience = audience

    def verify(self, token: str) -> Principal:
        try:
            key = self.client.get_signing_key_from_jwt(token)
            payload = jwt.decode(
                token,
                key.key,
                algorithms=["RS256", "ES256"],
                issuer=self.issuer,
                audience=self.audience,
                options={"require": ["sub", "org", "role", "exp"]},
            )
        except jwt.PyJWTError as error:
            raise HTTPException(401, "invalid trusted identity") from error
        return principal_from_claims(payload)


def configured_verifier() -> IdentityVerifier:
    jwks_url = os.getenv("AGENTCONSTRUCT_JWKS_URL")
    if jwks_url:
        issuer = os.environ["AGENTCONSTRUCT_OIDC_ISSUER"]
        audience = os.environ["AGENTCONSTRUCT_OIDC_AUDIENCE"]
        return JwksIdentityVerifier(jwks_url, issuer, audience)
    return LocalIdentityVerifier()


def verify_token(authorization: str = Header(...)) -> Principal:
    if not authorization.startswith("Bearer "):
        raise HTTPException(401, "bearer token required")
    return configured_verifier().verify(authorization.removeprefix("Bearer "))


def verify_local_token_for_test(authorization: str) -> Principal:
    """Compatibility helper for fast local tests."""
    if not authorization.startswith("Bearer "):
        raise HTTPException(401, "bearer token required")
    try:
        payload = jwt.decode(
            authorization.removeprefix("Bearer "),
            local_signing_key(),
            algorithms=["HS256"],
            issuer=LOCAL_ISSUER,
            audience=LOCAL_AUDIENCE,
            options={"require": ["sub", "org", "role", "exp"]},
        )
    except jwt.PyJWTError as error:
        raise HTTPException(401, "invalid signed identity") from error
    return principal_from_claims(payload)
