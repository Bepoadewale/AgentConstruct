# ticket74 — Local production-readiness completion

- PR: #74
- Branch: main
- Status: complete

## Problem / goal

Finish the remaining non-AWS hardening gaps after the initial scale-ready
boundary work: typed domain records, durable local lifecycle storage,
idempotency/concurrency checks, and enforceable usage admission.

## Current repo state

The initial boundary pass provided protocols and deterministic adapters. This
pass adds named v1 domain contracts, a tenant-scoped SQLite adapter, backup and
soft-delete primitives, idempotency stress coverage, and quota enforcement.

## Research / references used

- Existing AgentConstruct contracts, worker, policy, and execution boundaries.
- Customer-provided 18-part non-AWS hardening requirements.

## Work planned for the PR

- Add WorkloadSpec, ArchitecturePlan, DeploymentPlan, Approval, ExecutionJob,
  ObservedState, AuditEvent, CostEstimate, Recommendation, ResourceRecord, and
  EnvironmentOutput v1 contracts.
- Add durable local export, archive, backup, soft-delete, and tenant checks.
- Add concurrent idempotency and entitlement enforcement tests.

## Acceptance criteria

- Named contracts carry version, scope, provenance, evidence, policy/catalog,
  digest, and timestamps.
- Local records cannot be read across organizations or workspaces.
- Duplicate concurrent work admits exactly once.
- Usage admission rejects cross-tenant and over-quota events.
- All existing local flows remain green and no AWS mutation occurs.

## Acceptance status

- [x] Full validation complete

## Tests / validation performed

Validated with `make lint`, `make test` (164 passed), local smoke/load/browser/
frontend/responsive/accessibility contracts, customer-plan E2E, documentation
convention checks, and `git diff --check`.

## Evidence files produced

- `apps/api/src/agentconstruct/contracts.py`
- `apps/api/src/agentconstruct/production_readiness.py`
- `tests/test_production_readiness.py`

## Boundaries

This remains local-only. The SQLite adapter is a correctness and migration
seam, not a hosted persistence service, and no AWS resource or credential is
created.

## Follow-up work

Connect the same contracts to production identity, hosted persistence,
isolated customer-account runners, and live billing/catalog systems when those
external dependencies are authorized.
