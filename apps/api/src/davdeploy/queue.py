"""Replaceable durable job queue boundary.

PostgreSQL is the local/early-hosted transport. The contract is intentionally
small so SQS/EventBridge or a workflow service can be introduced later without
changing job semantics.
"""

from __future__ import annotations

from collections.abc import Iterable
from datetime import UTC, datetime, timedelta
from typing import Protocol

from sqlalchemy.orm import Session

from davdeploy.contracts import JobEnvelope, JobKind
from davdeploy.models import PlatformJob


class JobQueue(Protocol):
    def enqueue(self, job: JobEnvelope) -> JobEnvelope: ...

    def claim(self, tenant_organization_id: str, kinds: Iterable[JobKind] | None = None) -> JobEnvelope | None: ...

    def heartbeat(self, job_id: str) -> None: ...

    def retry(self, job_id: str, error: str) -> str: ...

    def cancel(self, job_id: str, reason: str = "cancelled") -> None: ...

    def dead_letter(self, job_id: str, error: str) -> None: ...

    def requeue_stale(self, timeout_seconds: int) -> int: ...

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

    def heartbeat(self, job_id: str) -> None:
        row = self.db.get(PlatformJob, job_id)
        if row is None:
            raise KeyError(f"unknown platform job: {job_id}")
        if row.state != "RUNNING":
            raise ValueError("only running jobs can heartbeat")
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

    def retry(self, job_id: str, error: str) -> str:
        return self.fail(job_id, error, retry=True)

    def cancel(self, job_id: str, reason: str = "cancelled") -> None:
        row = self.db.get(PlatformJob, job_id)
        if row is None:
            raise KeyError(f"unknown platform job: {job_id}")
        row.error = reason[:2_000]
        row.state = "CANCELLED"
        row.updated_at = datetime.now(UTC)
        self.db.commit()

    def dead_letter(self, job_id: str, error: str) -> None:
        row = self.db.get(PlatformJob, job_id)
        if row is None:
            raise KeyError(f"unknown platform job: {job_id}")
        row.error = error[:2_000]
        row.state = "DEAD_LETTER"
        row.updated_at = datetime.now(UTC)
        self.db.commit()

    def requeue_stale(self, timeout_seconds: int) -> int:
        cutoff = datetime.now(UTC) - timedelta(seconds=timeout_seconds)
        rows = self.db.query(PlatformJob).filter(PlatformJob.state == "RUNNING", PlatformJob.updated_at < cutoff).all()
        for row in rows:
            row.state = "QUEUED"
            row.updated_at = datetime.now(UTC)
        self.db.commit()
        return len(rows)

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
        self.claimed_at: dict[str, datetime] = {}

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
                self.claimed_at[job.job_id] = datetime.now(UTC)
                return updated
        return None

    def acknowledge(self, job_id: str) -> None:
        job, _ = self.jobs[job_id]
        self.jobs[job_id] = (job, "SUCCEEDED")

    def heartbeat(self, job_id: str) -> None:
        job, state = self.jobs[job_id]
        if state != "RUNNING":
            raise ValueError("only running jobs can heartbeat")
        self.jobs[job_id] = (job, state)

    def fail(self, job_id: str, error: str, *, retry: bool = True) -> str:
        job, _ = self.jobs[job_id]
        state = "QUEUED" if retry and job.attempt < job.max_attempts else "DEAD_LETTER"
        self.jobs[job_id] = (job, state)
        return state

    def retry(self, job_id: str, error: str) -> str:
        return self.fail(job_id, error, retry=True)

    def cancel(self, job_id: str, reason: str = "cancelled") -> None:
        job, _ = self.jobs[job_id]
        self.jobs[job_id] = (job, "CANCELLED")

    def dead_letter(self, job_id: str, error: str) -> None:
        job, _ = self.jobs[job_id]
        self.jobs[job_id] = (job, "DEAD_LETTER")

    def requeue_stale(self, timeout_seconds: int) -> int:
        cutoff = datetime.now(UTC) - timedelta(seconds=timeout_seconds)
        count = 0
        for job_id, (job, state) in list(self.jobs.items()):
            if state == "RUNNING" and self.claimed_at.get(job_id, datetime.now(UTC)) < cutoff:
                self.jobs[job_id] = (job, "QUEUED")
                count += 1
        return count
