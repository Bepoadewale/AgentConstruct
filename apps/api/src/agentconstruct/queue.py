"""Replaceable durable job queue boundary.

PostgreSQL is the local/early-hosted transport. The contract is intentionally
small so SQS/EventBridge or a workflow service can be introduced later without
changing job semantics.
"""

from __future__ import annotations

from collections.abc import Iterable
from datetime import UTC, datetime
from typing import Protocol

from sqlalchemy.orm import Session

from agentconstruct.contracts import JobEnvelope, JobKind
from agentconstruct.models import PlatformJob


class JobQueue(Protocol):
    def enqueue(self, job: JobEnvelope) -> JobEnvelope: ...

    def claim(self, tenant_organization_id: str, kinds: Iterable[JobKind] | None = None) -> JobEnvelope | None: ...

    def acknowledge(self, job_id: str) -> None: ...

    def fail(self, job_id: str, error: str, *, retry: bool = True) -> str: ...


class PostgresJobQueue:
    """Durable queue adapter for local and early hosted operation."""

    def __init__(self, db: Session):
        self.db = db

    def enqueue(self, job: JobEnvelope) -> JobEnvelope:
        existing = (
            self.db.query(PlatformJob)
            .filter(
                PlatformJob.organization_id == job.tenant.organization_id,
                PlatformJob.idempotency_key == job.idempotency_key,
            )
            .one_or_none()
        )
        if existing:
            return self._envelope(existing)
        row = PlatformJob(
            id=job.job_id,
            organization_id=job.tenant.organization_id,
            workspace_id=job.tenant.workspace_id,
            kind=job.kind.value,
            idempotency_key=job.idempotency_key,
            state="QUEUED",
            envelope=job.model_dump(mode="json"),
            attempt=job.attempt,
            max_attempts=job.max_attempts,
            timeout_seconds=job.timeout_seconds,
            trace_id=job.trace_id,
        )
        self.db.add(row)
        self.db.commit()
        return job

    def claim(
        self, tenant_organization_id: str, kinds: Iterable[JobKind] | None = None
    ) -> JobEnvelope | None:
        query = (
            self.db.query(PlatformJob)
            .filter(
                PlatformJob.organization_id == tenant_organization_id,
                PlatformJob.state == "QUEUED",
            )
            .order_by(PlatformJob.created_at.asc())
        )
        if kinds:
            query = query.filter(PlatformJob.kind.in_([kind.value for kind in kinds]))
        row = query.first()
        if row is None:
            return None
        row.state = "RUNNING"
        row.attempt += 1
        row.updated_at = datetime.now(UTC)
        self.db.commit()
        return self._envelope(row)

    def acknowledge(self, job_id: str) -> None:
        row = self.db.get(PlatformJob, job_id)
        if row is None:
            raise KeyError(f"unknown platform job: {job_id}")
        row.state = "SUCCEEDED"
        row.updated_at = datetime.now(UTC)
        self.db.commit()

    def fail(self, job_id: str, error: str, *, retry: bool = True) -> str:
        row = self.db.get(PlatformJob, job_id)
        if row is None:
            raise KeyError(f"unknown platform job: {job_id}")
        row.error = error[:2_000]
        row.state = "QUEUED" if retry and row.attempt < row.max_attempts else "DEAD_LETTER"
        row.updated_at = datetime.now(UTC)
        self.db.commit()
        return row.state

    @staticmethod
    def _envelope(row: PlatformJob) -> JobEnvelope:
        payload = dict(row.envelope)
        payload["attempt"] = row.attempt
        return JobEnvelope.model_validate(payload)


class InMemoryJobQueue:
    """Deterministic adapter for unit tests; it has no process durability."""

    def __init__(self):
        self.jobs: dict[str, tuple[JobEnvelope, str]] = {}
        self.idempotency: dict[tuple[str, str], str] = {}

    def enqueue(self, job: JobEnvelope) -> JobEnvelope:
        key = (job.tenant.organization_id, job.idempotency_key)
        existing_id = self.idempotency.get(key)
        if existing_id:
            return self.jobs[existing_id][0]
        self.jobs[job.job_id] = (job, "QUEUED")
        self.idempotency[key] = job.job_id
        return job

    def claim(
        self, tenant_organization_id: str, kinds: Iterable[JobKind] | None = None
    ) -> JobEnvelope | None:
        allowed = {kind.value for kind in kinds} if kinds else None
        for job, state in self.jobs.values():
            if (
                state == "QUEUED"
                and job.tenant.organization_id == tenant_organization_id
                and (allowed is None or job.kind.value in allowed)
            ):
                updated = job.model_copy(update={"attempt": job.attempt + 1})
                self.jobs[job.job_id] = (updated, "RUNNING")
                return updated
        return None

    def acknowledge(self, job_id: str) -> None:
        job, _ = self.jobs[job_id]
        self.jobs[job_id] = (job, "SUCCEEDED")

    def fail(self, job_id: str, error: str, *, retry: bool = True) -> str:
        job, _ = self.jobs[job_id]
        state = "QUEUED" if retry and job.attempt < job.max_attempts else "DEAD_LETTER"
        self.jobs[job_id] = (job, state)
        return state

