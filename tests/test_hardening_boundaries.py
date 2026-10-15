from datetime import UTC, datetime

import pytest
from agentconstruct.boundaries import (
    DataLifecycle,
    EvidenceGraph,
    FeatureFlag,
    InMemoryCapabilityRegistry,
    InMemoryDataLifecycle,
    InMemoryFeatureFlags,
    RunnerLimits,
    TenantBoundaryError,
    TenantContext,
    require_same_tenant,
    validate_runner_context,
)
from agentconstruct.contracts import (
    CapabilityKind,
    EvidenceKind,
    EvidenceRef,
    ExecutionContext,
    ExecutionOperation,
    ProviderCapability,
    TenantScope,
)


def context(org="org-demo"):
    return TenantContext(organization_id=org, workspace_id="ws-demo", actor_id="user-demo")


def test_tenant_context_rejects_cross_tenant_records():
    with pytest.raises(TenantBoundaryError):
        require_same_tenant(context(), TenantScope(organization_id="org-other", workspace_id="ws-demo", actor_id="other"))


def test_tenant_context_carries_cell_and_region_metadata():
    scoped = context().model_copy(update={"cell_id": "cell-a", "home_region": "eu-west-1"})
    assert scoped.cell_id == "cell-a"
    assert scoped.contract_scope().home_region == "eu-west-1"


def test_flags_are_disabled_by_default_and_targetable():
    flags = InMemoryFeatureFlags([FeatureFlag(name="new-runner", enabled=True, tenants=frozenset({"org-demo"}))])
    assert flags.enabled("new-runner", context()) is True
    assert flags.enabled("new-runner", context("org-other")) is False
    assert flags.enabled("missing", context()) is False


def test_data_lifecycle_exports_and_schedules_deletion():
    lifecycle = InMemoryDataLifecycle(DataLifecycle(deletion_grace_days=7))
    item = {"tenant": context().contract_scope().model_dump(), "kind": "plan", "id": "plan-1"}
    lifecycle.add(context(), item)
    assert lifecycle.export(context())["records"] == [item]
    due = lifecycle.request_delete(context(), now=datetime(2026, 1, 1, tzinfo=UTC))
    assert due.isoformat().startswith("2026-01-08")


def test_capability_registry_is_provider_neutral():
    registry = InMemoryCapabilityRegistry()
    registry.register(ProviderCapability(provider="local", kind=CapabilityKind.COMPUTE, name="managed", operational_complexity=1, catalog_version="fixture-v1"))
    registry.register(ProviderCapability(provider="other", kind=CapabilityKind.COMPUTE, name="managed", operational_complexity=2, catalog_version="fixture-v1"))
    assert len(registry.resolve(CapabilityKind.COMPUTE, "managed")) == 2
    assert registry.resolve(CapabilityKind.COMPUTE, "managed", provider="local")[0].provider == "local"


def test_evidence_graph_enforces_tenant_scope():
    graph = EvidenceGraph()
    root = EvidenceRef(tenant=context().contract_scope(), kind=EvidenceKind.FIXTURE, source="root")
    child = EvidenceRef(tenant=context().contract_scope(), kind=EvidenceKind.OBSERVATION, source="child")
    graph.add(root)
    graph.add(child, parent_id=root.evidence_id)
    assert graph.related(root.evidence_id, context())[0].source == "child"
    with pytest.raises(TenantBoundaryError):
        graph.related(root.evidence_id, context("org-other"))


def test_runner_limits_fail_closed():
    digest = "a" * 64
    execution = ExecutionContext(
        tenant=context().contract_scope(),
        plan_digest=digest,
        operation=ExecutionOperation.APPLY,
        allowed_operations=(ExecutionOperation.APPLY,),
    )
    with pytest.raises(TenantBoundaryError):
        validate_runner_context(execution, RunnerLimits())

    restricted = execution.model_copy(update={"operation": ExecutionOperation.PLAN, "requested_commands": ("terraform",)})
    with pytest.raises(TenantBoundaryError):
        validate_runner_context(restricted, RunnerLimits(allowed_commands=frozenset({"echo"})))
