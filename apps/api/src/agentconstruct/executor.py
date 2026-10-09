from __future__ import annotations

import os
from dataclasses import dataclass

import httpx


@dataclass(frozen=True)
class ExecutionObservation:
    state: str
    detail: dict


class FixtureExecutor:
    """Only calls a fixed local fixture API. It has no cloud, shell, or Docker authority."""

    def __init__(self, url: str | None = None):
        self.url = url or os.getenv("AGENTCONSTRUCT_EXECUTOR_URL", "http://fixture-executor:8090")

    def deploy(self, environment_id: str, should_fail: bool = False) -> ExecutionObservation:
        response = httpx.post(
            f"{self.url}/deployments",
            json={"environment_id": environment_id, "should_fail": should_fail},
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
