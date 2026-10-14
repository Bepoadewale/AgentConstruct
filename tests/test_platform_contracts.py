from datetime import UTC, datetime

import pytest
from agentconstruct.contracts import (
    CapabilityKind,
    CapabilityRequirement,
    CostEvidence,
    EvidenceKind,
    EvidenceRef,
    JobEnvelope,
    JobKind,
    ModelPurpose,
    ModelRequest,
    TenantScope,
    UsageEvent,
)
from pydantic import ValidationError


def scope() -> TenantScope:
    return TenantScope(
        organization_id="org-demo",
        workspace_id="workspace-demo",
        project_id="project-demo",
        actor_id="user-demo",
    )


def test_platform_contracts_require_explicit_tenant_scope():
    with pytest.raises(ValidationError):
        JobEnvelope(kind=JobKind.PLANNING, idempotency_key="planning-123")


def test_evidence_is_versioned_provenance_and_credential_free():
    evidence = EvidenceRef(
        tenant=scope(),
        kind=EvidenceKind.AWS_API,
        source="sts:GetCallerIdentity",
        captured_at=datetime.now(UTC),
        limitations=("read-only role",),
    )
    payload = evidence.model_dump(mode="json")
    assert payload["schema_version"]
    assert payload["tenant"]["organization_id"] == "org-demo"
    assert "access_key" not in str(payload).lower()


def test_model_request_carries_provider_budget_and_prompt_version_without_authority():
    request = ModelRequest(
        tenant=scope(),
        purpose=ModelPurpose.INTENT_EXTRACTION,
        provider="fixture",
        model="deterministic-fixture",
        prompt_version="intent-v1",
        input_digest="a" * 64,
        max_output_tokens=500,
    )
    assert request.schema_version
    assert request.timeout_seconds == 60
    assert request.purpose == ModelPurpose.INTENT_EXTRACTION


def test_jobs_are_transport_neutral_and_retryable():
    job = JobEnvelope(
        tenant=scope(),
        kind=JobKind.AWS_DISCOVERY,
        idempotency_key="discovery-123",
        payload={"connection_id": "connection-1"},
        max_attempts=5,
        timeout_seconds=300,
    )
    assert job.attempt == 0
    assert job.max_attempts == 5
    assert job.payload["connection_id"] == "connection-1"


def test_capability_requirements_are_provider_neutral():
    requirement = CapabilityRequirement(
        kind=CapabilityKind.COMPUTE,
        name="managed_application",
        constraints={"max_monthly_usd": 300, "private_ingress": True},
    )
    assert requirement.required is True
    assert requirement.kind == CapabilityKind.COMPUTE


def test_cost_evidence_is_an_estimate_unless_explicitly_actual():
    estimate = CostEvidence(
        monthly_low=20,
        monthly_high=50,
        catalog_version="aws-fixture-v1",
        assumptions=("not an AWS bill",),
    )
    assert estimate.actual_billing is False
    with pytest.raises(ValidationError):
        CostEvidence(monthly_low=50, monthly_high=20, catalog_version="bad")


def test_usage_events_are_tenant_scoped_and_meterable():
    event = UsageEvent(
        tenant=scope(),
        event_type="model_call",
        quantity=123,
        unit="output_tokens",
        source="intent-engine",
        correlation_id="plan-1",
    )
    assert event.tenant.workspace_id == "workspace-demo"
    assert event.quantity == 123

