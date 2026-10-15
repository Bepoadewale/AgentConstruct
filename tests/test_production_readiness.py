import pytest
from agentconstruct.boundaries import TenantBoundaryError, TenantContext
from agentconstruct.contracts import (
    ArchitecturePlanV1,
    Entitlement,
    EvidenceKind,
    EvidenceRef,
    UsageEvent,
)
from agentconstruct.production_readiness import (
    EntitlementEnforcer,
    LocalRecordStore,
    exercise_idempotency,
)


def context(org: str = "org-a", project: str | None = "project-a") -> TenantContext:
    return TenantContext(organization_id=org, workspace_id="workspace-a", actor_id="actor-a", project_id=project)


def test_named_contracts_carry_scope_provenance_and_digest() -> None:
    tenant = context().contract_scope()
    evidence = EvidenceRef(tenant=tenant, kind=EvidenceKind.FIXTURE, source="test")
    plan = ArchitecturePlanV1(
        tenant=tenant,
        actor_id=tenant.actor_id,
        project_id=tenant.project_id,
        architecture_family="managed-api",
        source_evidence=(evidence,),
        provenance={"planner": "fixture"},
        plan_digest="a" * 64,
        unknowns=("catalog-live",),
    )
    assert plan.contract_type == "ArchitecturePlan.v1"
    assert plan.schema_version
    assert plan.source_evidence[0].tenant.organization_id == "org-a"


def test_local_store_is_durable_tenant_scoped_and_backupable() -> None:
    store = LocalRecordStore()
    tenant = context().contract_scope()
    plan = ArchitecturePlanV1(tenant=tenant, actor_id=tenant.actor_id, project_id=tenant.project_id, architecture_family="local")
    store.put("plan-1", plan)
    assert store.get("plan-1", context())["architecture_family"] == "local"
    with pytest.raises((TenantBoundaryError, KeyError)):
        store.get("plan-1", context("org-b"))
    manifest, payload = store.backup(context(), "backup-1")
    assert manifest.record_count == 1
    assert manifest.content_digest
    assert "local" in payload
    assert store.soft_delete_project(context(), "project-a") == 1
    assert store.restore(context(), payload) == 1
    assert store.get("plan-1", context())["architecture_family"] == "local"


def test_idempotency_is_single_accept_under_concurrency() -> None:
    result = exercise_idempotency(context(), "execution-key-1", workers=32)
    assert result.unique is True
    assert result.accepted == 1


def test_entitlements_enforce_workspace_and_record_allowed_usage() -> None:
    tenant = context().contract_scope()
    enforcer = EntitlementEnforcer()
    entitlement = Entitlement(tenant=tenant, event_type="execution_jobs", limit=1, unit="job")
    event = UsageEvent(tenant=tenant, event_type="execution_jobs", quantity=1, unit="job", source="test")
    assert enforcer.decide_and_record(entitlement, event).allowed is True
    assert enforcer.decide_and_record(entitlement, event).allowed is False
    other = UsageEvent(tenant=context("org-b").contract_scope(), event_type="execution_jobs", quantity=1, unit="job", source="test")
    assert enforcer.decide_and_record(entitlement, other).allowed is False
