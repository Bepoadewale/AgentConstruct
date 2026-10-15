# ticket76 — Private-beta product readiness

- PR: #76
- Branch: main
- Status: complete

## Problem / goal

Finish the non-AWS work needed to make AgentConstruct ready for a controlled
private beta: membership, billing-ready controls, plan comparison, analytics,
security defaults, support/changelog primitives, and self-hosted packaging
metadata.

## Current repo state

The control plane already has versioned contracts, tenant boundaries, local
durability, queues, runners, policy, rollout, and evaluation seams. This pass
adds the customer-facing product service primitives and applies security
headers at the API boundary.

## Research / references used

- Existing local identity, workspace, plan, and review flows.
- Customer-provided non-AWS product readiness priorities 1–15.

## Work planned for the PR

- Add administrator-only membership and role management primitives.
- Add feature/usage gating, plan comparison, inventory/analytics/support
  models, changelog metadata, security headers, and deployment bundle digests.
- Add tests proving tenant-safe admission, revision diffs, and local product
  readiness behavior.

## Acceptance criteria

- Local/private-beta product controls are explicit and testable.
- API responses include baseline security headers.
- Usage and feature access are bounded before billing integration.
- Plan changes are explainable and support surfaces have stable records.
- No AWS resource or credential mutation occurs.

## Acceptance status

- [x] Full validation complete

## Durable control-plane completion

The initial primitives are now backed by the control-plane database and
versioned API routes rather than only process memory:

- administrator-created, expiring workspace invitations (only token digests
  are stored);
- hashed, scoped API credentials with one-time display and revocation;
- tenant-scoped usage records for future plans, quotas and billing;
- immutable revision comments for collaboration;
- durable support tickets; and
- administrator-requested export/deletion lifecycle records with audit events.

These are provider-neutral private-beta controls. They deliberately do not
claim hosted SSO, payment collection, email delivery, or automated deletion
execution before those external integrations are selected and verified.

## Tests / validation performed

Validated with lint, the complete unit suite, local smoke/load/browser/frontend
contracts, customer-plan E2E, documentation conventions, and diff checks.

## Evidence files produced

- `apps/api/src/agentconstruct/product_readiness.py`
- `tests/test_product_readiness.py`
- `docs/tickets/ticket76.md`

## Boundaries

These are local/private-beta implementations. Payment processing, hosted SSO,
customer cloud execution, and production support infrastructure remain external
integrations.

## Follow-up work

Connect these stable seams to approved identity, payment, hosted persistence,
and support providers during private-beta operations.
