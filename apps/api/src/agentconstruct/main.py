from __future__ import annotations

import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Response
from fastapi.staticfiles import StaticFiles
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from prometheus_client import Counter, generate_latest
from sqlalchemy import select
from sqlalchemy.orm import Session

from agentconstruct.db import SessionLocal, run_migrations, session
from agentconstruct.domain import (
    ApprovalRequest,
    CloudConnectionRequest,
    CloudInventorySnapshotRequest,
    IntentRequest,
    LocalLoginRequest,
    ProjectRequest,
)
from agentconstruct.models import Environment
from agentconstruct.security import Principal, issue_local_token, verify_token
from agentconstruct.service import ProductService
from agentconstruct.telemetry import configure_tracing

REQUESTS = Counter("agentconstruct_api_requests_total", "API requests by route", ["route"])
PLAN_RESULTS = Counter("agentconstruct_plan_results_total", "Plans by policy outcome", ["outcome"])
EXECUTION_RESULTS = Counter(
    "agentconstruct_execution_results_total", "Observed execution results", ["state"]
)


@asynccontextmanager
async def lifespan(_: FastAPI):
    run_migrations()
    db = SessionLocal()
    try:
        ProductService(db).seed_local_identity()
    finally:
        db.close()
    yield


app = FastAPI(title="AgentConstruct", version="0.1.0", lifespan=lifespan)
configure_tracing()
FastAPIInstrumentor.instrument_app(app)


def product_service(db: Session = Depends(session)) -> ProductService:
    return ProductService(db)


def translate(error: Exception) -> None:
    if isinstance(error, PermissionError):
        raise HTTPException(403, str(error)) from error
    if isinstance(error, (ValueError, KeyError)):
        raise HTTPException(409, str(error)) from error
    raise error


@app.get("/healthz")
def healthz():
    return {"status": "ok", "product": "AgentConstruct"}


@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type="text/plain; version=0.0.4")


@app.post("/api/v1/auth/local-login")
def local_login(request: LocalLoginRequest):
    """Local fixture only. Production uses a trusted external OIDC issuer."""
    return {
        "access_token": issue_local_token(request.username),
        "token_type": "bearer",
        "expires_in": 1800,
    }


@app.post("/api/v1/projects", status_code=201)
def create_project(
    request: ProjectRequest,
    principal: Principal = Depends(verify_token),
    service: ProductService = Depends(product_service),
):
    REQUESTS.labels("projects.create").inc()
    try:
        project = service.create_project(
            principal, request.name, str(request.repository_url) if request.repository_url else None
        )
    except (PermissionError, ValueError, KeyError) as error:
        translate(error)
    return {"id": project.id, "name": project.name, "repository_url": project.repository_url}


@app.post("/api/v1/cloud-connections", status_code=201)
def create_cloud_connection(
    request: CloudConnectionRequest,
    principal: Principal = Depends(verify_token),
    service: ProductService = Depends(product_service),
):
    REQUESTS.labels("cloud_connections.create").inc()
    connection = service.create_cloud_connection(
        principal, request.display_name, request.provider, request.connection_mode
    )
    return {
        "id": connection.id,
        "display_name": connection.display_name,
        "provider": connection.provider,
        "mode": connection.connection_mode,
        "executed": False,
    }


@app.get("/api/v1/cloud-connections")
def list_cloud_connections(
    principal: Principal = Depends(verify_token), service: ProductService = Depends(product_service)
):
    REQUESTS.labels("cloud_connections.list").inc()
    return [
        {
            "id": item.id,
            "display_name": item.display_name,
            "provider": item.provider,
            "mode": item.connection_mode,
            "executed": False,
        }
        for item in service.cloud_connections(principal)
    ]


@app.get("/api/v1/cloud-connections/{connection_id}/role-contract")
def get_cloud_role_contract(
    connection_id: str,
    principal: Principal = Depends(verify_token),
    service: ProductService = Depends(product_service),
):
    REQUESTS.labels("cloud_connections.role_contract").inc()
    try:
        return service.cloud_role_contract(principal, connection_id)
    except (PermissionError, ValueError, KeyError) as error:
        translate(error)


@app.post("/api/v1/cloud-connections/{connection_id}/inventory-snapshots", status_code=201)
def record_cloud_inventory_snapshot(
    connection_id: str,
    request: CloudInventorySnapshotRequest,
    principal: Principal = Depends(verify_token),
    service: ProductService = Depends(product_service),
):
    REQUESTS.labels("cloud_inventory_snapshots.create").inc()
    try:
        stored = service.record_cloud_inventory_snapshot(
            principal,
            connection_id,
            request.region,
            request.provenance,
            request.captured_at,
            request.snapshot,
        )
    except (PermissionError, ValueError, KeyError) as error:
        translate(error)
    return {"id": stored.id, "connection_id": stored.cloud_connection_id, "captured_at": stored.captured_at}


