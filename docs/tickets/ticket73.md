# ticket73 — Scale-ready local boundaries

- PR: #73
- Branch: main
- Status: complete

## Problem / goal

Harden the local product around stable contracts, tenant scope, isolated jobs,
model/provider replacement, evidence provenance, lifecycle controls, and staged
rollouts before adding more cloud infrastructure.

## Current repo state

The repository already has versioned contract primitives, a PostgreSQL queue,
model gateway, usage ledger, evidence refs, and a fail-closed execution runner.
This pass completes the missing local boundary interfaces and regression coverage.

## Research / references used

- Existing AgentConstruct domain contracts and local execution tests.
- Customer-provided scale-readiness requirements.

## Work planned for the PR

- Add required tenant context and cross-tenant fail-closed checks.
- Add feature flags, lifecycle export/deletion/archive policy, and capability registry.
- Add evidence graph, separate decision engines, and runner limit validation.
- Complete queue heartbeat/retry/cancel/dead-letter methods.
- Enforce model provider, timeout, and token budgets.
- Document the replacement seams and local-only limits.

## Acceptance criteria

- All new boundaries are provider-neutral and testable locally.
- Tenant mismatches fail closed.
- Model and runner limits are enforced before work starts.
- Queue lifecycle operations are explicit and idempotent.
- Existing API, browser, and customer-plan flows remain green.
- No AWS resource or credential mutation occurs.

## Acceptance status

- [x] Full validation complete

## Tests / validation performed

Validated with `make lint`, `make test` (153 passed), `make smoke`,
`make browser-contract`, `make frontend-contract`,
`make frontend-responsive-contract`, `make customer-plan-e2e`,
`python3 scripts/check_doc_conventions.py`, and `git diff --check`.

## Evidence files produced

- `docs/architecture/scale-ready-boundaries.md`
- `tests/test_hardening_boundaries.py`

## Boundaries

This is local contract hardening. It does not provision AWS, deploy workloads,
grant cloud credentials, or claim production-scale execution.

## Follow-up work

Connect these adapters to a real identity provider, durable hosted lifecycle
store, live billing/catalog sources, and isolated customer-account runners only
after the local contracts are accepted.
