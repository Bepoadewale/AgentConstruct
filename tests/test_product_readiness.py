import pytest
from agentconstruct.boundaries import TenantBoundaryError, TenantContext
from agentconstruct.contracts import ArchitecturePlanV1
from agentconstruct.product_readiness import (
    BillingControls,
    InMemoryMemberships,
    LocalAnalytics,
    ProductPlan,
    compare_plans,
    deployment_bundle_digest,
    security_headers,
)


def admin() -> TenantContext:
    return TenantContext(organization_id="org-a", workspace_id="ws-a", actor_id="admin", role="administrator")


def plan(components: tuple[str, ...], unknowns: tuple[str, ...] = ()) -> ArchitecturePlanV1:
    return ArchitecturePlanV1(tenant=admin().contract_scope(), actor_id="admin", architecture_family="managed", components=components, unknowns=unknowns, decision_scores={"risk": 2})


def test_membership_invites_and_role_changes_are_admin_only() -> None:
    memberships = InMemoryMemberships()
    invited = memberships.invite(admin(), "customer@example.com")
    assert memberships.change_role(admin(), invited.subject, "operator").role == "operator"
    with pytest.raises(TenantBoundaryError):
        memberships.invite(admin().model_copy(update={"role": "developer"}), "blocked@example.com")


def test_billing_controls_gate_features_and_usage() -> None:
    controls = BillingControls((ProductPlan(name="beta", monthly_limit=2, features=frozenset({"planning"})),))
    controls.assign(admin(), "beta")
    assert controls.admit(admin(), "planning") is True
    assert controls.admit(admin(), "planning") is True
    assert controls.admit(admin(), "planning") is False
    assert controls.admit(admin(), "execution") is False


def test_revision_diff_inventory_analytics_security_and_bundle() -> None:
    diff = compare_plans(plan(("api", "db"), ("catalog",)), plan(("api", "queue"), ("network",)))
    assert diff.added_components == ("queue",)
    assert diff.removed_components == ("db",)
    analytics = LocalAnalytics()
    analytics.track(admin(), "plan_created")
    assert analytics.events[0]["organization_id"] == "org-a"
    assert security_headers()["X-Frame-Options"] == "DENY"
    assert len(deployment_bundle_digest({"api": "v1", "web": "v1"})) == 64
