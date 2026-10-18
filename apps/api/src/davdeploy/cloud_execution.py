"""Narrow, explicitly gated cloud execution boundary.

The product never accepts arbitrary commands. The App Runner adapter invokes one
checked-in script with a fixed operation allowlist and bounded timeouts.
"""

from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol


@dataclass(frozen=True)
class CloudExecutionResult:
    state: str
    operations: tuple[dict[str, object], ...]
    outputs: dict[str, object]
    failure_reason: str | None = None


class CloudExecutionAdapter(Protocol):
    def execute(self, context: dict[str, object]) -> CloudExecutionResult: ...


class DisabledCloudExecutionAdapter:
    def execute(self, context: dict[str, object]) -> CloudExecutionResult:
        del context
        return CloudExecutionResult(
            state="BLOCKED_CLOUD_EXECUTION_NOT_ENABLED",
            operations=(),
            outputs={},
            failure_reason="Cloud execution adapter is disabled for this process.",
        )


class AppRunnerCloudExecutionAdapter:
    """Run only the checked-in App Runner pilot script when explicitly enabled."""

    operations = ("plan", "apply-foundation", "build-push-image", "apply-service", "wait-ready", "smoke")

    def __init__(self, *, root: str | Path = ".", timeout_seconds: int = 1_800):
        self.root = Path(root)
        self.timeout_seconds = timeout_seconds

    def execute(self, context: dict[str, object]) -> CloudExecutionResult:
        if os.getenv("DAVDEPLOY_CLOUD_EXECUTION_COMMAND_ENABLED", "false").lower() != "true":
            return DisabledCloudExecutionAdapter().execute(context)
        script = self.root / "scripts" / "customer-workload-app-runner-pilot.sh"
        if not script.is_file():
            return CloudExecutionResult(
                state="FAILED",
                operations=(),
                outputs={},
                failure_reason="App Runner execution script is unavailable.",
            )
        environment = os.environ.copy()
        for key, value in (context.get("environment") or {}).items():
            if not isinstance(key, str) or not isinstance(value, str):
                continue
            environment[key] = value
        results: list[dict[str, object]] = []
        for operation in self.operations:
            try:
                completed = subprocess.run(
                    [str(script), operation],
                    cwd=self.root,
                    env=environment,
                    capture_output=True,
                    text=True,
                    timeout=self.timeout_seconds,
                    check=False,
                )
            except subprocess.TimeoutExpired:
                results.append({"operation": operation, "returncode": None, "state": "TIMEOUT"})
                return CloudExecutionResult(
                    state="FAILED",
                    operations=tuple(results),
                    outputs={},
                    failure_reason=f"App Runner operation {operation} exceeded its timeout.",
                )
            results.append(
                {
                    "operation": operation,
                    "returncode": completed.returncode,
                    "state": "SUCCEEDED" if completed.returncode == 0 else "FAILED",
                    "stdout": completed.stdout[-2000:],
                    "stderr": completed.stderr[-2000:],
                }
            )
            if completed.returncode != 0:
                return CloudExecutionResult(
                    state="FAILED",
                    operations=tuple(results),
                    outputs={},
                    failure_reason=f"App Runner operation {operation} failed.",
                )
        return CloudExecutionResult(
            state="READY",
            operations=tuple(results),
            outputs={"source": "app-runner-pilot-script", "observed": True},
        )


def configured_cloud_execution_adapter() -> CloudExecutionAdapter:
    if os.getenv("DAVDEPLOY_CLOUD_EXECUTION_COMMAND_ENABLED", "false").lower() == "true":
        return AppRunnerCloudExecutionAdapter()
    return DisabledCloudExecutionAdapter()