@app.get("/api/v1/cloud-connections/{connection_id}/inventory-snapshots")
def list_cloud_inventory_snapshots(
    connection_id: str,
    principal: Principal = Depends(verify_token),
    service: ProductService = Depends(product_service),
):
    REQUESTS.labels("cloud_inventory_snapshots.list").inc()
    try:
        snapshots = service.cloud_inventory_snapshots(principal, connection_id)
    except (PermissionError, ValueError, KeyError) as error:
        translate(error)
    return [
        {
            "id": snapshot.id,
            "connection_id": snapshot.cloud_connection_id,
            "region": snapshot.region,
            "provenance": snapshot.provenance,
            "captured_at": snapshot.captured_at,
            "snapshot": snapshot.snapshot,
        }
        for snapshot in snapshots
    ]


@app.get("/api/v1/projects/{project_id}/repository-discovery")
def get_repository_discovery(
    project_id: str,
    principal: Principal = Depends(verify_token),
    service: ProductService = Depends(product_service),
):
    REQUESTS.labels("repositories.discovery").inc()
    try:
        return service.repository_discovery(principal, project_id)
    except (PermissionError, ValueError, KeyError) as error:
        translate(error)


@app.post("/api/v1/projects/{project_id}/desired-state-publications/{plan_id}")
def create_desired_state_publication(
    project_id: str,
    plan_id: str,
    principal: Principal = Depends(verify_token),
    service: ProductService = Depends(product_service),
):
    REQUESTS.labels("gitops.desired_state_contract").inc()
    try:
        return service.desired_state_publication(principal, project_id, plan_id)
    except (PermissionError, ValueError, KeyError) as error:
        translate(error)


@app.post("/api/v1/intents", status_code=201)
def create_intent(
    request: IntentRequest,
    principal: Principal = Depends(verify_token),
    service: ProductService = Depends(product_service),
):
    REQUESTS.labels("intents.create").inc()
    try:
        intent = service.create_intent(
            principal,
            request.project_id,
            request.prompt,
            request.source_repository,
            request.cloud_connection_id,
            request.idempotency_key,
        )
    except (PermissionError, ValueError, KeyError) as error:
        translate(error)
    return {"id": intent.id, "state": intent.state, "spec": intent.spec}


@app.post("/api/v1/intents/{intent_id}/plans", status_code=201)
def create_plan(
    intent_id: str,
    principal: Principal = Depends(verify_token),
    service: ProductService = Depends(product_service),
):
    REQUESTS.labels("plans.create").inc()
    try:
        plan = service.plan_intent(principal, intent_id)
    except (PermissionError, ValueError, KeyError) as error:
        translate(error)
    PLAN_RESULTS.labels(plan.policy_result).inc()
    return {
        "id": plan.id,
        "state": plan.state,
        "plan_hash": plan.plan_hash,
        "policy_result": plan.policy_result,
        "payload": plan.payload,
    }


@app.post("/api/v1/deployment-plans/{plan_id}/approve")
def approve_plan(
    plan_id: str,
    request: ApprovalRequest,
    principal: Principal = Depends(verify_token),
    service: ProductService = Depends(product_service),
):
    REQUESTS.labels("plans.approve").inc()
    try:
        plan = service.approve(principal, plan_id, request.plan_hash)
    except (PermissionError, ValueError, KeyError) as error:
        translate(error)
    return {"id": plan.id, "state": plan.state, "plan_hash": plan.plan_hash}


@app.get("/api/v1/deployment-plans/{plan_id}")
def get_plan(
    plan_id: str,
    principal: Principal = Depends(verify_token),
    service: ProductService = Depends(product_service),
):
    REQUESTS.labels("plans.get").inc()
    try:
        plan = service.get_plan(principal, plan_id)
    except (PermissionError, ValueError, KeyError) as error:
        translate(error)
    return {
        "id": plan.id,
        "state": plan.state,
        "plan_hash": plan.plan_hash,
        "policy_result": plan.policy_result,
        "action": plan.action,
        "payload": plan.payload,
    }


