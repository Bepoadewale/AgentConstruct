from agentconstruct.contracts import Entitlement, TenantScope, UsageEvent
from agentconstruct.usage import InMemoryUsageLedger, UsageMeterLedger


def tenant(org="org-demo"):
    return TenantScope(organization_id=org, workspace_id="ws", actor_id="user")


def event(org="org-demo", quantity=1):
    return UsageEvent(
        tenant=tenant(org),
        event_type="plan.generated",
        quantity=quantity,
        unit="request",
        source="test",
    )


def entitlement(org="org-demo", limit=2):
    return Entitlement(
        tenant=tenant(org), event_type="plan.generated", limit=limit, unit="request"
    )


def test_usage_is_tenant_scoped_and_admission_is_deterministic():
    ledger = InMemoryUsageLedger()
    ledger.record(event(quantity=1))
    decision = ledger.decide(entitlement(), event(quantity=1))
    assert decision.allowed is True
    assert decision.consumed == 1
    assert decision.remaining == 1


def test_usage_limit_denies_without_recording_the_attempt():
    ledger = InMemoryUsageLedger()
    ledger.record(event(quantity=2))
    decision = ledger.decide(entitlement(), event(quantity=1))
    assert decision.allowed is False
    assert decision.reason == "entitlement exceeded"


def test_cross_tenant_usage_is_denied():
    ledger = InMemoryUsageLedger()
    decision = ledger.decide(entitlement(org="org-a"), event(org="org-b"))
    assert decision.allowed is False
    assert "tenant" in decision.reason


def test_usage_meter_records_only_allowed_events():
    meter = UsageMeterLedger()
    first = event(quantity=1)
    second = event(quantity=1)
    assert meter.decide(entitlement(limit=1), first).allowed is True
    assert meter.decide(entitlement(limit=1), second).allowed is False
