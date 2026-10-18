from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Protocol

import boto3
import httpx
from botocore.exceptions import BotoCoreError, ClientError

from davdeploy.domain import PolicyResult, WorkloadSpec
from davdeploy.security import Principal


@dataclass(frozen=True)
class PolicyDecision:
    result: PolicyResult
    reason: str


@dataclass(frozen=True)
class AuthorizationRequest:
    actor_id: str
    tenant_id: str
    operation: str
    plan_digest: str
    scope: str
    approval: str | None = None


class AuthorizationService(Protocol):
    def authorize(self, request: AuthorizationRequest) -> PolicyDecision: ...


class FailClosedAuthorizationService:
    """Independent authorization boundary for non-HTTP clients and runners."""

    def __init__(self, policy: PolicyClient | None = None):
        self.policy = policy

    def authorize(self, request: AuthorizationRequest) -> PolicyDecision:
        if not request.actor_id or not request.tenant_id or len(request.plan_digest) != 64 or not request.scope:
            return PolicyDecision(PolicyResult.DENY, "authorization request is incomplete")
        if request.operation in {"apply", "destroy", "remediate"} and not request.approval:
            return PolicyDecision(PolicyResult.APPROVAL_REQUIRED, "privileged operation requires approval")
        return PolicyDecision(PolicyResult.ALLOW, "authorization boundary accepted request")


class PolicyClient:
    def __init__(self, url: str | None = None, fixture: bool = False):
        self.url = url or os.getenv(
            "DAVDEPLOY_OPA_URL", "http://opa:8181/v1/data/davdeploy/decision"
        )
        self.fixture = fixture or os.getenv("DAVDEPLOY_POLICY_FIXTURE", "false").lower() == "true"
        self.function_arn = os.getenv("DAVDEPLOY_POLICY_FUNCTION_ARN")

    def evaluate(
        self,
        principal: Principal,
        spec: WorkloadSpec,
        action: str,
        target_environment_type: str | None = None,
    ) -> PolicyDecision:
        payload = {
            "principal": {
                "subject": principal.subject,
                "organization_id": principal.organization_id,
                "role": principal.role,
            },
            "spec": spec.model_dump(mode="json"),
            "action": action,
            "target_environment_type": target_environment_type,
        }
        if self.fixture:
            return self._fixture(payload)
        if self.function_arn:
            return self._invoke_lambda(payload)
        try:
            response = httpx.post(self.url, json={"input": payload}, timeout=3)
            response.raise_for_status()
            result = response.json()["result"]
            return PolicyDecision(PolicyResult(result["result"]), result["reason"])
        except (httpx.HTTPError, KeyError, ValueError) as error:
            return PolicyDecision(
                PolicyResult.DENY,
                f"policy unavailable or invalid; fail closed: {type(error).__name__}",
            )

    def _invoke_lambda(self, payload: dict) -> PolicyDecision:
        try:
            import json

            response = boto3.client("lambda").invoke(
                FunctionName=self.function_arn,
                InvocationType="RequestResponse",
                Payload=json.dumps({"input": payload}).encode(),
            )
            if response.get("FunctionError"):
                raise ValueError("policy Lambda returned a function error")
            result = json.loads(response["Payload"].read())["result"]
            return PolicyDecision(PolicyResult(result["result"]), result["reason"])
        except (
            BotoCoreError,
            ClientError,
            KeyError,
            ValueError,
            TypeError,
            json.JSONDecodeError,
        ) as error:
            return PolicyDecision(
                PolicyResult.DENY,
                f"policy unavailable or invalid; fail closed: {type(error).__name__}",
            )

    @staticmethod
    def _fixture(payload: dict) -> PolicyDecision:
        spec = payload["spec"]
        if payload["action"] == "CHANGE":
            if payload.get("target_environment_type") == "production":
                return PolicyDecision(
                    PolicyResult.APPROVAL_REQUIRED,
                    "production change needs an independent approval",
                )
            return PolicyDecision(PolicyResult.ALLOW, "non-production change is allowed")
        if spec.get("monthly_budget_usd", 0) > 1500:
            return PolicyDecision(PolicyResult.DENY, "requested budget exceeds the V1 safety limit")
        if "production" in spec.get("environments", []):
            return PolicyDecision(
                PolicyResult.APPROVAL_REQUIRED,
                "production deployment needs an independent approval",
            )
        return PolicyDecision(PolicyResult.ALLOW, "development deployment is allowed")
