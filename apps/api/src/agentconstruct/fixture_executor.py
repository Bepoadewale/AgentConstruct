from __future__ import annotations

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="AgentConstruct bounded local execution fixture")
deployments: dict[str, dict] = {}


class DeployRequest(BaseModel):
    environment_id: str
    should_fail: bool = False


@app.get("/healthz")
def healthz():
    return {"status": "ok"}


@app.post("/deployments")
def deploy(request: DeployRequest):
    state = "FAILED" if request.should_fail else "READY"
    deployments[request.environment_id] = {
        "environment_id": request.environment_id,
        "state": state,
        "fixture": "bounded-local-executor",
        "health_checked": not request.should_fail,
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
