"""Provider-neutral hardening boundaries for the control plane.

These are intentionally small in-memory/local implementations. They make the
authorization, lifecycle, capability, evidence, rollout, and runner contracts
explicit without requiring a distributed deployment.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any, Protocol

from pydantic import BaseModel, ConfigDict, Field

from agentconstruct.contracts import (
    CapabilityKind,
    CostEvidence,
    EvidenceRef,
    ExecutionContext,
    ExecutionOperation,
    ProviderCapability,
    TenantScope,
)
from agentconstruct.security import Principal


class TenantBoundaryError(ValueError):
    """Raised when an operation crosses an explicit tenant boundary."""


class TenantContext(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    organization_id: str = Field(min_length=1, max_length=160)
    workspace_id: str = Field(min_length=1, max_length=160)
    actor_id: str = Field(min_length=1, max_length=160)
    role: str = Field(default="developer", min_length=1, max_length=80)
    project_id: str | None = Field(default=None, max_length=160)
    environment_id: str | None = Field(default=None, max_length=160)
    cell_id: str = Field(default="local", min_length=1, max_length=120)
    home_region: str = Field(default="local", min_length=1, max_length=80)

    @classmethod
    def from_principal(cls, principal: Principal, *, workspace_id: str = "workspace-default", **ids: str | None) -> TenantContext:
        return cls(
            organization_id=principal.organization_id,
            workspace_id=workspace_id,
            actor_id=principal.subject,
            role=principal.role,
            **ids,
        )

    def contract_scope(self) -> TenantScope:
        return TenantScope(
            organization_id=self.organization_id,
            workspace_id=self.workspace_id,
            project_id=self.project_id,
            environment_id=self.environment_id,
            actor_id=self.actor_id,
            cell_id=self.cell_id,
            home_region=self.home_region,
        )


def require_same_tenant(expected: TenantContext, actual: TenantScope | TenantContext) -> None:
    """Fail closed when a record or job is not owned by the active tenant."""

    if expected.organization_id != actual.organization_id or expected.workspace_id != actual.workspace_id:
        raise TenantBoundaryError("tenant scope mismatch")
    for field_name in ("project_id", "environment_id"):
        expected_value = getattr(expected, field_name)
        actual_value = getattr(actual, field_name)
        if expected_value and actual_value and expected_value != actual_value:
            raise TenantBoundaryError(f"{field_name} scope mismatch")


class FeatureFlag(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    name: str = Field(min_length=1, max_length=120)
    enabled: bool = False
    tenants: frozenset[str] = frozenset()
    roles: frozenset[str] = frozenset()
    environments: frozenset[str] = frozenset()
    percentage: int = Field(default=100, ge=0, le=100)
    version: str = "local-v1"


class FeatureFlags(Protocol):
    def enabled(self, name: str, context: TenantContext) -> bool: ...


class RolloutPolicy(Protocol):
    def enabled(self, name: str, context: TenantContext) -> bool: ...


class InMemoryFeatureFlags:
    def __init__(self, flags: list[FeatureFlag] | None = None):
        self._flags = {flag.name: flag for flag in flags or []}
        self.audit: list[dict[str, str]] = []

    def set(self, flag: FeatureFlag) -> None:
        self._flags[flag.name] = flag
        self.audit.append({"event": "flag_updated", "name": flag.name, "version": flag.version})

    def enabled(self, name: str, context: TenantContext) -> bool:
        flag = self._flags.get(name)
        if flag is None or not flag.enabled:
            return False
        if flag.tenants and context.organization_id not in flag.tenants:
            return False
        if flag.roles and context.role not in flag.roles:
            return False
        if flag.environments and (context.environment_id or "") not in flag.environments:
            return False
        bucket = sum(ord(char) for char in f"{flag.name}:{context.organization_id}") % 100
        return bucket < flag.percentage


class DataLifecycle(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    retention_days: int = Field(default=365, ge=1, le=3_650)
    export_format: str = "json"
    deletion_grace_days: int = Field(default=30, ge=0, le=365)
    audit_archive_after_days: int = Field(default=730, ge=1, le=3_650)


class InMemoryDataLifecycle:
    """Local export/delete/archive contract for tenant data."""

    def __init__(self, policy: DataLifecycle | None = None):
        self.policy = policy or DataLifecycle()
        self.records: dict[str, list[dict[str, Any]]] = {}
        self.deleted: set[str] = set()
        self.archived_before: dict[str, datetime] = {}

    def add(self, context: TenantContext, record: dict[str, Any]) -> None:
        require_same_tenant(context, TenantScope(**record["tenant"]))
        self.records.setdefault(context.organization_id, []).append(record)

    def export(self, context: TenantContext) -> dict[str, Any]:
        return {"tenant": context.model_dump(), "records": list(self.records.get(context.organization_id, [])), "format": self.policy.export_format}

    def request_delete(self, context: TenantContext, *, now: datetime | None = None) -> datetime:
        self.deleted.add(context.organization_id)
        return (now or datetime.now(UTC)) + timedelta(days=self.policy.deletion_grace_days)

    def request_project_delete(self, context: TenantContext, project_id: str, *, now: datetime | None = None) -> datetime:
        if context.project_id and context.project_id != project_id:
            raise TenantBoundaryError("project scope mismatch")
        return self.request_delete(context.model_copy(update={"project_id": project_id}), now=now)

    def purge_due(self, context: TenantContext, *, now: datetime | None = None) -> int:
        if context.organization_id not in self.deleted:
            return 0
        self.records.pop(context.organization_id, None)
        self.deleted.discard(context.organization_id)
        return 1

    def archive_audit(self, context: TenantContext, *, now: datetime | None = None) -> datetime:
        cutoff = (now or datetime.now(UTC)) - timedelta(days=self.policy.audit_archive_after_days)
        self.archived_before[context.organization_id] = cutoff
        return cutoff


class CapabilityRegistry(Protocol):
    def register(self, capability: ProviderCapability) -> None: ...
    def resolve(self, kind: CapabilityKind, name: str, *, provider: str | None = None) -> tuple[ProviderCapability, ...]: ...


class InMemoryCapabilityRegistry:
    def __init__(self):
        self._capabilities: list[ProviderCapability] = []

    def register(self, capability: ProviderCapability) -> None:
        self._capabilities = [
            item for item in self._capabilities
            if (item.provider, item.kind, item.name) != (capability.provider, capability.kind, capability.name)
        ]
        self._capabilities.append(capability)

    def resolve(self, kind: CapabilityKind, name: str, *, provider: str | None = None) -> tuple[ProviderCapability, ...]:
        return tuple(item for item in self._capabilities if item.kind == kind and item.name == name and (provider is None or item.provider == provider))


class CostEstimator(Protocol):
    def estimate(self, profile: str, region: str) -> CostEvidence: ...


class ComplexityEstimator(Protocol):
    def score(self, profile: str, component_count: int) -> int: ...


class RiskEstimator(Protocol):
    def score(self, profile: str, unknowns: int) -> int: ...


class ReliabilityEstimator(Protocol):
    def score(self, profile: str, availability_target: str | None) -> int: ...


class CapacityEstimator(Protocol):
    def score(self, profile: str, peak_rps: int | None, component_count: int) -> int: ...


class FixtureDecisionEngines:
    """Separate deterministic engines used until live catalogs are configured."""

    def __init__(self, pricing: CostEstimator):
        self.pricing = pricing

    def estimate(self, profile: str, region: str) -> CostEvidence:
        return self.pricing.estimate(profile, region)

    @staticmethod
    def score_complexity(profile: str, component_count: int) -> int:
        return min(5, max(1, component_count + (2 if "eks" in profile.lower() else 0)))

    @staticmethod
    def score_risk(profile: str, unknowns: int) -> int:
        return min(5, max(1, unknowns + (2 if "kubernetes" in profile.lower() or "eks" in profile.lower() else 0)))

    @staticmethod
    def score_reliability(profile: str, availability_target: str | None) -> int:
        return 5 if availability_target and "99.9" in availability_target else (4 if "managed" in profile.lower() else 3)

    @staticmethod
    def score_capacity(profile: str, peak_rps: int | None, component_count: int) -> int:
        load = peak_rps or 0
        if "lambda" in profile.lower() and load > 100:
            return 2
        return min(5, max(1, 3 + (1 if load > 50 else 0) + (1 if component_count > 3 else 0)))


class EvidenceGraph:
    """Tenant-scoped evidence links for explainable recommendations."""

    def __init__(self):
        self.nodes: dict[str, EvidenceRef] = {}
        self.links: dict[str, set[str]] = {}

    def add(self, evidence: EvidenceRef, *, parent_id: str | None = None) -> str:
        self.nodes[evidence.evidence_id] = evidence
        if parent_id:
            parent = self.nodes.get(parent_id)
            if parent is None:
                raise KeyError(parent_id)
            require_same_tenant(
                TenantContext(**parent.tenant.model_dump(exclude={"schema_version", "project_id", "environment_id"})),
                evidence.tenant,
            )
            self.links.setdefault(parent_id, set()).add(evidence.evidence_id)
        return evidence.evidence_id

    def related(self, evidence_id: str, context: TenantContext) -> tuple[EvidenceRef, ...]:
        root = self.nodes[evidence_id]
        require_same_tenant(context, root.tenant)
        return tuple(self.nodes[item] for item in self.links.get(evidence_id, set()))


class RunnerLimits(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    timeout_seconds: int = Field(default=900, ge=1, le=86_400)
    max_output_bytes: int = Field(default=1_000_000, ge=1_024, le=100_000_000)
    allowed_operations: frozenset[ExecutionOperation] = frozenset({ExecutionOperation.PLAN, ExecutionOperation.OBSERVE})
    allowed_commands: frozenset[str] = frozenset()
    network_policy: str = Field(default="isolated-runner", min_length=1, max_length=120)
    filesystem_policy: str = Field(default="ephemeral-workspace", min_length=1, max_length=120)
    credential_scope: str = Field(default="reference-only", min_length=1, max_length=120)
    retry_policy: str = Field(default="bounded", min_length=1, max_length=80)
    cleanup_policy: str = Field(default="always", min_length=1, max_length=80)


def validate_runner_context(context: ExecutionContext, limits: RunnerLimits) -> None:
    if context.operation not in limits.allowed_operations:
        raise TenantBoundaryError("runner operation is outside the configured allowlist")
    if context.timeout_seconds > limits.timeout_seconds:
        raise TenantBoundaryError("runner timeout exceeds configured limit")
    if context.network_policy != limits.network_policy:
        raise TenantBoundaryError("runner network policy mismatch")
    if context.filesystem_policy != limits.filesystem_policy:
        raise TenantBoundaryError("runner filesystem policy mismatch")
    if context.credential_scope != limits.credential_scope:
        raise TenantBoundaryError("runner credential scope mismatch")
    if limits.allowed_commands and any(command not in limits.allowed_commands for command in context.requested_commands):
        raise TenantBoundaryError("runner command is outside the configured allowlist")
