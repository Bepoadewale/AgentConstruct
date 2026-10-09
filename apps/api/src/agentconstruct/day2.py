from __future__ import annotations

from datetime import UTC, datetime

from agentconstruct.domain import CostRange, OptimizationRecommendation, TelemetryEvidence
from agentconstruct.models import Environment

FIXTURE_CAPTURED_AT = datetime(2026, 10, 9, tzinfo=UTC)


class FixtureDay2Advisor:
    """Deterministic local evidence, intentionally not a cloud telemetry integration."""

    def recommend(self, environment: Environment) -> OptimizationRecommendation:
        current_min_replicas = int(environment.desired_state.get("min_replicas", 1))
        evidence = TelemetryEvidence(
            source="deterministic-local-telemetry-fixture",
            captured_at=FIXTURE_CAPTURED_AT,
            p95_latency_ms=2800,
            queue_time_ms=1200,
            utilization_percent=92,
            current_min_replicas=current_min_replicas,
        )
        target_min_replicas = current_min_replicas + 1
        return OptimizationRecommendation(
            recommendation_id=f"latency-scale-{environment.id}",
            diagnosis="Queue time and replica utilization are high enough to explain the p95 latency increase.",
            evidence=evidence,
            proposed_change={
                "kind": "increase_min_replicas",
                "from": current_min_replicas,
                "to": target_min_replicas,
                "reason": "Reduce queueing while keeping the change bounded.",
            },
            estimated_monthly_cost_delta=CostRange(
                monthly_low=25,
                monthly_high=40,
                assumptions=[
                    "Local fixture estimate only; it is not an AWS bill.",
                    "One additional minimum application replica is available for the full month.",
                ],
                catalog_version="local-day2-fixture-2026-10",
                estimated_at=FIXTURE_CAPTURED_AT,
            ),
            risk="low",
            rollback="Create a new governed change plan that restores the previous minimum replica count.",
            assumptions=[
                "The deterministic telemetry fixture represents sustained saturation.",
                "The existing environment can safely run one additional replica.",
            ],
            requires_approval=environment.environment_type == "production",
            execution_boundary=(
                "The local executor can only call its fixed fixture endpoint. It cannot change AWS, "
                "Kubernetes, Terraform, shell state, or secrets."
            ),
        )
