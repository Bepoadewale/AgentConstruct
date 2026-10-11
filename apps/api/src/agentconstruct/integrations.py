"""Narrow production integration contracts; local V1 does not hold cloud credentials."""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Protocol
from urllib.parse import urlparse

import boto3
import httpx
import jwt
from botocore.exceptions import BotoCoreError, ClientError

from agentconstruct.domain import CloudInventorySnapshot


@dataclass(frozen=True)
class RepositoryMetadata:
    provider: str
    installation_id: str
    repository: str
    default_branch: str


@dataclass(frozen=True)
class GitHubInstallation:
    id: str
    account_login: str
    account_type: str


@dataclass(frozen=True)
class GitHubRepository:
    full_name: str
    html_url: str
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
    def installations(self) -> list[GitHubInstallation]: ...

    def repositories(self, installation_id: str) -> list[GitHubRepository]: ...

    def branches(self, installation_id: str, repository: str) -> list[str]: ...

    def inspect_repository(self, installation_id: str, repository: str) -> RepositoryMetadata: ...

    def publish_desired_state(
        self, installation_id: str, repository: str, path: str, content: str
    ) -> str: ...

    def validate_webhook(
        self, event: str, delivery_id: str, signature: str
    ) -> GitHubWebhookContract: ...


class AwsCloudConnection(Protocol):
    """Future adapter: assumes a customer-scoped role with short-lived STS credentials."""

    def discover(self, connection_id: str) -> dict: ...

    def estimate_catalog_version(self, region: str) -> str: ...

    def role_contract(self, connection_id: str) -> AwsRoleContract: ...

    def assume_scoped_role(
        self, contract: AwsRoleContract, subject_token: str
    ) -> AssumedRoleSession: ...


class CloudDiscovery(Protocol):
    def inventory(self, connection_id: str, region: str) -> CloudInventorySnapshot: ...


class SlackNotifier(Protocol):
    def notify(self, channel: str, text: str) -> None: ...


class FixtureGitHubConnection:
    """Local deterministic fixture; it cannot reach GitHub or write a repository."""

    def installations(self) -> list[GitHubInstallation]:
        return [GitHubInstallation("fixture-installation", "demo-ai-startup", "Organization")]

    def repositories(self, installation_id: str) -> list[GitHubRepository]:
        if installation_id != "fixture-installation":
            raise PermissionError("GitHub installation is not available to this workspace")
        return [
            GitHubRepository(
                "example/support-rag-api", "https://github.com/example/support-rag-api", "main"
            ),
            GitHubRepository("example/fastapi-ai-api", "https://github.com/example/fastapi-ai-api", "main"),
        ]

    def branches(self, installation_id: str, repository: str) -> list[str]:
        if installation_id != "fixture-installation":
            raise PermissionError("GitHub installation is not available to this workspace")
        self._repository_name(repository)
        return ["main", "staging"]

    @staticmethod
    def _repository_name(repository: str) -> str:
        parsed = urlparse(repository)
        candidate = parsed.path.strip("/") if parsed.scheme else repository.strip("/")
        candidate = candidate.removesuffix(".git")
        if len(candidate.split("/")) != 2:
            raise ValueError("repository must be an owner/name GitHub repository")
        return candidate

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

    def validate_webhook(
        self, event: str, delivery_id: str, signature: str
    ) -> GitHubWebhookContract:
        if not signature.startswith("fixture-sha256="):
            raise ValueError("fixture webhook signature is invalid")
        return GitHubWebhookContract(
            event=event,
            delivery_id=delivery_id,
            installation_id="fixture-installation",
            repository="example/support-rag-api",
            verification="SIMULATED_VALID",
        )


