"""Deterministic tenant usage and entitlement boundary.

This is a local admission ledger, not a billing system. Hosted deployments can replace
the storage adapter while preserving the contract and tenant isolation rules.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import UTC, datetime, timedelta
from typing import Protocol

from agentconstruct.contracts import Entitlement, UsageDecision, UsageEvent


class UsageMeter(Protocol):
    def record(self, event: UsageEvent) -> None: ...


class EntitlementService(Protocol):
    def decide(self, entitlement: Entitlement, event: UsageEvent) -> UsageDecision: ...


class QuotaService(EntitlementService, Protocol):
    """Quota admission is intentionally the same shape as entitlement admission."""


class UsageMeterLedger:
    """Named adapter combining metering and admission for future billing clients."""

    def __init__(self, ledger: InMemoryUsageLedger | None = None):
        self.ledger = ledger or InMemoryUsageLedger()

    def record(self, event: UsageEvent) -> None:
        self.ledger.record(event)

    def decide(self, entitlement: Entitlement, event: UsageEvent) -> UsageDecision:
        decision = self.ledger.decide(entitlement, event)
        if decision.allowed:
            self.ledger.record(event)
        return decision


class InMemoryUsageLedger:
    def __init__(self) -> None:
        self._events: dict[tuple[str, str], list[UsageEvent]] = defaultdict(list)

    def record(self, event: UsageEvent) -> None:
        self._events[(event.tenant.organization_id, event.event_type)].append(event)

    def decide(self, entitlement: Entitlement, event: UsageEvent) -> UsageDecision:
        if event.tenant.organization_id != entitlement.tenant.organization_id:
            return UsageDecision(
                tenant=event.tenant,
                event_type=event.event_type,
                allowed=False,
                consumed=0,
                limit=entitlement.limit,
                unit=entitlement.unit,
                remaining=0,
                reason="tenant scope does not match entitlement",
                policy_version=entitlement.policy_version,
            )
        if event.event_type != entitlement.event_type or event.unit != entitlement.unit:
            return UsageDecision(
                tenant=event.tenant,
                event_type=event.event_type,
                allowed=False,
                consumed=0,
                limit=entitlement.limit,
                unit=entitlement.unit,
                remaining=0,
                reason="event type or unit is not entitled",
                policy_version=entitlement.policy_version,
            )
        cutoff = datetime.now(UTC) - timedelta(seconds=entitlement.window_seconds)
        consumed = sum(
            item.quantity
            for item in self._events[(event.tenant.organization_id, event.event_type)]
            if item.occurred_at >= cutoff and item.unit == entitlement.unit
        )
        allowed = consumed + event.quantity <= entitlement.limit
        remaining = max(0.0, entitlement.limit - consumed)
        return UsageDecision(
            tenant=event.tenant,
            event_type=event.event_type,
            allowed=allowed,
            consumed=consumed,
            limit=entitlement.limit,
            unit=entitlement.unit,
            remaining=remaining,
            reason="within entitlement" if allowed else "entitlement exceeded",
            policy_version=entitlement.policy_version,
        )
