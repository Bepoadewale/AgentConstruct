from __future__ import annotations

from davdeploy.domain import InfrastructurePlanDecision, InfrastructurePlanState
from davdeploy.security import LOCAL_USERS, Principal, issue_local_token, verify_token
from test_infrastructure_plan_lifecycle import plan_content
from test_product import founder, make_service


def administrator() -> Principal:
    subject, organization_id, role = LOCAL_USERS["administrator"]
    return Principal(subject, organization_id, role)


def submitted_plan(service):
    project = service.create_project(founder(), "dashboard-api", "https://github.com/example/dashboard")
    revision = service.create_infrastructure_plan(founder(), project.id, "Dashboard API", plan_content())
    return service.submit_infrastructure_plan(founder(), revision.id)


def test_administrator_local_token_is_accepted_as_a_distinct_product_role():
    principal = verify_token(f"Bearer {issue_local_token('administrator')}")
    assert principal.role == "administrator"
    assert principal.subject != founder().subject


def test_developer_dashboard_shows_only_own_customer_plan_revisions():
    service, _ = make_service()
    revision = submitted_plan(service)
    dashboard = service.workspace_dashboard(founder())
    assert dashboard["user"]["role"] == "developer"
    assert dashboard["pending_approval_count"] == 0
    assert [item["id"] for item in dashboard["plans"]] == [revision.id]


def test_administrator_dashboard_and_pending_queue_are_workspace_scoped():
    service, _ = make_service()
    revision = submitted_plan(service)
    dashboard = service.workspace_dashboard(administrator())
    assert dashboard["user"]["role"] == "administrator"
    assert dashboard["pending_approval_count"] == 1
    pending = service.pending_infrastructure_plan_revisions(administrator())
    assert pending[0]["id"] == revision.id
    assert pending[0]["state"] == InfrastructurePlanState.SUBMITTED
    assert pending[0]["repository"] == "https://github.com/example/service"
    assert pending[0]["policy_result"] == "APPROVAL_REQUIRED"
    assert pending[0]["not_deployed"] is True
    assert revision.state == InfrastructurePlanState.SUBMITTED


def test_administrator_review_queue_filters_decisions_and_self_approval():
    service, _ = make_service()
    submitted = submitted_plan(service)
    approved = service.decide_infrastructure_plan(
        administrator(),
        submitted.id,
        InfrastructurePlanDecision.APPROVED,
        submitted.content_digest,
    )
    project = service.create_project(
        administrator(), "admin-owned-review", "https://github.com/example/admin"
    )
    own = service.create_infrastructure_plan(
        administrator(), project.id, "Admin-owned API", plan_content()
    )
    service.submit_infrastructure_plan(administrator(), own.id)
    service.decide_infrastructure_plan(
        administrator(), own.id, InfrastructurePlanDecision.APPROVED, own.content_digest
    )

    approved_items = service.admin_infrastructure_plan_revisions(
        administrator(), InfrastructurePlanState.APPROVED
    )
    assert {item["id"] for item in approved_items} == {approved.id, own.id}
    self_approved = service.admin_infrastructure_plan_revisions(administrator(), "SELF_APPROVED")
    assert [item["id"] for item in self_approved] == [own.id]


def test_plan_detail_contains_admin_review_evidence_and_audit_export():
    service, _ = make_service()
    submitted = submitted_plan(service)
    detail = service.infrastructure_plan_revision_detail(administrator(), submitted.id)
    summary = detail["review_summary"]
    assert summary["requester"] == founder().subject
    assert summary["repository"] == "https://github.com/example/service"
    assert summary["region"] == "us-east-1"
    assert summary["policy_result"] == "APPROVAL_REQUIRED"
    assert summary["execution_boundary"].startswith("Approval records")

    service.decide_infrastructure_plan(
        administrator(),
        submitted.id,
        InfrastructurePlanDecision.REJECTED,
        submitted.content_digest,
        "Need a narrower budget.",
    )
    evidence = service.audit_evidence(administrator(), submitted.id)
    rejected = next(item for item in evidence if item["action"] == "infrastructure_plan.rejected")
    assert rejected["label"] == "Plan rejected"
    assert rejected["actor_role"] == "administrator"
    assert rejected["plan_digest"] == submitted.content_digest
    assert rejected["decision_reason"] == "Need a narrower budget."
    assert rejected["export_ready"] is True


def test_developer_cannot_read_administrator_pending_queue():
    service, _ = make_service()
    submitted_plan(service)
    try:
        service.pending_infrastructure_plan_revisions(founder())
    except PermissionError as error:
        assert "administrator" in str(error)
    else:
        raise AssertionError("developer received the administrator queue")
