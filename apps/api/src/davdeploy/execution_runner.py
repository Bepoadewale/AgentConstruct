"""Isolated execution boundary for future cells and provider runners.

The local adapter is intentionally bounded and does not invoke a shell, Terraform,
Kubernetes, or cloud API. Hosted runners must implement the same contract and obtain
short-lived credentials outside this domain module.
"""

from __future__ import annotations

from typing import Protocol

from pydantic import BaseModel, ConfigDict

from davdeploy.boundaries import RunnerLimits, validate_runner_context
from davdeploy.contracts import (
    ExecutionContext,
    ExecutionOperation,
    ExecutionOutcome,
)


class RunnerPreparation(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    execution_id: str
    runner: str
    prepared: bool = False
    reason: str | None = None


class ExecutionRunner(Protocol):
    def prepare(self, context: ExecutionContext) -> RunnerPreparation: ...
    def execute(self, context: ExecutionContext) -> ExecutionOutcome: ...
    def observe(self, context: ExecutionContext) -> ExecutionOutcome: ...
    def destroy(self, context: ExecutionContext) -> ExecutionOutcome: ...
    def cancel(self, context: ExecutionContext) -> ExecutionOutcome: ...
    def collect_evidence(self, context: ExecutionContext) -> tuple[str, ...]: ...

    def run(self, context: ExecutionContext) -> ExecutionOutcome: ...


class DisabledExecutionRunner:
    """Fail closed until an explicitly configured isolated runner exists."""

    def prepare(self, context: ExecutionContext) -> RunnerPreparation:
        return RunnerPreparation(execution_id=context.execution_id, runner="disabled", reason="runner not configured")

    def _blocked(self, context: ExecutionContext) -> ExecutionOutcome:
        return ExecutionOutcome(
            execution_id=context.execution_id,
            tenant=context.tenant,
            state="BLOCKED_RUNNER_NOT_CONFIGURED",
            failure_reason="No isolated execution runner is configured.",
            runner="disabled",
        )

    def execute(self, context: ExecutionContext) -> ExecutionOutcome:
        return self._blocked(context)

    observe = execute
    destroy = execute
    cancel = execute

    def collect_evidence(self, context: ExecutionContext) -> tuple[str, ...]:
        return (f"runner-disabled:{context.execution_id}",)

    def run(self, context: ExecutionContext) -> ExecutionOutcome:
        return self._blocked(context)


class FixtureExecutionRunner:
    """Deterministic local runner for contract tests; no external side effects."""

    def __init__(self, limits: RunnerLimits | None = None):
        self.limits = limits or RunnerLimits(allowed_operations=frozenset({ExecutionOperation.PLAN, ExecutionOperation.OBSERVE, ExecutionOperation.APPLY, ExecutionOperation.DESTROY}))

    def prepare(self, context: ExecutionContext) -> RunnerPreparation:
        try:
            validate_runner_context(context, self.limits)
        except ValueError as error:
            return RunnerPreparation(execution_id=context.execution_id, runner="fixture", reason=str(error))
        return RunnerPreparation(execution_id=context.execution_id, runner="fixture", prepared=True)

    def _run(self, context: ExecutionContext) -> ExecutionOutcome:
        if context.operation not in context.allowed_operations:
            return ExecutionOutcome(
                execution_id=context.execution_id,
                tenant=context.tenant,
                state="DENIED_OPERATION_NOT_ALLOWLISTED",
                failure_reason=f"{context.operation.value} is not allowlisted for this run.",
                runner="fixture",
            )
        if context.operation is ExecutionOperation.APPLY:
            state = "SIMULATED_APPLY"
        elif context.operation is ExecutionOperation.DESTROY:
            state = "SIMULATED_DESTROY"
        elif context.operation is ExecutionOperation.OBSERVE:
            state = "OBSERVED"
        else:
            state = "PLANNED"
        return ExecutionOutcome(
            execution_id=context.execution_id,
            tenant=context.tenant,
            state=state,
            observed=context.operation in {ExecutionOperation.OBSERVE, ExecutionOperation.APPLY, ExecutionOperation.DESTROY},
            outputs={"plan_digest": context.plan_digest, "cell_id": context.placement.cell_id},
            runner="fixture",
        )

    def execute(self, context: ExecutionContext) -> ExecutionOutcome:
        return self._run(context.model_copy(update={"operation": ExecutionOperation.APPLY}))

    def observe(self, context: ExecutionContext) -> ExecutionOutcome:
        return self._run(context.model_copy(update={"operation": ExecutionOperation.OBSERVE}))

    def destroy(self, context: ExecutionContext) -> ExecutionOutcome:
        return self._run(context.model_copy(update={"operation": ExecutionOperation.DESTROY}))

    def cancel(self, context: ExecutionContext) -> ExecutionOutcome:
        return ExecutionOutcome(execution_id=context.execution_id, tenant=context.tenant, state="CANCELLED", observed=True, runner="fixture")

    def collect_evidence(self, context: ExecutionContext) -> tuple[str, ...]:
        return (f"fixture-runner:{context.execution_id}", f"plan-digest:{context.plan_digest}")

    def run(self, context: ExecutionContext) -> ExecutionOutcome:
        return self._run(context)
