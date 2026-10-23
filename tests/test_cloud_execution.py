from __future__ import annotations

from davdeploy.cloud_execution import (
    CloudExecutionResult,
    CodeBuildCloudExecutionAdapter,
    DisabledCloudExecutionAdapter,
)
from davdeploy.models import CloudExecutionRun
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


def test_codebuild_adapter_submits_only_the_fixed_execution_environment():
    calls = []

    class CodeBuild:
        def start_build(self, **kwargs):
            calls.append(kwargs)
            return {"build": {"id": "davdeploy:build-1", "arn": "arn:build-1"}}

    environment = {
        key: "value" for key in CodeBuildCloudExecutionAdapter.required_environment
    }
    environment["DAVDEPLOY_EXECUTION_OPERATION"] = "apply-foundation"
    adapter = CodeBuildCloudExecutionAdapter("davdeploy-customer-executor", client=CodeBuild())

    result = adapter.execute({"environment": environment})

    assert result.state == "SUBMITTED"
    assert result.outputs["codebuild_build_id"] == "davdeploy:build-1"
    assert calls[0]["projectName"] == "davdeploy-customer-executor"
    assert all(item["name"] != "COMMAND" for item in calls[0]["environmentVariablesOverride"])


def test_codebuild_completion_accepts_the_eventbridge_build_arn(monkeypatch):
    service, _ = make_service()
    short_id = "davdeploy-customer-executor:build-1"
    build_arn = f"arn:aws:codebuild:us-east-1:111122223333:build/{short_id}"
    run = CloudExecutionRun(
        organization_id=founder().organization_id,
        revision_id="revision-1",
        project_id="project-1",
        profile="aws-app-runner",
        state="SUBMITTED",
        mode="AUTHENTICATED_TERRAFORM_PLAN",
        attempt=1,
        command={},
        evidence={"result_s3_uri": "not-an-s3-uri"},
        outputs={"codebuild_build_id": short_id, "codebuild_build_arn": build_arn},
        content_digest="a" * 64,
        requested_by_subject=founder().subject,
    )
    service.db.add(run)
    service.db.commit()
    calls = []

    class CodeBuild:
        def batch_get_builds(self, *, ids):
            calls.append(ids)
            return {"builds": [{"buildStatus": "FAILED"}]}

    monkeypatch.setattr("davdeploy.service.boto3.client", lambda service_name: CodeBuild())

    assert service.reconcile_cloud_execution_build(build_arn) is True
    assert calls == [[short_id]]


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


def test_queueing_a_ready_cloud_run_wakes_the_worker(monkeypatch):
    service, _ = make_service()
    run = CloudExecutionRun(
        organization_id=founder().organization_id,
        revision_id="revision-queued",
        project_id="project-queued",
        profile="aws-app-runner",
        state="READY_FOR_OPERATOR_APP_RUNNER_EXECUTION",
        mode="AUTHENTICATED_APP_RUNNER_APPLY",
        attempt=1,
        command={},
        evidence={},
        outputs={},
        content_digest="b" * 64,
        requested_by_subject=founder().subject,
    )
    service.db.add(run)
    service.db.commit()
    wakeups = []
    monkeypatch.setattr(service, "_wake_worker", lambda kind, job_id: wakeups.append((kind, job_id)))

    queued = service.queue_cloud_execution_run(
        operator(), run.id, run.content_digest, "EXECUTE_APP_RUNNER_WORKLOAD"
    )

    assert queued["state"] == "QUEUED"
    assert wakeups == [("cloud_execution", run.id)]


def test_authenticated_cloud_run_requires_verified_connection_and_execution_role(monkeypatch):
    """A fixture/local plan may be reviewed, but never becomes an AWS apply request."""
    service, _ = make_service()
    approved = approved_app_runner_customer_review(service)
    monkeypatch.setenv("ALLOW_CLOUD_APPLY", "true")
    monkeypatch.setenv("DAVDEPLOY_ENABLE_APP_RUNNER_EXECUTION", "true")

    run = service.create_cloud_execution_run_for_revision(
        operator(),
        approved.id,
        content_digest=approved.content_digest,
        terraform_render_id=None,
        preflight_id=None,
        terraform_plan_review_id=None,
        expected_account_id=None,
        expected_region="us-east-1",
        mode="AUTHENTICATED_APP_RUNNER_APPLY",
        confirmation="EXECUTE_APP_RUNNER_WORKLOAD",
    )

    assert run["state"] != "READY_FOR_OPERATOR_APP_RUNNER_EXECUTION"
    assert "verified customer cloud connection" in " ".join(run["evidence"]["blockers"])
