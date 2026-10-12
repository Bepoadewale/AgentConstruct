from __future__ import annotations

from agentconstruct.domain import InfrastructurePlanDecision, InfrastructurePlanState
from test_product import complete_prompt, founder, make_service, operator


def test_simple_fastapi_customer_review_selects_one_non_eks_aws_plan_with_monitoring():
    service, _ = make_service()
    project = service.create_project(
        founder(),
        "review-fastapi",
        "https://github.com/example/fastapi-ai-api",
        "main",
    )
    service.repository_discovery(founder(), project.id)
    connection = service.create_cloud_connection(
        founder(), "Local AWS fixture", "aws", "byoc_role_contract"
    )
    intent = service.create_intent(
        founder(),
        project.id,
        complete_prompt(500),
        project.repository_url,
        connection.id,
        "customer-review-fastapi-001",
    )
    deployment = service.plan_intent(founder(), intent.id)
    review = service.create_customer_plan_review(founder(), deployment.id)
    content = review.content

    assert review.state == InfrastructurePlanState.DRAFT
    assert content["summary"]["selected_profile"] != "aws-eks-governed"
    assert content["application_analysis"]["branch"] == "main"
    assert content["application_analysis"]["repository_analysis"]["framework_hints"] == ["fastapi"]
    assert content["target"]["connection_id"] == connection.id
    assert content["observability"]["metrics_backend"].startswith("Prometheus")
    assert content["observability"]["dashboard"] == "Amazon Managed Grafana"
    assert any(item["category"] == "monitoring" for item in content["cost_estimate"]["components"])
    assert content["deployment_strategy"]["boundary"].startswith("Submission and approval")
    assert service.create_customer_plan_review(founder(), deployment.id).id == review.id


def test_customer_review_is_tenant_scoped_and_never_marks_deployment_executed():
    service, _ = make_service()
    project = service.create_project(founder(), "review-boundary", "https://github.com/example/api")
    intent = service.create_intent(
        founder(), project.id, complete_prompt(500), project.repository_url, None, "review-boundary-001"
    )
    deployment = service.plan_intent(founder(), intent.id)
    review = service.create_customer_plan_review(founder(), deployment.id)
    assert review.content["evidence"]["execution"] == "unexecuted customer plan review"
    assert deployment.state != "READY"


def test_customer_review_submits_then_administrator_approves_without_deploying():
    service, _ = make_service()
    project = service.create_project(
        founder(), "review-submit", "https://github.com/example/review-submit", "main"
    )
    intent = service.create_intent(
        founder(), project.id, complete_prompt(500), project.repository_url, None, "review-submit-001"
    )
    deployment = service.plan_intent(founder(), intent.id)
    review = service.create_customer_plan_review(founder(), deployment.id)

    submitted = service.submit_infrastructure_plan(founder(), review.id)
    detail = service.infrastructure_plan_revision_detail(founder(), submitted.id)
    assert detail["state"] == InfrastructurePlanState.SUBMITTED
    assert detail["execution"] == "UNEXECUTED_APPROVAL_ONLY"

    approved = service.decide_infrastructure_plan(
        operator(), review.id, InfrastructurePlanDecision.APPROVED, review.content_digest
    )
    decision = service.infrastructure_plan_revision_detail(founder(), approved.id)["decision"]
    assert approved.state == InfrastructurePlanState.APPROVED
    assert decision["is_self_approval"] is False
    assert deployment.state != "READY"
