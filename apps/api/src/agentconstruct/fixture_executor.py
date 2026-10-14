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
    app_url = f"https://{request.environment_id}.local.agentconstruct.example"
    service_arn = (
        "arn:aws:apprunner:us-east-1:000000000000:"
        f"service/local-{request.profile}/{request.environment_id}"
    )
    deployments[request.environment_id] = {
        "environment_id": request.environment_id,
        "profile": request.profile,
        "state": state,
        "fixture": "bounded-local-executor",
        "health_checked": not request.should_fail,
        "degradation_detected": request.should_degrade,
        "outputs": [
            {
                "name": "application_url",
                "type": "https_url",
                "value": app_url,
                "visibility": "customer",
                "sensitive": False,
                "source": "fixture-observer",
                "status": "ACTIVE" if state in {"READY", "DEGRADED"} else "FAILED",
            },
            {
                "name": "app_runner_service_arn",
                "type": "aws_arn",
                "value": service_arn,
                "visibility": "customer",
                "sensitive": False,
                "source": "fixture-observer",
                "status": "ACTIVE" if state in {"READY", "DEGRADED"} else "FAILED",
            },
            {
                "name": "log_group",
                "type": "log_group",
                "value": f"/aws/apprunner/local-{request.profile}/{request.environment_id}",
                "visibility": "customer",
                "sensitive": False,
                "source": "fixture-observer",
                "status": "ACTIVE" if state in {"READY", "DEGRADED"} else "FAILED",
            },
            {
                "name": "grafana_dashboard",
                "type": "dashboard_url",
                "value": "http://localhost:3000/d/agentconstruct-local",
                "visibility": "customer",
                "sensitive": False,
                "source": "fixture-observer",
                "status": "ACTIVE" if state in {"READY", "DEGRADED"} else "FAILED",
            },
            {
                "name": "database_endpoint",
                "type": "secret_reference",
                "value": "not-created-for-this-local-dry-run",
                "visibility": "customer",
                "sensitive": False,
                "source": "fixture-observer",
                "status": "NOT_APPLICABLE",
            },
        ],
        "resources": [
            {
                "provider": "aws",
                "resource_type": "apprunner_service",
                "name": f"local-{request.profile}",
                "external_id": service_arn,
                "region": "us-east-1",
                "status": "ACTIVE" if state in {"READY", "DEGRADED"} else "FAILED",
                "tags": {
                    "agentconstruct:environment-id": request.environment_id,
                    "agentconstruct:execution-mode": "LOCAL_DRY_RUN",
                },
            },
            {
                "provider": "aws",
                "resource_type": "logs_log_group",
                "name": f"/aws/apprunner/local-{request.profile}/{request.environment_id}",
                "external_id": None,
                "region": "us-east-1",
                "status": "ACTIVE" if state in {"READY", "DEGRADED"} else "FAILED",
                "tags": {
                    "agentconstruct:environment-id": request.environment_id,
                    "agentconstruct:execution-mode": "LOCAL_DRY_RUN",
                },
            },
            {
                "provider": "agentconstruct",
                "resource_type": "grafana_dashboard",
                "name": "agentconstruct-local",
                "external_id": "http://localhost:3000/d/agentconstruct-local",
                "region": None,
                "status": "ACTIVE" if state in {"READY", "DEGRADED"} else "FAILED",
                "tags": {
                    "agentconstruct:environment-id": request.environment_id,
                    "agentconstruct:execution-mode": "LOCAL_DRY_RUN",
                },
            },
        ],
    }
    return deployments[request.environment_id]


@app.delete("/deployments/{environment_id}")
def destroy(environment_id: str):
    if environment_id not in deployments:
        raise HTTPException(404, "fixture deployment missing")
    previous = deployments.pop(environment_id)
    return {
        "environment_id": environment_id,
        "state": "DESTROYED",
        "fixture": "bounded-local-executor",
        "cleanup_verified": True,
        "outputs": [
            {**output, "status": "DESTROYED"} for output in previous.get("outputs", [])
        ],
        "resources": [
            {**resource, "status": "DESTROYED"} for resource in previous.get("resources", [])
        ],
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
