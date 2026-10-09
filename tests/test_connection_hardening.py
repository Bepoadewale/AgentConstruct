from pathlib import Path

from agentconstruct.connection_secrets import LocalEncryptedConnectionSecretStore


def test_local_connection_secret_reference_does_not_contain_plaintext():
    store = LocalEncryptedConnectionSecretStore("test-key")
    reference = store.put_external_id("org-demo", "connection-demo", "never-store-me")
    assert "never-store-me" not in reference
    assert store.get_external_id(reference) == "never-store-me"


def test_runtime_identity_is_separate_from_github_and_scoped():
    root = Path("infrastructure/terraform/control-plane-runtime-identity/main.tf").read_text()
    github = Path("infrastructure/terraform/management-identity/main.tf").read_text()
    assert "agentconstruct-control-plane-runtime" in root
    assert "AgentConstructDiscovery-*" in root
    assert "secretsmanager:GetSecretValue" in root
    assert "agentconstruct-control-plane-runtime" not in github