class GitHubAppReadOnlyConnection:
    """Live GitHub App reader. It never exposes or persists installation tokens."""

    api_url = "https://api.github.com"
    execution = "EXECUTED_READ_ONLY"

    def __init__(self, app_id: str, installation_id: str, private_key_path: str):
        self.app_id = app_id
        self.installation_id = installation_id
        self.private_key_path = Path(private_key_path)

    def _app_jwt(self) -> str:
        now = datetime.now(UTC)
        return jwt.encode(
            {
                "iat": now - timedelta(seconds=30),
                "exp": now + timedelta(minutes=9),
                "iss": self.app_id,
            },
            self.private_key_path.read_text(),
            algorithm="RS256",
        )

    def _installation_token(self) -> str:
        response = httpx.post(
            f"{self.api_url}/app/installations/{self.installation_id}/access_tokens",
            headers={
                "Authorization": f"Bearer {self._app_jwt()}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            },
            timeout=10,
        )
        response.raise_for_status()
        return str(response.json()["token"])

    def installations(self) -> list[GitHubInstallation]:
        # This product connection deliberately exposes only its configured installation.
        return [GitHubInstallation(self.installation_id, "configured-github-app", "Installation")]

    def repositories(self, installation_id: str) -> list[GitHubRepository]:
        if installation_id != self.installation_id:
            raise PermissionError("GitHub installation is not configured for this connection")
        response = httpx.get(
            f"{self.api_url}/installation/repositories",
            headers={
                "Authorization": f"Bearer {self._installation_token()}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            },
            timeout=10,
        )
        response.raise_for_status()
        return [
            GitHubRepository(item["full_name"], item["html_url"], item["default_branch"])
            for item in response.json().get("repositories", [])
        ]

    def branches(self, installation_id: str, repository: str) -> list[str]:
        if installation_id != self.installation_id:
            raise PermissionError("GitHub installation is not configured for this connection")
        name = self._repository_name(repository)
        response = httpx.get(
            f"{self.api_url}/repos/{name}/branches",
            headers={
                "Authorization": f"Bearer {self._installation_token()}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            },
            params={"per_page": 100},
            timeout=10,
        )
        response.raise_for_status()
        return [str(item["name"]) for item in response.json()]

    @staticmethod
    def _repository_name(repository: str) -> str:
        parsed = urlparse(repository)
        candidate = parsed.path.strip("/") if parsed.scheme else repository.strip("/")
        candidate = candidate.removesuffix(".git")
        if len(candidate.split("/")) != 2:
            raise ValueError("repository must be an owner/name GitHub repository")
        return candidate

    def inspect_repository(self, installation_id: str, repository: str) -> RepositoryMetadata:
        if installation_id != self.installation_id:
            raise PermissionError("GitHub installation is not configured for this connection")
        name = self._repository_name(repository)
        response = httpx.get(
            f"{self.api_url}/repos/{name}",
            headers={
                "Authorization": f"Bearer {self._installation_token()}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            },
            timeout=10,
        )
        response.raise_for_status()
        payload = response.json()
        return RepositoryMetadata(
            "github_app", self.installation_id, name, payload["default_branch"]
        )

    def publish_desired_state(
        self, installation_id: str, repository: str, path: str, content: str
    ) -> str:
        raise PermissionError(
            "live GitHub App integration is read-only until reviewed-write is approved"
        )

    def validate_webhook(
        self, event: str, delivery_id: str, signature: str
    ) -> GitHubWebhookContract:
        raise PermissionError("live webhook processing is not enabled in read-only mode")


def configured_github_connection() -> GitHubConnection:
    """Use live GitHub only after an explicit operator opt-in and complete key configuration."""
    enabled = os.getenv("AGENTCONSTRUCT_GITHUB_APP_READ_ONLY", "false").lower() == "true"
    app_id = os.getenv("AGENTCONSTRUCT_GITHUB_APP_ID")
    installation_id = os.getenv("AGENTCONSTRUCT_GITHUB_APP_INSTALLATION_ID")
    key_path = os.getenv("AGENTCONSTRUCT_GITHUB_APP_PRIVATE_KEY_PATH")
    if not enabled:
        return FixtureGitHubConnection()
    if not all([app_id, installation_id, key_path]):
        raise RuntimeError(
            "live GitHub App mode requires app ID, installation ID, and private-key path"
        )
    if not Path(key_path).is_file():
        raise RuntimeError("configured GitHub App private key is unavailable")
    return GitHubAppReadOnlyConnection(app_id, installation_id, key_path)


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

    def assume_scoped_role(
        self, contract: AwsRoleContract, subject_token: str
    ) -> AssumedRoleSession:
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


class StsAwsDiscovery:
    """Server-side, short-lived discovery for an already-approved customer role.

    The browser never receives the assumed-role credentials. The process identity must
    already be the configured AgentConstruct control-plane identity.
    """

    def __init__(self, session: object | None = None):
        self.session = session or boto3.Session()

    def verify(self, connection_id: str, role_arn: str, external_id: str, region: str) -> CloudInventorySnapshot:
        sts = self.session.client("sts", region_name=region)
        assumed = sts.assume_role(
            RoleArn=role_arn,
            RoleSessionName=f"agentconstruct-discovery-{connection_id[:8]}",
            ExternalId=external_id,
            DurationSeconds=900,
        )["Credentials"]
        customer = boto3.Session(
            aws_access_key_id=assumed["AccessKeyId"],
            aws_secret_access_key=assumed["SecretAccessKey"],
            aws_session_token=assumed["SessionToken"],
            region_name=region,
        )
        account = customer.client("sts").get_caller_identity()["Account"]
        resources = [f"aws-account:{account}"]
        resources.extend(self._inventory(customer, region))
        return CloudInventorySnapshot(
            provider="aws",
            region=region,
            approved_resources=resources,
            approved_regions=[region],
            discovered_at=datetime.now(UTC),
            provenance="live-read-only-sts-discovery",
        )

    @staticmethod
    def _inventory(customer: object, region: str) -> list[str]:
        """Collect only counts and identifiers needed by the planner; never workload data."""
        discovered: list[str] = []
        checks = (
            ("vpc", lambda: customer.client("ec2", region_name=region).describe_vpcs().get("Vpcs", [])),
            ("ecr", lambda: customer.client("ecr", region_name=region).describe_repositories().get("repositories", [])),
            ("eks", lambda: customer.client("eks", region_name=region).list_clusters().get("clusters", [])),
            ("ecs", lambda: customer.client("ecs", region_name=region).list_clusters().get("clusterArns", [])),
            ("rds", lambda: customer.client("rds", region_name=region).describe_db_instances().get("DBInstances", [])),
            ("lambda", lambda: customer.client("lambda", region_name=region).list_functions().get("Functions", [])),
            ("app-runner", lambda: customer.client("apprunner", region_name=region).list_services().get("ServiceSummaryList", [])),
        )
        for name, query in checks:
            try:
                discovered.append(f"{name}:{len(query())}")
            except (BotoCoreError, ClientError) as error:  # Customer policy may omit a service.
                discovered.append(f"{name}:unavailable:{type(error).__name__}")
        try:
            buckets = customer.client("s3", region_name=region).list_buckets().get("Buckets", [])
            discovered.append(f"s3:{len(buckets)}")
        except (BotoCoreError, ClientError) as error:
            discovered.append(f"s3:unavailable:{type(error).__name__}")
        return discovered
