"""Small deterministic benchmark for planner regressions.

Reference expectations are intentionally coarse: they test safety and architectural
direction, not one hard-coded price or a model's prose.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from davdeploy.domain import ArchitecturePlan, WorkloadSpec
from davdeploy.planner import AwsV1Planner


@dataclass(frozen=True)
class PlannerScenario:
    name: str
    build: Callable[[], WorkloadSpec]
    required_profile_terms: tuple[str, ...] = ()
    forbidden_profile_terms: tuple[str, ...] = ()
    requires_gpu: bool = False


@dataclass(frozen=True)
class ScenarioResult:
    name: str
    passed: bool
    selected_profile: str | None
    failures: tuple[str, ...] = ()


def default_scenarios() -> tuple[PlannerScenario, ...]:
    return (
        PlannerScenario(
            "tiny-stateless-api",
            lambda: WorkloadSpec(
                workload_type="api", peak_rps=10, monthly_budget_usd=300, confidence=0.9
            ),
            forbidden_profile_terms=("eks", "kubernetes"),
        ),
        PlannerScenario(
            "gpu-multiservice-inference",
            lambda: WorkloadSpec(
                workload_type="inference", peak_rps=100, monthly_budget_usd=5_000,
                requires_gpu=True, multi_service=True, requires_kubernetes=True, confidence=0.9
            ),
            required_profile_terms=("eks",),
            requires_gpu=True,
        ),
    )


def evaluate_scenario(scenario: PlannerScenario, planner: AwsV1Planner | None = None) -> ScenarioResult:
    planner = planner or AwsV1Planner()
    try:
        plan: ArchitecturePlan = planner.plan(scenario.build())
    except (ValueError, TypeError) as error:
        return ScenarioResult(scenario.name, False, None, (str(error),))
    profile = plan.profile.lower()
    failures = [
        f"selected profile {plan.profile!r} lacks {term!r}"
        for term in scenario.required_profile_terms
        if term not in profile
    ]
    failures.extend(
        f"selected profile {plan.profile!r} contains forbidden term {term!r}"
        for term in scenario.forbidden_profile_terms
        if term in profile
    )
    if scenario.requires_gpu and not any("gpu" in component.service.lower() for component in plan.components):
        failures.append("GPU scenario selected no GPU component")
    return ScenarioResult(scenario.name, not failures, plan.profile, tuple(failures))


def run_default_benchmark(planner: AwsV1Planner | None = None) -> tuple[ScenarioResult, ...]:
    return tuple(evaluate_scenario(scenario, planner) for scenario in default_scenarios())
