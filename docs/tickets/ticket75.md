# ticket75 — Final local contract seams

- PR: #75
- Branch: main
- Status: complete

## Problem / goal

Close the remaining non-AWS contract gaps: explicit capability interfaces,
persisted rollout policy, compatibility/deprecation metadata, and auditable
evidence/decision seams.

## Current repo state

AgentConstruct now has named v1 domain records, tenant-scoped local durability,
runner and queue boundaries, and regression gates. This pass makes provider
capabilities and rollout/compatibility behavior explicit and testable.

## Research / references used

- Existing provider-neutral contracts and local boundary adapters.
- Customer-provided 18-part hardening requirements.

## Work planned for the PR

- Add explicit compute, data, networking, secrets, observability, execution,
  observation, destroy, and pricing protocols.
- Persist feature flags and rollout audit history locally.
- Add API compatibility/deprecation metadata and tests.
- Keep all behavior local-only and fail closed by default.

## Acceptance criteria

- Capability interfaces are independent of AWS implementations.
- Rollout decisions survive process boundaries through local persistence.
- Unsupported client contract versions fail explicitly.
- Existing unit, browser, load, and customer-plan checks remain green.

## Acceptance status

- [x] Full validation complete

## Tests / validation performed

Validated with `make lint`, `make test` (165 passed), local smoke/load/browser/
frontend/responsive/accessibility contracts, customer-plan E2E, documentation
convention checks, and `git diff --check`.

## Evidence files produced

- `apps/api/src/agentconstruct/capabilities.py`
- `apps/api/src/agentconstruct/api_compat.py`
- `apps/api/src/agentconstruct/production_readiness.py`
- `tests/test_production_readiness.py`

## Boundaries

No AWS resource, cloud credential, hosted model, or distributed queue was
created. These are local adapters and release seams.

## Follow-up work

Wire the seams to approved production identity, persistence, billing/catalog,
model, and customer-account execution services when those dependencies are
authorized.
