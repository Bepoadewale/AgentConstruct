"""Control-plane-only storage for customer connection material.

The browser receives a one-time CloudFormation URL but never receives, stores, or replays
the ExternalId. Local development encrypts the value in the database reference; production
uses a dedicated Secrets Manager secret per connection.
"""

from __future__ import annotations

import base64
import hashlib
import os
from typing import Protocol

import boto3
from cryptography.fernet import Fernet


class ConnectionSecretStore(Protocol):
    def put_external_id(self, organization_id: str, connection_id: str, value: str) -> str: ...

    def get_external_id(self, reference: str) -> str: ...


class LocalEncryptedConnectionSecretStore:
    """Deterministic local-only substitute for a managed secret store."""

    def __init__(self, key: str | None = None):
        material = (key or "agentconstruct-local-development-only").encode()
        self.fernet = Fernet(base64.urlsafe_b64encode(hashlib.sha256(material).digest()))

    def put_external_id(self, organization_id: str, connection_id: str, value: str) -> str:
        del organization_id, connection_id
        return "local-encrypted:" + self.fernet.encrypt(value.encode()).decode()

    def get_external_id(self, reference: str) -> str:
        if not reference.startswith("local-encrypted:"):
            raise ValueError("invalid local encrypted connection-secret reference")
        return self.fernet.decrypt(reference.removeprefix("local-encrypted:").encode()).decode()


class AwsSecretsManagerConnectionSecretStore:
    """Production contract: only the control-plane runtime role may read this secret."""

    def __init__(self, prefix: str | None = None):
        self.prefix = (prefix or "agentconstruct/customer-connections").rstrip("/")
        self.client = boto3.client("secretsmanager")

    def put_external_id(self, organization_id: str, connection_id: str, value: str) -> str:
        name = f"{self.prefix}/{organization_id}/{connection_id}/external-id"
        try:
            return str(self.client.create_secret(Name=name, SecretString=value)["ARN"])
        except self.client.exceptions.ResourceExistsException:
            self.client.put_secret_value(SecretId=name, SecretString=value)
            return str(self.client.describe_secret(SecretId=name)["ARN"])

    def get_external_id(self, reference: str) -> str:
        return str(self.client.get_secret_value(SecretId=reference)["SecretString"])


def configured_connection_secret_store() -> ConnectionSecretStore:
    backend = os.getenv("AGENTCONSTRUCT_CONNECTION_SECRET_BACKEND", "local_encrypted")
    if backend == "aws_secrets_manager":
        return AwsSecretsManagerConnectionSecretStore(
            os.getenv("AGENTCONSTRUCT_CONNECTION_SECRET_PREFIX")
        )
    if backend == "local_encrypted":
        return LocalEncryptedConnectionSecretStore(os.getenv("AGENTCONSTRUCT_CONNECTION_SECRET_KEY"))
    raise RuntimeError("unsupported AGENTCONSTRUCT_CONNECTION_SECRET_BACKEND")
