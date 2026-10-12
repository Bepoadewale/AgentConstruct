from __future__ import annotations

import pytest
from agentconstruct.domain import (
    InfrastructurePlanDecision,
    InfrastructurePlanState,
    LifecycleState,
)
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


def approved_customer_review(service, prompt: str | None = None):
    project = service.create_project(
        founder(), "review-dry-run", "https://github.com/example/review-dry-run", "main"
    )
    intent = service.create_intent(
        founder(),
        project.id,
        prompt or complete_prompt(500),
        project.repository_url,
        None,
        "review-dry-run-001",
    )
    deployment = service.plan_intent(founder(), intent.id)
    review = service.create_customer_plan_review(founder(), deployment.id)
    service.submit_infrastructure_plan(founder(), review.id)
    return service.decide_infrastructure_plan(
        operator(), review.id, InfrastructurePlanDecision.APPROVED, review.content_digest
    )


def test_approved_customer_review_executes_bounded_local_dry_run_and_observes_ready():
    service, _ = make_service()
    approved = approved_customer_review(service)
    detail = service.infrastructure_plan_revision_detail(founder(), approved.id)
    assert detail["local_executions"] == []
    assert detail["execution"] == "UNEXECUTED_APPROVAL_ONLY"

    environments = service.execute_customer_plan_dry_run(founder(), approved.id)
    assert {environment.state for environment in environments} == {LifecycleState.QUEUED}
    assert all(
        environment.desired_state["customer_plan_revision_id"] == approved.id
        for environment in environments
    )
    assert all(environment.desired_state["execution_mode"] == "LOCAL_DRY_RUN" for environment in environments)

    while service.run_next_job():
        pass

    refreshed = service.infrastructure_plan_revision_detail(founder(), approved.id)
    states = {environment["state"] for environment in refreshed["local_executions"]}
    assert states == {LifecycleState.READY}
    assert all(environment["cost_estimate"] for environment in refreshed["local_executions"])
    assert any(
        event.action == "customer_plan.local_dry_run_queued"
        for event in service.audits(founder())
    )


def test_customer_review_cannot_execute_before_approval_and_can_observe_failure():
    service, _ = make_service()
    project = service.create_project(
        founder(), "review-failure", "https://github.com/example/review-failure", "main"
    )
    intent = service.create_intent(
        founder(),
        project.id,
        f"{complete_prompt(500)} Force failure local readiness evidence.",
        project.repository_url,
        None,
        "review-failure-001",
    )
    deployment = service.plan_intent(founder(), intent.id)
    review = service.create_customer_plan_review(founder(), deployment.id)
    with pytest.raises(ValueError, match="must be approved"):
        service.execute_customer_plan_dry_run(founder(), review.id)

    service.submit_infrastructure_plan(founder(), review.id)
    approved = service.decide_infrastructure_plan(
        operator(), review.id, InfrastructurePlanDecision.APPROVED, review.content_digest
    )
    service.execute_customer_plan_dry_run(founder(), approved.id)
    while service.run_next_job():
        pass
    refreshed = service.infrastructure_plan_revision_detail(founder(), approved.id)
    assert {environment["state"] for environment in refreshed["local_executions"]} == {
        LifecycleState.FAILED
    }


def test_customer_review_local_destroy_is_tied_to_revision_and_observed():
    service, _ = make_service()
    approved = approved_customer_review(service)
    environments = service.execute_customer_plan_dry_run(founder(), approved.id)
    while service.run_next_job():
        pass
    production = next(
        environment
        for environment in environments
        if environment.environment_type == "production"
    )

    destroy = service.customer_plan_destroy_plan(founder(), approved.id, production.id)
    assert destroy.state == LifecycleState.DESTROY_APPROVAL_REQUIRED
    assert destroy.payload["customer_plan_revision_id"] == approved.id
    with pytest.raises(PermissionError):
        service.approve(founder(), destroy.id, destroy.plan_hash)

    service.approve(operator(), destroy.id, destroy.plan_hash)
    service.execute(operator(), destroy.id)
    while service.run_next_job():
        pass
    refreshed = service.infrastructure_plan_revision_detail(founder(), approved.id)
    production_execution = next(
        environment
        for environment in refreshed["local_executions"]
        if environment["id"] == production.id
    )
    assert production_execution["state"] == LifecycleState.DESTROYED
    assert any(event.action == "customer_plan.local_destroy_requested" for event in service.audits(founder()))
