from __future__ import annotations

from agentconstruct.security import LOCAL_USERS, Principal
from test_product import founder, make_service


def other_tenant() -> Principal:
    subject, organization_id, role = LOCAL_USERS["other-tenant"]
    return Principal(subject, organization_id, role)


def test_fixture_github_connection_lists_only_authorized_repositories_and_branches():
    service, _ = make_service()
    status = service.github_connection_status(founder())
    assert status["execution"] == "SIMULATED"
    assert status["writes_enabled"] is False
    installation_id = status["installations"][0]["id"]
    repositories = service.github_repositories(founder(), installation_id)
    assert repositories[0]["full_name"] == "example/support-rag-api"
    branches = service.github_branches(founder(), installation_id, repositories[0]["full_name"])
    assert branches == ["main", "staging"]


def test_project_persists_selected_repository_branch_for_safe_read_only_discovery():
    service, _ = make_service()
    project = service.create_project(
        founder(),
        "branch-selection",
        "https://github.com/example/support-rag-api",
        "staging",
    )
    discovered = service.repository_discovery(founder(), project.id)
    assert discovered["selected_branch"] == "staging"
    assert discovered["execution"] == "SIMULATED"
    assert discovered["analysis"]["framework_hints"] == ["fastapi"]
    assert "Dockerfile" in discovered["analysis"]["manifests"]


def test_repository_analysis_is_persisted_and_feeds_intent_spec():
    service, _ = make_service()
    project = service.create_project(
        founder(),
        "repo-analysis",
        "https://github.com/example/support-rag-api",
        "main",
    )
    service.repository_discovery(founder(), project.id)
    intent = service.create_intent(
        founder(),
        project.id,
        "Deploy this AI API in AWS. Keep customer data private. Support 20 requests per second and peak at 100 requests per second. Keep monthly infrastructure under $500. Create staging and production. Enable monitoring.",
        project.repository_url,
        None,
        "repo-analysis-001",
    )

    analysis = intent.spec["repository_analysis"]
    assert analysis["repository"] == "example/support-rag-api"
    assert analysis["selected_branch"] == "main"
    assert intent.spec["runtime"] == "python-fastapi"
    assert intent.spec["stateful"] is True


def test_aws_connection_detail_and_disconnect_are_tenant_scoped_and_credential_free():
    service, _ = make_service()
    connection = service.create_cloud_connection(founder(), "Customer account", "aws", "byoc_role_contract")
    detail = service.cloud_connection_detail(founder(), connection.id)
    assert detail["credentials_stored"] is False
    assert detail["deployment_permission"] == "not granted"
    try:
        service.cloud_connection_detail(other_tenant(), connection.id)
    except PermissionError:
        pass
    else:
        raise AssertionError("other tenant read an AWS connection")
    service.disconnect_cloud_connection(founder(), connection.id)
    assert service.cloud_connections(founder()) == []
