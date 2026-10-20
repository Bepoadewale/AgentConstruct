from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Protocol

import httpx


@dataclass(frozen=True)
class ExecutionObservation:
    state: str
    detail: dict


class ExecutionAdapter(Protocol):
    def deploy(
        self,
        environment_id: str,
        profile: str,
        should_fail: bool = False,
        should_degrade: bool = False,
    ) -> ExecutionObservation: ...

    def destroy(self, environment_id: str) -> ExecutionObservation: ...

    def change(self, environment_id: str, minimum_replicas: int) -> ExecutionObservation: ...


def fixture_primary_resource(environment_id: str, profile: str, status: str) -> tuple[dict, dict]:
    resource_families = {
        "aws-lambda-api": (
            "lambda_function_arn",
            "lambda_function",
            f"arn:aws:lambda:us-east-1:000000000000:function:local-{environment_id}",
        ),
        "aws-app-runner": (
            "app_runner_service_arn",
            "apprunner_service",
            (
                "arn:aws:apprunner:us-east-1:000000000000:"
                f"service/local-{profile}/{environment_id}"
            ),
        ),
        "aws-ecs-fargate": (
            "ecs_service_arn",
            "ecs_service",
            (
                "arn:aws:ecs:us-east-1:000000000000:"
                f"service/local-{profile}/{environment_id}"
            ),
        ),
        "aws-eks-governed": (
            "eks_cluster_arn",
            "eks_cluster",
            f"arn:aws:eks:us-east-1:000000000000:cluster/local-{environment_id}",
        ),
    }
    output_name, resource_type, external_id = resource_families.get(
        profile,
        (
            "simulated_resource_reference",
            "simulated_service",
            f"fixture://{profile}/{environment_id}",
        ),
    )
    provider = "aws" if profile in resource_families else "fixture"
    return (
        {
            "name": output_name,
            "type": "aws_arn" if provider == "aws" else "resource_reference",
            "value": external_id,
            "visibility": "customer",
            "sensitive": False,
            "source": "fixture-observer",
            "status": status,
        },
        {
            "provider": provider,
            "resource_type": resource_type,
            "name": f"local-{profile}",
            "external_id": external_id,
            "region": "us-east-1" if provider == "aws" else None,
            "status": status,
            "tags": {
                "davdeploy:environment-id": environment_id,
                "davdeploy:execution-mode": "LOCAL_DRY_RUN",
            },
        },
    )


def fixture_deployment(
    environment_id: str,
    profile: str,
    should_fail: bool = False,
    should_degrade: bool = False,
) -> dict:
    state = "FAILED" if should_fail else "DEGRADED" if should_degrade else "READY"
    app_url = f"https://{environment_id}.local.davdeploy.example"
    status = "ACTIVE" if state in {"READY", "DEGRADED"} else "FAILED"
    primary_output, primary_resource = fixture_primary_resource(environment_id, profile, status)
    return {
        "environment_id": environment_id,
        "profile": profile,
        "state": state,
        "fixture": "bounded-embedded-executor",
        "health_checked": not should_fail,
        "degradation_detected": should_degrade,
        "outputs": [
            {
                "name": "application_url",
                "type": "https_url",
                "value": app_url,
                "visibility": "customer",
                "sensitive": False,
                "source": "fixture-observer",
                "status": status,
            },
            primary_output,
        ],
        "resources": [primary_resource],
    }


class FixtureExecutor:
    """Only calls a fixed local fixture API. It has no cloud, shell, or Docker authority."""

    def __init__(self, url: str | None = None):
        self.url = url or os.getenv("DAVDEPLOY_EXECUTOR_URL", "http://fixture-executor:8090")

    def deploy(
        self,
        environment_id: str,
        profile: str,
        should_fail: bool = False,
        should_degrade: bool = False,
    ) -> ExecutionObservation:
        response = httpx.post(
            f"{self.url}/deployments",
            json={
                "environment_id": environment_id,
                "profile": profile,
                "should_fail": should_fail,
                "should_degrade": should_degrade,
            },
            timeout=5,
        )
        response.raise_for_status()
        body = response.json()
        return ExecutionObservation(body["state"], body)

    def destroy(self, environment_id: str) -> ExecutionObservation:
        response = httpx.delete(f"{self.url}/deployments/{environment_id}", timeout=5)
        response.raise_for_status()
        body = response.json()
        return ExecutionObservation(body["state"], body)

    def change(self, environment_id: str, minimum_replicas: int) -> ExecutionObservation:
        response = httpx.post(
            f"{self.url}/changes",
            json={"environment_id": environment_id, "minimum_replicas": minimum_replicas},
            timeout=5,
        )
        response.raise_for_status()
        body = response.json()
        return ExecutionObservation(body["state"], body)


class EmbeddedFixtureExecutor:
    """Runs deterministic dry-run observations without network or cloud authority."""

    def deploy(
        self,
        environment_id: str,
        profile: str,
        should_fail: bool = False,
        should_degrade: bool = False,
    ) -> ExecutionObservation:
        detail = fixture_deployment(
            environment_id,
            profile,
            should_fail=should_fail,
            should_degrade=should_degrade,
        )
        return ExecutionObservation(detail["state"], detail)

    def destroy(self, environment_id: str) -> ExecutionObservation:
        detail = {
            "environment_id": environment_id,
            "state": "DESTROYED",
            "fixture": "bounded-embedded-executor",
            "cleanup_verified": True,
            "outputs": [],
            "resources": [],
        }
        return ExecutionObservation("DESTROYED", detail)

    def change(self, environment_id: str, minimum_replicas: int) -> ExecutionObservation:
        detail = {
            "environment_id": environment_id,
            "state": "READY",
            "fixture": "bounded-embedded-executor",
            "minimum_replicas": minimum_replicas,
            "health_checked": True,
            "p95_latency_ms": 1500,
            "queue_time_ms": 300,
        }
        return ExecutionObservation("READY", detail)


def configured_executor() -> ExecutionAdapter:
    mode = os.getenv("DAVDEPLOY_EXECUTOR_MODE", "http_fixture")
    if mode == "http_fixture":
        return FixtureExecutor()
    if mode == "embedded_fixture":
        return EmbeddedFixtureExecutor()
    raise RuntimeError(f"unsupported executor mode: {mode}")
