from datetime import UTC, datetime

from agentconstruct.contracts import EvidenceKind, EvidenceRef, PlanningEvidence, TenantScope
from agentconstruct.domain import CloudInventorySnapshot, WorkloadSpec
from agentconstruct.evidence import FixturePricingCatalog
from agentconstruct.planner import AwsV1Planner


def tenant() -> TenantScope:
    return TenantScope(
        organization_id="org-demo",
        workspace_id="workspace-demo",
        project_id="project-demo",
        actor_id="user-demo",
    )


def simple_spec() -> WorkloadSpec:
    return WorkloadSpec(
        workload_type="ai_api",
        cloud="aws",
        average_rps=2,
        peak_rps=10,
        monthly_budget_usd=300,
        runtime="containerized",
        containerized=True,
        confidence=0.8,
    )


def test_fixture_pricing_is_explicitly_an_estimate():
    quote = FixturePricingCatalog().quote("aws-app-runner", "us-east-1")
    assert quote.actual_billing is False
    assert quote.catalog_version.startswith("aws-fixture")
    assert quote.monthly_low <= quote.monthly_high


def test_planner_attaches_typed_evidence_and_limitations():
    repository = EvidenceRef(
        tenant=tenant(),
        kind=EvidenceKind.REPOSITORY,
        source="github:fixture/repo",
        captured_at=datetime.now(UTC),
        limitations=("manifest-only inspection",),
    )
    pricing = FixturePricingCatalog().quote("aws-app-runner", "us-east-1")
    evidence = PlanningEvidence(
        tenant=tenant(),
        repository=(repository,),
        pricing=pricing,
        limitations=("AWS quotas were not queried",),
    )
    plan = AwsV1Planner().plan(
        simple_spec(),
        CloudInventorySnapshot(discovered_at=datetime.now(UTC)),
        evidence,
    )
    assert plan.profile == "aws-app-runner"
    assert plan.evidence_refs[0].kind == EvidenceKind.REPOSITORY
    assert "AWS quotas were not queried" in plan.evidence_limitations


def test_planner_labels_missing_evidence_as_fixture_limited():
    plan = AwsV1Planner().plan(simple_spec())
    assert plan.evidence_refs == []
    assert "fixture assumptions" in plan.evidence_limitations[0]

