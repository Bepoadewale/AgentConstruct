"""Local/private-beta product services that do not require AWS."""

from __future__ import annotations

import hashlib
import secrets
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Protocol

from pydantic import BaseModel, ConfigDict, Field

from davdeploy.boundaries import TenantBoundaryError, TenantContext
from davdeploy.contracts import ArchitecturePlanV1, ResourceRecordV1


class Membership(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    subject: str = Field(min_length=1, max_length=160)
    email: str = Field(min_length=3, max_length=240)
    role: str = Field(default="developer", min_length=1, max_length=40)
    state: str = "INVITED"


class MembershipService(Protocol):
    def invite(self, context: TenantContext, email: str, role: str = "developer") -> Membership: ...
    def change_role(self, context: TenantContext, subject: str, role: str) -> Membership: ...


class InMemoryMemberships:
    def __init__(self) -> None:
        self._members: dict[tuple[str, str], Membership] = {}

    def invite(self, context: TenantContext, email: str, role: str = "developer") -> Membership:
        if context.role not in {"administrator", "owner"}:
            raise TenantBoundaryError("administrator role required")
        member = Membership(subject=f"invite-{secrets.token_hex(6)}", email=email, role=role)
        self._members[(context.organization_id, member.subject)] = member
        return member

    def change_role(self, context: TenantContext, subject: str, role: str) -> Membership:
        if context.role not in {"administrator", "owner"}:
            raise TenantBoundaryError("administrator role required")
        key = (context.organization_id, subject)
        member = self._members[key]
        updated = member.model_copy(update={"role": role})
        self._members[key] = updated
        return updated


class ProductPlan(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    name: str = Field(min_length=1, max_length=80)
    monthly_limit: float = Field(gt=0)
    features: frozenset[str] = frozenset()


class BillingControls:
    def __init__(self, plans: tuple[ProductPlan, ...] | None = None) -> None:
        self.plans = {plan.name: plan for plan in plans or (ProductPlan(name="beta", monthly_limit=100, features=frozenset({"planning", "review"})),)}
        self.assignments: dict[str, str] = {}
        self.usage: dict[str, float] = {}

    def assign(self, context: TenantContext, plan: str) -> None:
        if plan not in self.plans:
            raise ValueError("unknown product plan")
        self.assignments[context.organization_id] = plan

    def admit(self, context: TenantContext, feature: str, quantity: float = 1) -> bool:
        plan = self.plans[self.assignments.get(context.organization_id, "beta")]
        if feature not in plan.features:
            return False
        used = self.usage.get(context.organization_id, 0)
        if used + quantity > plan.monthly_limit:
            return False
        self.usage[context.organization_id] = used + quantity
        return True


@dataclass(frozen=True)
class RevisionDiff:
    added_components: tuple[str, ...]
    removed_components: tuple[str, ...]
    changed_unknowns: tuple[str, ...]
    score_changes: dict[str, tuple[int | None, int | None]]


def compare_plans(previous: ArchitecturePlanV1, current: ArchitecturePlanV1) -> RevisionDiff:
    return RevisionDiff(
        added_components=tuple(sorted(set(current.components) - set(previous.components))),
        removed_components=tuple(sorted(set(previous.components) - set(current.components))),
        changed_unknowns=tuple(sorted(set(current.unknowns) ^ set(previous.unknowns))),
        score_changes={key: (previous.decision_scores.get(key), current.decision_scores.get(key)) for key in set(previous.decision_scores) | set(current.decision_scores) if previous.decision_scores.get(key) != current.decision_scores.get(key)},
    )


@dataclass(frozen=True)
class InventoryView:
    resources: tuple[ResourceRecordV1, ...]
    unknown_count: int
    generated_at: datetime = field(default_factory=lambda: datetime.now(UTC))


class LocalAnalytics:
    def __init__(self) -> None:
        self.events: list[dict[str, Any]] = []

    def track(self, context: TenantContext, name: str, properties: dict[str, str] | None = None) -> None:
        self.events.append({"organization_id": context.organization_id, "workspace_id": context.workspace_id, "actor_id": context.actor_id, "name": name, "properties": properties or {}, "at": datetime.now(UTC).isoformat()})


@dataclass(frozen=True)
class SupportCase:
    case_id: str
    organization_id: str
    subject: str
    status: str = "OPEN"


@dataclass(frozen=True)
class ChangelogEntry:
    version: str
    title: str
    body: str
    published_at: datetime = field(default_factory=lambda: datetime.now(UTC))


def security_headers() -> dict[str, str]:
    return {"X-Content-Type-Options": "nosniff", "X-Frame-Options": "DENY", "Referrer-Policy": "strict-origin-when-cross-origin", "Permissions-Policy": "camera=(), microphone=(), geolocation=()", "Content-Security-Policy": "default-src 'self'; connect-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline'; frame-ancestors 'none'; base-uri 'self'"}


def deployment_bundle_digest(files: dict[str, str]) -> str:
    canonical = "".join(f"{name}\0{files[name]}\0" for name in sorted(files))
    return hashlib.sha256(canonical.encode()).hexdigest()
