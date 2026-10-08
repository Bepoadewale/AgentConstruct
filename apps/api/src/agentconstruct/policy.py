from __future__ import annotations

import os
from dataclasses import dataclass

import httpx

from agentconstruct.domain import PolicyResult, WorkloadSpec
from agentconstruct.security import Principal


@dataclass(frozen=True)
class PolicyDecision:
    result: PolicyResult
    reason: str


class PolicyClient:
    def __init__(self, url: str | None = None, fixture: bool = False):
        self.url = url or os.getenv("AGENTCONSTRUCT_OPA_URL", "http://opa:8181/v1/data/agentconstruct/decision")
        self.fixture = fixture

    def evaluate(self, principal: Principal, spec: WorkloadSpec, action: str) -> PolicyDecision:
        payload = {
            "principal": {"subject": principal.subject, "organization_id": principal.organization_id, "role": principal.role},
            "spec": spec.model_dump(mode="json"),
            "action": action,
        }
        if self.fixture:
            return self._fixture(payload)
        try:
            response = httpx.post(self.url, json={"input": payload}, timeout=3)
            response.raise_for_status()
            result = response.json()["result"]
            return PolicyDecision(PolicyResult(result["result"]), result["reason"])
        except (httpx.HTTPError, KeyError, ValueError) as error:
            return PolicyDecision(PolicyResult.DENY, f"policy unavailable or invalid; fail closed: {type(error).__name__}")

    @staticmethod
    def _fixture(payload: dict) -> PolicyDecision:
        spec = payload["spec"]
        if spec.get("monthly_budget_usd", 0) > 1500:
            return PolicyDecision(PolicyResult.DENY, "requested budget exceeds the V1 safety limit")
        if "production" in spec.get("environments", []):
            return PolicyDecision(PolicyResult.APPROVAL_REQUIRED, "production deployment needs an independent approval")
        return PolicyDecision(PolicyResult.ALLOW, "development deployment is allowed")