@app.post("/api/v1/deployment-plans/{plan_id}/execute")
def execute_plan(
    plan_id: str,
    principal: Principal = Depends(verify_token),
    service: ProductService = Depends(product_service),
):
    REQUESTS.labels("plans.execute").inc()
    try:
        environments = service.execute(principal, plan_id)
    except (PermissionError, ValueError, KeyError) as error:
        translate(error)
    for environment in environments:
        EXECUTION_RESULTS.labels(environment.state).inc()
    return {
        "environments": [
            {
                "id": item.id,
                "state": item.state,
                "type": item.environment_type,
                "observed_state": item.observed_state,
            }
            for item in environments
        ]
    }


@app.get("/api/v1/environments")
def list_environments(principal: Principal = Depends(verify_token), db: Session = Depends(session)):
    REQUESTS.labels("environments.list").inc()
    items = db.scalars(
        select(Environment).where(Environment.organization_id == principal.organization_id)
    ).all()
    return [
        {
            "id": item.id,
            "name": item.name,
            "type": item.environment_type,
            "state": item.state,
            "observed_state": item.observed_state,
        }
        for item in items
    ]


@app.get("/api/v1/environments/{environment_id}")
def get_environment(
    environment_id: str,
    principal: Principal = Depends(verify_token),
    service: ProductService = Depends(product_service),
):
    REQUESTS.labels("environments.get").inc()
    try:
        item = service.get_environment(principal, environment_id)
    except (PermissionError, ValueError, KeyError) as error:
        translate(error)
    return {
        "id": item.id,
        "name": item.name,
        "type": item.environment_type,
        "state": item.state,
        "desired_state": item.desired_state,
        "observed_state": item.observed_state,
    }


@app.get("/api/v1/environments/{environment_id}/recommendation")
def get_recommendation(
    environment_id: str,
    principal: Principal = Depends(verify_token),
    service: ProductService = Depends(product_service),
):
    REQUESTS.labels("day2.recommendation").inc()
    try:
        return service.recommendation(principal, environment_id)
    except (PermissionError, ValueError, KeyError) as error:
        translate(error)


@app.get("/api/v1/environments/{environment_id}/incidents")
def get_incidents(
    environment_id: str,
    principal: Principal = Depends(verify_token),
    service: ProductService = Depends(product_service),
):
    REQUESTS.labels("incidents.list").inc()
    try:
        return [
            {
                "id": incident.id,
                "state": incident.state,
                "summary": incident.summary,
                "evidence": incident.evidence,
                "at": incident.created_at,
            }
            for incident in service.incidents(principal, environment_id)
        ]
    except (PermissionError, ValueError, KeyError) as error:
        translate(error)


@app.post("/api/v1/environments/{environment_id}/change-plan", status_code=201)
def create_change_plan(
    environment_id: str,
    principal: Principal = Depends(verify_token),
    service: ProductService = Depends(product_service),
):
    REQUESTS.labels("day2.change_plan").inc()
    try:
        plan = service.change_plan(principal, environment_id)
    except (PermissionError, ValueError, KeyError) as error:
        translate(error)
    PLAN_RESULTS.labels(plan.policy_result).inc()
    return {
        "id": plan.id,
        "state": plan.state,
        "plan_hash": plan.plan_hash,
        "policy_result": plan.policy_result,
        "action": plan.action,
        "payload": plan.payload,
    }


@app.post("/api/v1/environments/{environment_id}/destroy-plan", status_code=201)
def create_destroy_plan(
    environment_id: str,
    principal: Principal = Depends(verify_token),
    service: ProductService = Depends(product_service),
):
    REQUESTS.labels("destroy.plan").inc()
    try:
        plan = service.destroy_plan(principal, environment_id)
    except (PermissionError, ValueError, KeyError) as error:
        translate(error)
    return {
        "id": plan.id,
        "state": plan.state,
        "plan_hash": plan.plan_hash,
        "policy_result": plan.policy_result,
    }


@app.get("/api/v1/audit-events")
def audit_events(
    environment_id: str | None = None,
    principal: Principal = Depends(verify_token),
    service: ProductService = Depends(product_service),
):
    REQUESTS.labels("audit.list").inc()
    return [
        {
            "action": item.action,
            "entity_type": item.entity_type,
            "entity_id": item.entity_id,
            "detail": item.detail,
            "at": item.created_at,
        }
        for item in service.audits(principal, environment_id)
    ]


web_root = Path(os.getenv("AGENTCONSTRUCT_WEB_ROOT", str(Path(__file__).parents[3] / "web")))
app.mount("/", StaticFiles(directory=web_root, html=True), name="web")
