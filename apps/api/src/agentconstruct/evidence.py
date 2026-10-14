"""Evidence and pricing adapter contracts used by the planner."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import ClassVar, Protocol

from agentconstruct.contracts import CostEvidence


class PricingCatalog(Protocol):
    catalog_version: str

    def quote(self, profile: str, region: str) -> CostEvidence: ...


class FixturePricingCatalog:
    """Small transparent catalog; it is an estimate, never an AWS bill."""

    catalog_version: ClassVar[str] = "aws-fixture-pricing-2026-10"
    ranges: ClassVar[dict[str, tuple[int, int]]] = {
        "aws-lambda-api": (30, 120),
        "aws-app-runner": (65, 180),
        "aws-ecs-fargate": (120, 310),
        "aws-eks-governed": (950, 1450),
        "aws-gpu-inference": (780, 1650),
    }

    def quote(self, profile: str, region: str) -> CostEvidence:
        low, high = self.ranges.get(profile, (0, 0))
        assumptions = (
            f"fixture estimate for {profile} in {region}",
            "does not include customer-specific discounts or settled billing",
        )
        return CostEvidence(
            monthly_low=low,
            monthly_high=high,
            catalog_version=self.catalog_version,
            captured_at=datetime.now(UTC),
            assumptions=assumptions,
            actual_billing=False,
        )
