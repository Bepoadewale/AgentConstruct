from agentconstruct.contracts import (
    ExecutionContext,
    ExecutionOperation,
    ExecutionPlacement,
    TenantScope,
)
from agentconstruct.execution_runner import DisabledExecutionRunner, FixtureExecutionRunner


def tenant(org="org-demo"):
    return TenantScope(
        organization_id=org,
        workspace_id="workspace-demo",
        project_id="project-demo",
        actor_id="user-demo",
    )


def context(operation=ExecutionOperation.OBSERVE, org="org-demo"):
    return ExecutionContext(
        tenant=tenant(org),
        placement=ExecutionPlacement(cell_id="cell-a", region="us-east-1", provider="aws"),
        plan_digest="a" * 64,
        operation=operation,
        allowed_operations=(operation,),
        credential_reference="sts://customer-role/session-1",
    )


def test_fixture_runner_is_tenant_scoped_and_returns_safe_outputs():
    result = FixtureExecutionRunner().run(context())
    assert result.tenant.organization_id == "org-demo"
    assert result.state == "OBSERVED"
    assert result.outputs["cell_id"] == "cell-a"
    assert "secret" not in str(result.outputs).lower()


def test_runner_denies_operation_not_in_allowlist():
    restricted = context(ExecutionOperation.APPLY)
    restricted = restricted.model_copy(update={"allowed_operations": (ExecutionOperation.OBSERVE,)})
    assert FixtureExecutionRunner().run(restricted).state == "DENIED_OPERATION_NOT_ALLOWLISTED"


def test_disabled_runner_fails_closed():
    result = DisabledExecutionRunner().run(context())
    assert result.state == "BLOCKED_RUNNER_NOT_CONFIGURED"


def test_context_rejects_non_digest_and_keeps_credential_as_reference():
    try:
        ExecutionContext(tenant=tenant(), plan_digest="not-a-digest", operation=ExecutionOperation.PLAN)
    except ValueError:
        pass
    else:
        raise AssertionError("invalid plan digest accepted")
