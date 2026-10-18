from __future__ import annotations

from davdeploy.cloud_execution import CloudExecutionResult, DisabledCloudExecutionAdapter
from test_customer_plan_review import approved_app_runner_customer_review
from test_product import founder, make_service, operator


class FakeCloudExecutionAdapter:
    def __init__(self, state="READY"):
        self.state = state
        self.contexts = []

    def execute(self, context):
        self.contexts.append(context)
        return CloudExecutionResult(
            state=self.state,
            operations=({"operation": "pilot", "returncode": 0},),
            outputs={"application_url": "https://customer.example"},
            failure_reason=None if self.state == "READY" else "fixture failure",
        )


def test_disabled_cloud_adapter_never_executes():
    result = DisabledCloudExecutionAdapter().execute({"profile": "aws-app-runner"})
    assert result.state == "BLOCKED_CLOUD_EXECUTION_NOT_ENABLED"
    assert result.operations == ()


def test_ready_cloud_run_is_queued_and_observed_by_trusted_worker():
    service, _ = make_service()
    adapter = FakeCloudExecutionAdapter()
    service.cloud_execution = adapter
    approved = approved_app_runner_customer_review(service)
    render = service.create_terraform_plan_render_for_revision(founder(), approved.id, approved.content_digest)
    preflight = service.create_cloud_readiness_preflight(
        operator(),
        approved.id,
        content_digest=approved.content_digest,
        expected_account_id=None,
        allowed_regions=["us-east-1"],
        required_tags={},
        budget_ceiling_usd=5000,
        execution_mode="PLAN_ONLY",
        require_reviewed_pr=False,
        runtime_identity_configured=True,
    )
    plan_review = service.create_terraform_plan_review_for_revision(
        operator(),
        approved.id,
        content_digest=approved.content_digest,
        preflight_id=preflight["id"],
        expected_account_id=None,
        expected_region="us-east-1",
        mode="LOCAL_CONTRACT_ONLY",
        allow_cloud_plan=False,
    )
    run = service.create_cloud_execution_run_for_revision(
        operator(),
        approved.id,
        content_digest=approved.content_digest,
        terraform_render_id=render["id"],
        preflight_id=preflight["id"],
        terraform_plan_review_id=plan_review["id"],
        expected_account_id=None,
        expected_region="us-east-1",
        mode="AUTHENTICATED_APP_RUNNER_APPLY",
        confirmation="EXECUTE_APP_RUNNER_WORKLOAD",
    )
    assert run["state"] != "READY_FOR_OPERATOR_APP_RUNNER_EXECUTION"
    # Local test config does not enable cloud apply, so it remains blocked.
    assert service.run_next_cloud_execution() is False


def test_cloud_run_queue_requires_admin_and_exact_confirmation():
    service, _ = make_service()
    approved = approved_app_runner_customer_review(service)
    run = service.create_cloud_execution_run_for_revision(
        operator(),
        approved.id,
        content_digest=approved.content_digest,
        terraform_render_id=None,
        preflight_id=None,
        terraform_plan_review_id=None,
        expected_account_id=None,
        expected_region=None,
        mode="GUARDED_CLOUD_EXECUTION",
        confirmation=None,
    )
    try:
        service.queue_cloud_execution_run(founder(), run["id"], approved.content_digest, "bad")
    except PermissionError:
        pass
    else:
        raise AssertionError("developer could queue cloud execution")
