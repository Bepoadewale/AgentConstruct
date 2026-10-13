from __future__ import annotations

import pytest
from agentconstruct.domain import (
    InfrastructurePlanDecision,
    InfrastructurePlanState,
    LifecycleState,
)
from agentconstruct.models import (
    DesiredStatePublication,
    GitHubAppInstallationState,
    RepositoryConnection,
)
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


def test_administrator_can_record_fixture_pr_checks_passed_for_approved_revision():
    service, _ = make_service()
    approved = approved_customer_review(service)
    publication = service.create_desired_state_publication_for_revision(
        founder(), approved.id, approved.content_digest
    )

    with pytest.raises(PermissionError, match="workspace administrator"):
        service.update_desired_state_publication_state(
            founder(),
            approved.id,
            publication["id"],
            content_digest=approved.content_digest,
            state="CHECKS_PASSED",
        )

    updated = service.update_desired_state_publication_state(
        operator(),
        approved.id,
        publication["id"],
        content_digest=approved.content_digest,
        state="CHECKS_PASSED",
    )

    assert updated["state"] == "CHECKS_PASSED"
    assert updated["merge_boundary"] == "AgentConstruct never merges the desired-state PR itself."
    assert any(
        event.action == "desired_state.fixture_pr_state_recorded"
        for event in service.audits(operator())
    )


