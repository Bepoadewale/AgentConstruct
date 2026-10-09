"""Narrow production integration contracts; local V1 does not hold cloud credentials."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Protocol

from agentconstruct.domain import CloudInventorySnapshot


@dataclass(frozen=True)
class RepositoryMetadata:
    provider: str
    installation_id: str
    repository: str
    default_branch: str


@dataclass(frozen=True)
class GitHubWebhookContract:
    event: str
    delivery_id: str
    installation_id: str
    repository: str
    verification: str


@dataclass(frozen=True)
class DesiredStatePullRequest:
    pull_request_url: str
    branch: str
    required_checks: tuple[str, ...]
    status: str


@dataclass(frozen=True)
class AwsRoleContract:
    provider: str
    role_arn: str
    audience: str
    session_duration_minutes: int
    credential_boundary: str


@dataclass(frozen=True)
class AssumedRoleSession:
    session_reference: str
    expires_at: datetime
    credential_boundary: str


class GitHubConnection(Protocol):
    def inspect_repository(self, installation_id: str, repository: str) -> RepositoryMetadata: ...

    def publish_desired_state(
        self, installation_id: str, repository: str, path: str, content: str
    ) -> str: ...

    def validate_webhook(self, event: str, delivery_id: str, signature: str) -> GitHubWebhookContract: ...


class AwsCloudConnection(Protocol):
    """Future adapter: assumes a customer-scoped role with short-lived STS credentials."""

    def discover(self, connection_id: str) -> dict: ...

    def estimate_catalog_version(self, region: str) -> str: ...

    def role_contract(self, connection_id: str) -> AwsRoleContract: ...

    def assume_scoped_role(self, contract: AwsRoleContract, subject_token: str) -> AssumedRoleSession: ...


class CloudDiscovery(Protocol):
    def inventory(self, connection_id: str, region: str) -> CloudInventorySnapshot: ...


class SlackNotifier(Protocol):
    def notify(self, channel: str, text: str) -> None: ...


class FixtureGitHubConnection:
    """Local deterministic fixture; it cannot reach GitHub or write a repository."""

    def inspect_repository(self, installation_id: str, repository: str) -> RepositoryMetadata:
        return RepositoryMetadata("fixture", installation_id, repository, "main")

    def publish_desired_state(
        self, installation_id: str, repository: str, path: str, content: str
    ) -> str:
        return f"fixture-pr://{installation_id}/{repository}/{path}"

    def publish_reviewed_desired_state(
        self, installation_id: str, repository: str, path: str, content: str
    ) -> DesiredStatePullRequest:
        return DesiredStatePullRequest(
            pull_request_url=self.publish_desired_state(installation_id, repository, path, content),
            branch=f"agentconstruct/desired-state-{installation_id}",
            required_checks=("agentconstruct-plan", "agentconstruct-policy"),
            status="SIMULATED",
        )

    def validate_webhook(self, event: str, delivery_id: str, signature: str) -> GitHubWebhookContract:
        if not signature.startswith("fixture-sha256="):
            raise ValueError("fixture webhook signature is invalid")
        return GitHubWebhookContract(
            event=event,
            delivery_id=delivery_id,
            installation_id="fixture-installation",
            repository="example/support-rag-api",
            verification="SIMULATED_VALID",
        )


class FixtureAwsDiscovery:
    """Deterministic local discovery. It holds no AWS credentials and makes no network calls."""

    def inventory(self, connection_id: str, region: str) -> CloudInventorySnapshot:
        return CloudInventorySnapshot(
            provider="aws",
            region=region,
            approved_resources=[],
            approved_regions=["us-east-1", "eu-west-1"],
            discovered_at=datetime.now(UTC),
            provenance=f"fixture:{connection_id}",
        )

    def role_contract(self, connection_id: str) -> AwsRoleContract:
        return AwsRoleContract(
            provider="aws",
            role_arn=f"arn:aws:iam::000000000000:role/agentconstruct-{connection_id[:8]}",
            audience="agentconstruct-byoc",
            session_duration_minutes=60,
            credential_boundary=(
                "Contract only: production uses customer-approved OIDC and STS. "
                "The local fixture returns no AWS credentials."
            ),
        )

    def assume_scoped_role(self, contract: AwsRoleContract, subject_token: str) -> AssumedRoleSession:
        if not subject_token:
            raise ValueError("an AgentConstruct identity token is required")
        return AssumedRoleSession(
            session_reference=f"fixture-sts-session:{contract.role_arn.rsplit('/', maxsplit=1)[-1]}",
            expires_at=datetime.now(UTC) + timedelta(minutes=contract.session_duration_minutes),
            credential_boundary=(
                "Simulated session reference only; no AWS access key, secret, session token, "
                "or live role assumption exists."
            ),
        )
