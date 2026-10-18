"""Independent deterministic policy Lambda.

The model and browser cannot invoke privileged work through this function.
It evaluates only the typed decision input used by the control plane.
"""

from __future__ import annotations

from typing import Any

from agentconstruct.domain import PolicyResult


def handler(event: dict[str, Any], _context: Any) -> dict[str, dict[str, str]]:
    payload = event.get("input")
    if not isinstance(payload, dict):
        return _decision(PolicyResult.DENY, "policy input is missing")
    principal = payload.get("principal") or {}
    spec = payload.get("spec") or {}
    if not principal.get("subject") or not principal.get("organization_id"):
        return _decision(PolicyResult.DENY, "tenant-bound principal is required")
    if payload.get("action") == "CHANGE":
        if payload.get("target_environment_type") == "production":
            return _decision(
                PolicyResult.APPROVAL_REQUIRED,
                "production change needs an independent approval",
            )
        return _decision(PolicyResult.ALLOW, "non-production change is allowed")
    if spec.get("monthly_budget_usd", 0) > 1500:
        return _decision(PolicyResult.DENY, "requested budget exceeds the safety limit")
    if "production" in spec.get("environments", []):
        return _decision(
            PolicyResult.APPROVAL_REQUIRED,
            "production deployment needs an independent approval",
        )
    return _decision(PolicyResult.ALLOW, "development deployment is allowed")


def _decision(result: PolicyResult, reason: str) -> dict[str, dict[str, str]]:
    return {"result": {"result": result.value, "reason": reason}}