def test_fixture_pr_state_update_rejects_stale_digest_and_invalid_transition():
    service, _ = make_service()
    approved = approved_customer_review(service)
    publication = service.create_desired_state_publication_for_revision(
        founder(), approved.id, approved.content_digest
    )

    with pytest.raises(ValueError, match="stale desired-state state update"):
        service.update_desired_state_publication_state(
            operator(),
            approved.id,
            publication["id"],
            content_digest="0" * 64,
            state="CHECKS_PASSED",
        )

    service.update_desired_state_publication_state(
        operator(),
        approved.id,
        publication["id"],
        content_digest=approved.content_digest,
        state="CHECKS_PASSED",
    )
    with pytest.raises(ValueError, match="cannot change fixture PR state"):
        service.update_desired_state_publication_state(
            operator(),
            approved.id,
            publication["id"],
            content_digest=approved.content_digest,
            state="CHECKS_PENDING",
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


def test_cloud_readiness_preflight_blocks_until_runtime_identity_is_configured():
    service, db = make_service()
    approved = approved_app_runner_customer_review(service)
    service.create_terraform_plan_render_for_revision(founder(), approved.id, approved.content_digest)
    service.create_desired_state_publication_for_revision(founder(), approved.id, approved.content_digest)
    publication = db.scalar(
        select(DesiredStatePublication).where(DesiredStatePublication.revision_id == approved.id)
    )
    publication.state = "CHECKS_PASSED"
    db.commit()

    preflight = service.create_cloud_readiness_preflight(
        founder(),
        approved.id,
        content_digest=approved.content_digest,
        expected_account_id=None,
        allowed_regions=["us-east-1"],
        required_tags={"ManagedBy": "AgentConstruct"},
        budget_ceiling_usd=1000,
        execution_mode="DRY_RUN_ONLY",
        require_reviewed_pr=True,
        runtime_identity_configured=False,
    )

    assert preflight["state"] == "BLOCKED_CLOUD_RUNTIME_NOT_CONFIGURED"
    failures = [item["id"] for item in preflight["checklist"] if item["status"] == "FAIL"]
    assert failures == ["runtime_identity"]
    assert preflight["would_deploy"]["not_deployed"] is True
    assert "Preflight only" in preflight["would_deploy"]["boundary"]


def test_cloud_readiness_preflight_can_be_ready_for_future_authorized_plan():
    service, db = make_service()
    approved = approved_app_runner_customer_review(service)
    service.create_terraform_plan_render_for_revision(founder(), approved.id, approved.content_digest)
    service.create_desired_state_publication_for_revision(founder(), approved.id, approved.content_digest)
    publication = db.scalar(
        select(DesiredStatePublication).where(DesiredStatePublication.revision_id == approved.id)
    )
    publication.state = "CHECKS_PASSED"
    db.commit()

    preflight = service.create_cloud_readiness_preflight(
        founder(),
        approved.id,
        content_digest=approved.content_digest,
        expected_account_id=None,
        allowed_regions=["us-east-1"],
        required_tags={"ManagedBy": "AgentConstruct"},
        budget_ceiling_usd=1000,
        execution_mode="DRY_RUN_ONLY",
        require_reviewed_pr=True,
        runtime_identity_configured=True,
    )

    assert preflight["state"] == "READY_FOR_AUTHORIZED_CLOUD_PLAN"
    assert {item["status"] for item in preflight["checklist"]} == {"PASS"}
    assert preflight["would_deploy"]["terraform_root"] == "infrastructure/terraform/renderers/app-runner-plan"


def test_cloud_readiness_preflight_records_guardrail_failures_without_cloud_action():
    service, _ = make_service()
    approved = approved_app_runner_customer_review(service)
    service.create_terraform_plan_render_for_revision(founder(), approved.id, approved.content_digest)

    preflight = service.create_cloud_readiness_preflight(
        founder(),
        approved.id,
        content_digest=approved.content_digest,
        expected_account_id="123456789012",
        allowed_regions=["eu-west-1"],
        required_tags={"MissingTag": "required"},
        budget_ceiling_usd=1,
        execution_mode="DRY_RUN_ONLY",
        require_reviewed_pr=True,
        runtime_identity_configured=False,
    )

    failed = {item["id"] for item in preflight["checklist"] if item["status"] == "FAIL"}
    assert preflight["state"] == "BLOCKED_GUARDRAIL_FAILURE"
    assert {
        "expected_account",
        "allowed_region",
        "required_tags",
        "budget_ceiling",
        "reviewed_pr",
        "runtime_identity",
    }.issubset(failed)
    assert preflight["execution"] == "LOCAL_PREFLIGHT_ONLY"


def test_cloud_readiness_preflight_rejects_stale_digest():
    service, _ = make_service()
    approved = approved_app_runner_customer_review(service)
    service.create_terraform_plan_render_for_revision(founder(), approved.id, approved.content_digest)

    with pytest.raises(ValueError, match="stale cloud preflight"):
        service.create_cloud_readiness_preflight(
            founder(),
            approved.id,
            content_digest="0" * 64,
            expected_account_id=None,
            allowed_regions=["us-east-1"],
            required_tags={},
            budget_ceiling_usd=None,
            execution_mode="DRY_RUN_ONLY",
            require_reviewed_pr=False,
            runtime_identity_configured=False,
        )


def ready_app_runner_preflight(service, db, approved):
    service.create_terraform_plan_render_for_revision(operator(), approved.id, approved.content_digest)
    publication = service.create_desired_state_publication_for_revision(
        operator(), approved.id, approved.content_digest
    )
    service.update_desired_state_publication_state(
        operator(),
        approved.id,
        publication["id"],
        content_digest=approved.content_digest,
        state="CHECKS_PASSED",
    )
    return service.create_cloud_readiness_preflight(
        operator(),
        approved.id,
        content_digest=approved.content_digest,
        expected_account_id=None,
        allowed_regions=["us-east-1"],
        required_tags={"ManagedBy": "AgentConstruct"},
        budget_ceiling_usd=1000,
        execution_mode="PLAN_ONLY",
        require_reviewed_pr=True,
        runtime_identity_configured=True,
    )


def test_terraform_plan_review_is_administrator_only():
    service, db = make_service()
    approved = approved_app_runner_customer_review(service)
    preflight = ready_app_runner_preflight(service, db, approved)

    with pytest.raises(PermissionError, match="workspace administrator"):
        service.create_terraform_plan_review_for_revision(
            founder(),
            approved.id,
            content_digest=approved.content_digest,
            preflight_id=preflight["id"],
            expected_account_id=None,
            expected_region="us-east-1",
            mode="LOCAL_CONTRACT_ONLY",
            allow_cloud_plan=False,
        )


def test_terraform_plan_review_blocks_without_preflight_or_render():
    service, _ = make_service()
    approved = approved_app_runner_customer_review(service)

    review = service.create_terraform_plan_review_for_revision(
        operator(),
        approved.id,
        content_digest=approved.content_digest,
        preflight_id=None,
        expected_account_id=None,
        expected_region="us-east-1",
        mode="LOCAL_CONTRACT_ONLY",
        allow_cloud_plan=False,
    )

    assert review["state"] == "BLOCKED_PREFLIGHT_REQUIRED"
    assert review["apply_available"] is False
    assert any("Generate an App Runner Terraform contract" in blocker for blocker in review["evidence"]["blockers"])
    assert any("Run a cloud-readiness preflight" in blocker for blocker in review["evidence"]["blockers"])


def test_terraform_plan_review_blocks_failed_cloud_preflight():
    service, _ = make_service()
    approved = approved_app_runner_customer_review(service)
    service.create_terraform_plan_render_for_revision(operator(), approved.id, approved.content_digest)
    preflight = service.create_cloud_readiness_preflight(
        operator(),
        approved.id,
        content_digest=approved.content_digest,
        expected_account_id="123456789012",
        allowed_regions=["eu-west-1"],
        required_tags={"ManagedBy": "AgentConstruct"},
        budget_ceiling_usd=1,
        execution_mode="PLAN_ONLY",
        require_reviewed_pr=True,
        runtime_identity_configured=False,
    )

    review = service.create_terraform_plan_review_for_revision(
        operator(),
        approved.id,
        content_digest=approved.content_digest,
        preflight_id=preflight["id"],
        expected_account_id=None,
        expected_region="us-east-1",
        mode="LOCAL_CONTRACT_ONLY",
        allow_cloud_plan=False,
    )

    assert review["state"] == "BLOCKED_PREFLIGHT"
    assert "Cloud-readiness preflight is BLOCKED_GUARDRAIL_FAILURE." in review["evidence"]["blockers"]
    assert all("apply" not in command for command in review["command"]["commands"])


def test_terraform_plan_review_records_local_plan_only_evidence_after_ready_preflight():
    service, db = make_service()
    approved = approved_app_runner_customer_review(service)
    preflight = ready_app_runner_preflight(service, db, approved)

    review = service.create_terraform_plan_review_for_revision(
        operator(),
        approved.id,
        content_digest=approved.content_digest,
        preflight_id=preflight["id"],
        expected_account_id=None,
        expected_region="us-east-1",
        mode="LOCAL_CONTRACT_ONLY",
        allow_cloud_plan=False,
    )
    detail = service.infrastructure_plan_revision_detail(operator(), approved.id)

    assert review["state"] == "LOCAL_CONTRACT_PLAN_REVIEWED"
    assert review["execution"] == "PLAN_ONLY_REVIEW_NO_APPLY"
    assert review["apply_available"] is False
    assert review["evidence"]["plan_digest_embedded"] is True
    assert any("terraform -chdir=" in command for command in review["command"]["commands"])
    assert all(" apply" not in command for command in review["command"]["commands"])
    assert detail["terraform_plan_reviews"][0]["id"] == review["id"]
    assert any(
        event.action == "terraform.plan_only_review_recorded"
        for event in service.audits(operator())
    )


def test_authenticated_terraform_plan_review_requires_explicit_operator_flag(monkeypatch):
    service, db = make_service()
    approved = approved_app_runner_customer_review(service)
    preflight = ready_app_runner_preflight(service, db, approved)
    monkeypatch.delenv("ALLOW_CLOUD_PLAN", raising=False)

    review = service.create_terraform_plan_review_for_revision(
        operator(),
        approved.id,
        content_digest=approved.content_digest,
        preflight_id=preflight["id"],
        expected_account_id=None,
        expected_region="us-east-1",
        mode="AUTHENTICATED_TERRAFORM_PLAN",
        allow_cloud_plan=False,
    )

    assert review["state"] == "BLOCKED_CLOUD_PLAN_NOT_ALLOWED"
    assert review["command"]["executor"] == "authenticated-terraform-plan-gated"
    assert review["evidence"]["allow_cloud_plan_env"] is False
    assert review["apply_available"] is False


def test_terraform_plan_review_rejects_stale_digest():
    service, db = make_service()
    approved = approved_app_runner_customer_review(service)
    preflight = ready_app_runner_preflight(service, db, approved)

    with pytest.raises(ValueError, match="stale Terraform plan review"):
        service.create_terraform_plan_review_for_revision(
            operator(),
            approved.id,
            content_digest="0" * 64,
            preflight_id=preflight["id"],
            expected_account_id=None,
            expected_region="us-east-1",
            mode="LOCAL_CONTRACT_ONLY",
            allow_cloud_plan=False,
        )
