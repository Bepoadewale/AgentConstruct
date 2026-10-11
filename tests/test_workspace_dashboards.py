from __future__ import annotations

from agentconstruct.domain import InfrastructurePlanState
from agentconstruct.security import LOCAL_USERS, Principal, issue_local_token, verify_token
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
    assert revision.state == InfrastructurePlanState.SUBMITTED


def test_developer_cannot_read_administrator_pending_queue():
    service, _ = make_service()
    submitted_plan(service)
    try:
        service.pending_infrastructure_plan_revisions(founder())
    except PermissionError as error:
        assert "administrator" in str(error)
    else:
        raise AssertionError("developer received the administrator queue")
