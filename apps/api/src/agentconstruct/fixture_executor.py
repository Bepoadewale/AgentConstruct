from __future__ import annotations

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="AgentConstruct bounded local execution fixture")
deployments: dict[str, dict] = {}


class DeployRequest(BaseModel):
    environment_id: str
    profile: str
    should_fail: bool = False
    should_degrade: bool = False


class ChangeRequest(BaseModel):
    environment_id: str
    minimum_replicas: int


@app.get("/healthz")
def healthz():
    return {"status": "ok"}


@app.post("/deployments")
def deploy(request: DeployRequest):
    state = "FAILED" if request.should_fail else "DEGRADED" if request.should_degrade else "READY"
    deployments[request.environment_id] = {
        "environment_id": request.environment_id,
        "profile": request.profile,
        "state": state,
        "fixture": "bounded-local-executor",
        "health_checked": not request.should_fail,
        "degradation_detected": request.should_degrade,
    }
    return deployments[request.environment_id]


@app.delete("/deployments/{environment_id}")
def destroy(environment_id: str):
    if environment_id not in deployments:
        raise HTTPException(404, "fixture deployment missing")
    deployments.pop(environment_id)
    return {
        "environment_id": environment_id,
        "state": "DESTROYED",
        "fixture": "bounded-local-executor",
        "cleanup_verified": True,
    }


@app.post("/changes")
def change(request: ChangeRequest):
    if request.environment_id not in deployments:
        raise HTTPException(404, "fixture deployment missing")
    deployments[request.environment_id].update(
        {
            "state": "READY",
            "fixture": "bounded-local-executor",
            "minimum_replicas": request.minimum_replicas,
            "health_checked": True,
            "p95_latency_ms": 1500,
            "queue_time_ms": 300,
        }
    )
    return deployments[request.environment_id]
