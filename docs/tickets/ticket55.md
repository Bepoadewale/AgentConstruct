# ticket55 — Usage and entitlement boundaries

PR: usage and entitlement boundaries

Branch: `feature/usage-entitlements`

Status: ready for review

## Problem / goal

The scale strategy requires tenant-aware quotas and future metering, but the current
repository only has a raw usage event contract. Add deterministic admission contracts
without introducing billing or a vendor dependency.

## Current repo state

- `UsageEvent` exists as a tenant-scoped input contract.
- Queue and model boundaries exist, but no typed entitlement decision exists.
- Local execution and tests must remain provider-free and deterministic.

## Research / references used

- `apps/api/src/agentconstruct/contracts.py`
- `apps/api/src/agentconstruct/queue.py`
- `docs/strategy/10-scale-and-multi-tenancy.md`
- AWS SaaS Lens: https://docs.aws.amazon.com/wellarchitected/latest/saas-lens/saas-lens.html

## Work planned for the PR

- Add `Entitlement` and `UsageDecision` contracts.
- Add a deterministic in-memory usage ledger with tenant isolation and time windows.
- Add tests and scale documentation; do not implement billing.

## Acceptance criteria

- [x] Entitlements are tenant-scoped and versioned.
- [x] Usage decisions are deterministic and unit-aware.
- [x] Cross-tenant events are denied.
- [x] Exceeded limits are denied without counting the attempt.
- [x] No billing provider or cloud resource is introduced.

## Acceptance status

Met for local admission and contract boundaries. Durable hosted metering and billing remain future work.

## Tests / validation performed

```bash
make lint
make test
python3 scripts/check_doc_conventions.py
git diff --check
```

Results: expected 143 tests; lint and documentation checks must pass.

## Evidence files produced

No customer workload or AWS execution occurs; no `docs/test/test55.md` is produced.

## Boundaries

This PR does not claim production quota enforcement, billing accuracy, or million-customer capacity.

## Follow-up work

Add a durable usage sink and billing integration only after hosted tenancy and retention requirements are approved.
