from agentconstruct.domain import InfrastructurePlanDecision, InfrastructurePlanState
from agentconstruct.models import InfrastructurePlanDecisionRecord
from agentconstruct.security import Principal
from agentconstruct.service import plan_hash
from sqlalchemy import select
from test_product import founder, make_service, operator


def plan_content() -> dict:
    return {
        "provider": "aws",
        "repository": {"url": "https://github.com/example/service", "branch": "main"},
        "target": {"account_id": "123456789012", "region": "us-east-1"},
        "request": "Deploy a private FastAPI service with monitoring.",
    }


def draft(service):
    project = service.create_project(founder(), "lifecycle-app", "https://github.com/example/service")
    return service.create_infrastructure_plan(founder(), project.id, "Private API", plan_content())


def test_developer_submits_and_administrator_approves_exact_revision():
    service, db = make_service()
    revision = draft(service)
    submitted = service.submit_infrastructure_plan(founder(), revision.id)
    assert submitted.state == InfrastructurePlanState.SUBMITTED
    approved = service.decide_infrastructure_plan(
        operator(), revision.id, InfrastructurePlanDecision.APPROVED, revision.content_digest
    )
    assert approved.state == InfrastructurePlanState.APPROVED
    decision = db.scalar(select(InfrastructurePlanDecisionRecord).where(
        InfrastructurePlanDecisionRecord.revision_id == revision.id
    ))
    assert decision and not decision.is_self_approval
    assert decision.approved_digest == revision.content_digest


def test_administrator_can_self_approve_and_audits_exception():
    service, db = make_service()
    project = service.create_project(operator(), "admin-app", "https://github.com/example/admin-service")
    revision = service.create_infrastructure_plan(operator(), project.id, "Admin API", plan_content())
    service.submit_infrastructure_plan(operator(), revision.id)
    service.decide_infrastructure_plan(
        operator(), revision.id, InfrastructurePlanDecision.APPROVED, revision.content_digest
    )
    decision = db.scalar(select(InfrastructurePlanDecisionRecord).where(
        InfrastructurePlanDecisionRecord.revision_id == revision.id
    ))
    assert decision and decision.is_self_approval
    assert decision.authorization_policy == "workspace-administrator-self-approval-allowed"


def test_developer_cannot_decide_submitted_revision():
    service, _ = make_service()
    revision = draft(service)
    service.submit_infrastructure_plan(founder(), revision.id)
    try:
        service.decide_infrastructure_plan(
            founder(), revision.id, InfrastructurePlanDecision.APPROVED, revision.content_digest
        )
    except PermissionError:
        pass
    else:
        raise AssertionError("developer decision was accepted")
    assert revision.state == InfrastructurePlanState.SUBMITTED


def test_rejection_requires_reason_and_new_revision_preserves_history():
    service, _ = make_service()
    revision = draft(service)
    service.submit_infrastructure_plan(founder(), revision.id)
    try:
        service.decide_infrastructure_plan(
            operator(), revision.id, InfrastructurePlanDecision.REJECTED, revision.content_digest
        )
    except ValueError as error:
        assert "reason" in str(error)
    else:
        raise AssertionError("reason-free rejection was accepted")
    rejected = service.decide_infrastructure_plan(
        operator(), revision.id, InfrastructurePlanDecision.REJECTED, revision.content_digest, "Need a budget."
    )
    revision_two = service.revise_infrastructure_plan(
        founder(), rejected.infrastructure_plan_id, {**plan_content(), "monthly_budget_usd": 300}
    )
    assert rejected.state == InfrastructurePlanState.REJECTED
    assert revision_two.revision_number == 2
    assert revision_two.state == InfrastructurePlanState.DRAFT
    assert rejected.content_digest == plan_hash(plan_content())


def test_submitted_content_cannot_be_silently_changed_or_decided_twice():
    service, _ = make_service()
    revision = draft(service)
    revision.content["target"]["region"] = "eu-west-1"
    try:
        service.submit_infrastructure_plan(founder(), revision.id)
    except ValueError as error:
        assert "integrity" in str(error)
    else:
        raise AssertionError("tampered draft was submitted")

    plan = service._infrastructure_plan(founder(), revision.infrastructure_plan_id)
    revision = service.create_infrastructure_plan(
        founder(), plan.project_id, "Private API revision", plan_content()
    )
    service.submit_infrastructure_plan(founder(), revision.id)
    service.decide_infrastructure_plan(
        operator(), revision.id, InfrastructurePlanDecision.APPROVED, revision.content_digest
    )
    try:
        service.decide_infrastructure_plan(
            operator(), revision.id, InfrastructurePlanDecision.APPROVED, revision.content_digest
        )
    except ValueError as error:
        assert "submitted" in str(error)
    else:
        raise AssertionError("duplicate decision was accepted")


def test_infrastructure_revision_is_tenant_scoped():
    service, _ = make_service()
    revision = draft(service)
    other = Principal("user-other", "org-other", "developer")
    try:
        service.submit_infrastructure_plan(other, revision.id)
    except PermissionError:
        pass
    else:
        raise AssertionError("cross-tenant plan submission was accepted")
