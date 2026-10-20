from __future__ import annotations

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from davdeploy.executor import fixture_primary_resource

app = FastAPI(title="davdeploy bounded local execution fixture")
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
    app_url = f"https://{request.environment_id}.local.davdeploy.example"
    status = "ACTIVE" if state in {"READY", "DEGRADED"} else "FAILED"
    primary_output, primary_resource = fixture_primary_resource(
        request.environment_id, request.profile, status
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
                "status": status,
            },
            primary_output,
            {
                "name": "log_group",
                "type": "log_group",
                "value": f"/aws/apprunner/local-{request.profile}/{request.environment_id}",
                "visibility": "customer",
                "sensitive": False,
                "source": "fixture-observer",
                "status": status,
            },
            {
                "name": "grafana_dashboard",
                "type": "dashboard_url",
                "value": "http://localhost:3000/d/davdeploy-local",
                "visibility": "customer",
                "sensitive": False,
                "source": "fixture-observer",
                "status": status,
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
            primary_resource,
            {
                "provider": "aws",
                "resource_type": "logs_log_group",
                "name": f"/aws/apprunner/local-{request.profile}/{request.environment_id}",
                "external_id": None,
                "region": "us-east-1",
                "status": status,
                "tags": {
                    "davdeploy:environment-id": request.environment_id,
                    "davdeploy:execution-mode": "LOCAL_DRY_RUN",
                },
            },
            {
                "provider": "davdeploy",
                "resource_type": "grafana_dashboard",
                "name": "davdeploy-local",
                "external_id": "http://localhost:3000/d/davdeploy-local",
                "region": None,
                "status": status,
                "tags": {
                    "davdeploy:environment-id": request.environment_id,
                    "davdeploy:execution-mode": "LOCAL_DRY_RUN",
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
