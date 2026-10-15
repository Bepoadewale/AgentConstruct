"""Durable local adapters and correctness probes for pre-cloud hardening.

The adapters intentionally use SQLite/std-lib primitives so the same contracts can
later be backed by a hosted store without changing callers.
"""

from __future__ import annotations

import json
import sqlite3
import threading
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from agentconstruct.boundaries import TenantBoundaryError, TenantContext, require_same_tenant
from agentconstruct.contracts import (
    DomainContractV1,
    Entitlement,
    TenantScope,
    UsageDecision,
    UsageEvent,
)


class BackupManifest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    backup_id: str = Field(min_length=1, max_length=160)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    record_count: int = Field(ge=0)
    content_digest: str = Field(min_length=1, max_length=128)


class LocalRecordStore:
    """Tenant-scoped durable record store for local correctness and recovery tests."""

    def __init__(self, path: str | Path = ":memory:") -> None:
        self.path = str(path)
        self._lock = threading.RLock()
        self._db = sqlite3.connect(self.path, check_same_thread=False)
        self._db.execute("PRAGMA journal_mode=WAL")
        self._db.execute(
            "CREATE TABLE IF NOT EXISTS records (record_id TEXT PRIMARY KEY, organization_id TEXT NOT NULL, workspace_id TEXT NOT NULL, project_id TEXT, kind TEXT NOT NULL, payload TEXT NOT NULL, archived INTEGER NOT NULL DEFAULT 0, deleted INTEGER NOT NULL DEFAULT 0, created_at TEXT NOT NULL)"
        )
        self._db.commit()

    def put(self, record_id: str, record: DomainContractV1) -> None:
        payload = json.dumps(record.model_dump(mode="json"), sort_keys=True)
        with self._lock:
            self._db.execute(
                "INSERT OR REPLACE INTO records(record_id, organization_id, workspace_id, project_id, kind, payload, archived, deleted, created_at) VALUES(?,?,?,?,?,?,0,0,?)",
                (record_id, record.tenant.organization_id, record.tenant.workspace_id, record.project_id, record.contract_type, payload, record.created_at.isoformat()),
            )
            self._db.commit()

    def get(self, record_id: str, context: TenantContext) -> dict[str, Any]:
        with self._lock:
            row = self._db.execute("SELECT organization_id, workspace_id, project_id, payload, deleted FROM records WHERE record_id=?", (record_id,)).fetchone()
        if row is None or row[4]:
            raise KeyError(record_id)
        scope = TenantScope(organization_id=row[0], workspace_id=row[1], project_id=row[2], actor_id=context.actor_id)
        require_same_tenant(context, scope)
        return json.loads(row[3])

    def export(self, context: TenantContext) -> list[dict[str, Any]]:
        with self._lock:
            rows = self._db.execute("SELECT payload FROM records WHERE organization_id=? AND workspace_id=? AND deleted=0", (context.organization_id, context.workspace_id)).fetchall()
        return [json.loads(row[0]) for row in rows]

    def soft_delete_project(self, context: TenantContext, project_id: str) -> int:
        if context.project_id and context.project_id != project_id:
            raise TenantBoundaryError("project scope mismatch")
        with self._lock:
            cur = self._db.execute("UPDATE records SET deleted=1 WHERE organization_id=? AND workspace_id=? AND project_id=?", (context.organization_id, context.workspace_id, project_id))
            self._db.commit()
            return cur.rowcount

    def archive_before(self, context: TenantContext, cutoff: datetime) -> int:
        with self._lock:
            cur = self._db.execute("UPDATE records SET archived=1 WHERE organization_id=? AND workspace_id=? AND created_at<?", (context.organization_id, context.workspace_id, cutoff.isoformat()))
            self._db.commit()
            return cur.rowcount

    def backup(self, context: TenantContext, backup_id: str) -> tuple[BackupManifest, str]:
        with self._lock:
            rows = self._db.execute("SELECT record_id, payload FROM records WHERE organization_id=? AND workspace_id=? AND deleted=0", (context.organization_id, context.workspace_id)).fetchall()
        payload = json.dumps({"records": [{"record_id": row[0], "payload": json.loads(row[1])} for row in rows]}, sort_keys=True)
        import hashlib
        digest = hashlib.sha256(payload.encode()).hexdigest()
        return BackupManifest(backup_id=backup_id, record_count=len(rows), content_digest=digest), payload

    def restore(self, context: TenantContext, payload: str) -> int:
        restored = 0
        for item in json.loads(payload).get("records", []):
            record = item["payload"]
            scope = TenantScope(**record["tenant"])
            require_same_tenant(context, scope)
            with self._lock:
                self._db.execute(
                    "INSERT OR REPLACE INTO records(record_id, organization_id, workspace_id, project_id, kind, payload, archived, deleted, created_at) VALUES(?,?,?,?,?,?,0,0,?)",
                    (item["record_id"], scope.organization_id, scope.workspace_id, record.get("project_id"), record.get("contract_type", "unknown"), json.dumps(record, sort_keys=True), record.get("created_at", datetime.now(UTC).isoformat())),
                )
                restored += 1
        with self._lock:
            self._db.commit()
        return restored


class IdempotencyLedger:
    """Thread-safe exactly-once admission ledger for local job/workflow tests."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._completed: set[tuple[str, str]] = set()

    def claim(self, context: TenantContext, key: str) -> bool:
        token = (context.organization_id, key)
        with self._lock:
            if token in self._completed:
                return False
            self._completed.add(token)
            return True


@dataclass(frozen=True)
class ConcurrencyResult:
    submitted: int
    accepted: int
    unique: bool


def exercise_idempotency(context: TenantContext, key: str, workers: int = 8) -> ConcurrencyResult:
    ledger = IdempotencyLedger()
    with ThreadPoolExecutor(max_workers=workers) as pool:
        results = list(pool.map(lambda _: ledger.claim(context, key), range(workers)))
    return ConcurrencyResult(submitted=workers, accepted=sum(results), unique=sum(results) == 1)


class TenantRepository:
    """Small guard used by service implementations before reading user IDs."""

    @staticmethod
    def require(context: TenantContext, record_tenant: TenantScope) -> None:
        require_same_tenant(context, record_tenant)


class EntitlementEnforcer:
    """Admission facade used by every billable/limited operation."""

    def __init__(self) -> None:
        self._events: dict[tuple[str, str], list[UsageEvent]] = {}
        self._lock = threading.RLock()

    def decide_and_record(self, entitlement: Entitlement, event: UsageEvent) -> UsageDecision:
        if entitlement.tenant.organization_id != event.tenant.organization_id or entitlement.tenant.workspace_id != event.tenant.workspace_id:
            return UsageDecision(tenant=event.tenant, event_type=event.event_type, allowed=False, consumed=0, limit=entitlement.limit, unit=entitlement.unit, remaining=0, reason="tenant scope does not match entitlement", policy_version=entitlement.policy_version)
        with self._lock:
            key = (event.tenant.organization_id, event.event_type)
            consumed = sum(item.quantity for item in self._events.get(key, []) if item.unit == entitlement.unit)
            allowed = event.event_type == entitlement.event_type and event.unit == entitlement.unit and consumed + event.quantity <= entitlement.limit
            if allowed:
                self._events.setdefault(key, []).append(event)
            return UsageDecision(tenant=event.tenant, event_type=event.event_type, allowed=allowed, consumed=consumed, limit=entitlement.limit, unit=entitlement.unit, remaining=max(0, entitlement.limit - consumed - (event.quantity if allowed else 0)), reason="within entitlement" if allowed else "entitlement exceeded", policy_version=entitlement.policy_version)
