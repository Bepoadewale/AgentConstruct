"""Narrow production integration contracts; local V1 does not hold cloud credentials."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Protocol

from agentconstruct.domain import CloudInventorySnapshot


@dataclass(frozen=True)
class RepositoryMetadata:
    provider: str
    installation_id: str
    repository: str
    default_branch: str


class GitHubConnection(Protocol):
    def inspect_repository(self, installation_id: str, repository: str) -> RepositoryMetadata: ...

    def publish_desired_state(
        self, installation_id: str, repository: str, path: str, content: str
    ) -> str: ...


class AwsCloudConnection(Protocol):
    """Future adapter: assumes a customer-scoped role with short-lived STS credentials."""

    def discover(self, connection_id: str) -> dict: ...

    def estimate_catalog_version(self, region: str) -> str: ...


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
