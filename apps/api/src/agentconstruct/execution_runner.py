"""Isolated execution boundary for future cells and provider runners.

The local adapter is intentionally bounded and does not invoke a shell, Terraform,
Kubernetes, or cloud API. Hosted runners must implement the same contract and obtain
short-lived credentials outside this domain module.
"""

from __future__ import annotations

from typing import Protocol

from agentconstruct.contracts import (
    ExecutionContext,
    ExecutionOperation,
    ExecutionOutcome,
)


class ExecutionRunner(Protocol):
    def run(self, context: ExecutionContext) -> ExecutionOutcome: ...


class DisabledExecutionRunner:
    """Fail closed until an explicitly configured isolated runner exists."""

    def run(self, context: ExecutionContext) -> ExecutionOutcome:
        return ExecutionOutcome(
            execution_id=context.execution_id,
            tenant=context.tenant,
            state="BLOCKED_RUNNER_NOT_CONFIGURED",
            failure_reason="No isolated execution runner is configured.",
            runner="disabled",
        )


class FixtureExecutionRunner:
    """Deterministic local runner for contract tests; no external side effects."""

    def run(self, context: ExecutionContext) -> ExecutionOutcome:
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
