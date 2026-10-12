from __future__ import annotations

import pytest
from agentconstruct.domain import (
    InfrastructurePlanDecision,
    InfrastructurePlanState,
    LifecycleState,
)
from agentconstruct.models import GitHubAppInstallationState, RepositoryConnection
from sqlalchemy import select
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


def approved_app_runner_customer_review(service):
    return approved_customer_review(
        service,
        (
            "Deploy this small FastAPI AI application in AWS. It receives about 2 requests per "
            "second and may peak at 10 requests per second. Use normal CPU web serving. Keep it "
            "private where practical. Keep infrastructure below $700/month. Create staging and "
            "production. Enable monitoring."
        ),
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


def test_approved_customer_review_publishes_fixture_desired_state_pr_contract():
    service, _ = make_service()
    approved = approved_customer_review(service)

    publication = service.create_desired_state_publication_for_revision(
        founder(), approved.id, approved.content_digest
    )
    detail = service.infrastructure_plan_revision_detail(founder(), approved.id)

    assert publication["state"] == "PUBLISHED"
    assert publication["publication_url"].startswith("fixture-pr://")
    assert publication["required_checks"] == ["agentconstruct-plan", "agentconstruct-policy"]
    assert publication["package"]["kind"] == "agentconstruct.desired-state-package.v1"
    assert publication["package"]["profile"] == "aws-ecs-fargate"
    assert "infrastructure/aws-ecs-fargate/contract.json" in [
        file["path"] for file in publication["package"]["files"]
    ]
    assert publication["merge_boundary"] == "AgentConstruct never merges the desired-state PR itself."
    assert detail["desired_state_publications"][0]["id"] == publication["id"]
    assert any(
        event.action == "desired_state.fixture_pr_published"
        for event in service.audits(founder())
    )


def test_desired_state_publication_requires_exact_approved_digest():
    service, _ = make_service()
    approved = approved_customer_review(service)

    with pytest.raises(ValueError, match="stale desired-state publication"):
        service.create_desired_state_publication_for_revision(founder(), approved.id, "0" * 64)


def test_desired_state_publication_rejects_changed_repository_branch():
    service, db = make_service()
    approved = approved_customer_review(service)
    plan = service._infrastructure_plan(founder(), approved.infrastructure_plan_id)
    connection = db.scalar(
        select(RepositoryConnection).where(RepositoryConnection.project_id == plan.project_id)
    )
    connection.selected_branch = "release"
    db.commit()

    with pytest.raises(ValueError, match="branch changed"):
        service.create_desired_state_publication_for_revision(
            founder(), approved.id, approved.content_digest
        )


def test_desired_state_publication_rejects_revoked_github_installation():
    service, db = make_service()
    approved = approved_customer_review(service)
    db.add(
        GitHubAppInstallationState(
            organization_id=founder().organization_id,
            installation_id="fixture-installation",
            account_login="demo-ai-startup",
            state="REVOKED",
        )
    )
    db.commit()

    with pytest.raises(PermissionError, match="REVOKED"):
        service.create_desired_state_publication_for_revision(
            founder(), approved.id, approved.content_digest
        )


def test_eks_desired_state_package_contains_gitops_contract_only_when_profile_requires_it():
    service, _ = make_service()
    approved = approved_customer_review(
        service,
        "Deploy this multi-service AI inference API in AWS. GPU acceleration is required. Kubernetes is required for GPU scheduling, isolation and controlled rollouts. Support 20 requests per second and peak at 100 requests per second. Keep monthly infrastructure under $1500. Create staging and production.",
    )

    publication = service.create_desired_state_publication_for_revision(
        founder(), approved.id, approved.content_digest
    )
    contract_file = next(
        file for file in publication["package"]["files"] if file["path"].endswith("/contract.json")
    )

    assert publication["package"]["profile"] == "aws-eks-governed"
    assert contract_file["content"]["kubernetes_required"] is True
    assert "argocd_application" in contract_file["content"]["resources"]


def test_simple_fastapi_approved_plan_renders_app_runner_terraform_contract_not_eks():
    service, _ = make_service()
    approved = approved_app_runner_customer_review(service)

    render = service.create_terraform_plan_render_for_revision(
        founder(), approved.id, approved.content_digest
    )
    detail = service.infrastructure_plan_revision_detail(founder(), approved.id)

    assert approved.content["summary"]["selected_profile"] == "aws-app-runner"
    assert render["profile"] == "aws-app-runner"
    assert render["state"] == "PLAN_ONLY_NOT_APPLIED"
    assert render["render"]["module_path"] == "infrastructure/terraform/modules/app-runner-plan-contract"
    assert render["render"]["module_inputs"]["profile"] == "aws-app-runner"
    assert render["render"]["module_inputs"]["service_name"] != "aws-eks-governed"
    assert render["render"]["apply_command_available"] is False
    assert all("apply" not in command for command in render["render"]["commands"])
    assert detail["terraform_plan_renders"][0]["id"] == render["id"]


def test_app_runner_terraform_contract_embeds_exact_approved_hash_and_tags():
    service, _ = make_service()
    approved = approved_app_runner_customer_review(service)

    render = service.create_terraform_plan_render_for_revision(
        founder(), approved.id, approved.content_digest
    )
    inputs = render["render"]["module_inputs"]
    files = render["render"]["files"]

    assert inputs["plan_digest"] == approved.content_digest
    assert inputs["environment_variables"]["AGENTCONSTRUCT_PLAN_DIGEST"] == approved.content_digest
    assert inputs["tags"]["AgentConstructPlanDigest"] == approved.content_digest
    assert approved.content_digest in str(files)


def test_eks_plan_does_not_use_app_runner_terraform_renderer():
    service, _ = make_service()
    approved = approved_customer_review(
        service,
        "Deploy this multi-service AI inference API in AWS. GPU acceleration is required. Kubernetes is required for GPU scheduling, isolation and controlled rollouts. Support 20 requests per second and peak at 100 requests per second. Keep monthly infrastructure under $1500. Create staging and production.",
    )

    assert approved.content["summary"]["selected_profile"] == "aws-eks-governed"
    with pytest.raises(ValueError, match="only supports aws-app-runner"):
        service.create_terraform_plan_render_for_revision(
            founder(), approved.id, approved.content_digest
        )


def test_terraform_renderer_fails_closed_for_stale_digest_and_unapproved_revision():
    service, _ = make_service()
    approved = approved_app_runner_customer_review(service)

    with pytest.raises(ValueError, match="stale Terraform render"):
        service.create_terraform_plan_render_for_revision(founder(), approved.id, "0" * 64)

    project = service.create_project(
        founder(), "unapproved-render", "https://github.com/example/unapproved-render", "main"
    )
    intent = service.create_intent(
        founder(),
        project.id,
        "Deploy this small FastAPI AI application in AWS. It receives about 2 requests per second and may peak at 10. Keep infrastructure below $700/month. Create staging and production. Enable monitoring.",
        project.repository_url,
        None,
        "unapproved-render-001",
    )
    deployment = service.plan_intent(founder(), intent.id)
    draft = service.create_customer_plan_review(founder(), deployment.id)
    with pytest.raises(ValueError, match="must be approved"):
        service.create_terraform_plan_render_for_revision(founder(), draft.id, draft.content_digest)
