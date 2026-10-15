import pytest
from agentconstruct.contracts import JobEnvelope, JobKind, ModelPurpose, ModelRequest, TenantScope
from agentconstruct.db import run_migrations
from agentconstruct.model_gateway import (
    DeterministicModelGateway,
    DisabledModelGateway,
    ModelCallPolicy,
    ModelGatewayUnavailable,
    guarded_complete,
)
from agentconstruct.models import Base
from agentconstruct.queue import InMemoryJobQueue, PostgresJobQueue
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


def tenant(org="org-demo"):
    return TenantScope(
        organization_id=org,
        workspace_id="workspace-demo",
        project_id="project-demo",
        actor_id="user-demo",
    )


def job(key="planning-123", org="org-demo"):
    return JobEnvelope(tenant=tenant(org), kind=JobKind.PLANNING, idempotency_key=key)


def test_in_memory_queue_is_idempotent_and_retries_then_dead_letters():
    queue = InMemoryJobQueue()
    first = queue.enqueue(job())
    duplicate = queue.enqueue(job())
    assert duplicate.job_id == first.job_id
    claimed = queue.claim("org-demo")
    assert claimed is not None and claimed.attempt == 1
    assert queue.fail(claimed.job_id, "temporary") == "QUEUED"
    claimed_again = queue.claim("org-demo")
    assert claimed_again is not None and claimed_again.attempt == 2
    queue.heartbeat(claimed_again.job_id)
    queue.cancel(claimed_again.job_id, "operator requested cancellation")
    assert queue.fail(claimed_again.job_id, "permanent", retry=False) == "DEAD_LETTER"


def test_in_memory_queue_does_not_cross_tenants():
    queue = InMemoryJobQueue()
    queue.enqueue(job(org="org-a"))
    assert queue.claim("org-b") is None


def test_postgres_queue_persists_and_deduplicates_jobs():
    engine = create_engine("sqlite+pysqlite:///:memory:", connect_args={"check_same_thread": False})
    run_migrations(engine)
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, expire_on_commit=False)
    with session_factory() as db:
        queue = PostgresJobQueue(db)
        first = queue.enqueue(job())
        duplicate = queue.enqueue(job())
        assert duplicate.job_id == first.job_id
        claimed = queue.claim("org-demo", [JobKind.PLANNING])
        assert claimed is not None and claimed.attempt == 1
        assert queue.fail(claimed.job_id, "retryable") == "QUEUED"
        assert queue.claim("org-demo") is not None
        queue.heartbeat(claimed.job_id)
        queue.acknowledge(claimed.job_id)


def test_fixture_model_gateway_returns_typed_non_authoritative_response():
    request = ModelRequest(
        tenant=tenant(),
        purpose=ModelPurpose.INTENT_EXTRACTION,
        provider="fixture",
        model="deterministic-fixture",
        prompt_version="intent-v1",
        input_digest="a" * 64,
    )
    response = DeterministicModelGateway().complete(request, {"prompt": "deploy api"})
    assert response.output["mode"] == "SIMULATED"
    assert response.evidence[0].kind.value == "fixture"
    assert response.usage is not None


def test_disabled_model_gateway_fails_closed():
    try:
        DisabledModelGateway().complete(None, {})  # type: ignore[arg-type]
    except ModelGatewayUnavailable as error:
        assert "configured" in str(error)
    else:
        raise AssertionError("disabled model gateway returned a response")


def test_model_call_policy_enforces_provider_and_budget():
    request = ModelRequest(
        tenant=tenant(),
        purpose=ModelPurpose.INTENT_EXTRACTION,
        provider="fixture",
        model="deterministic-fixture",
        prompt_version="intent-v1",
        input_digest="a" * 64,
        max_output_tokens=100,
    )
    response = guarded_complete(DeterministicModelGateway(), request, {"prompt": "ok"}, ModelCallPolicy(max_output_tokens=100))
    assert response.request.request_id == request.request_id
    with pytest.raises(ModelGatewayUnavailable):
        guarded_complete(DeterministicModelGateway(), request.model_copy(update={"provider": "unknown"}), {"prompt": "no"})
