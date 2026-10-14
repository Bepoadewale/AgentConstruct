# ticket54 — Execution isolation and cell-ready boundaries

PR: execution isolation and cell-ready metadata

Branch: `feature/execution-isolation`

Status: ready for review

## Problem / goal

Make future high-scale execution safe by carrying tenant/cell placement, exact plan
digest, allowlisted operations, bounded timeout, network policy, and credential references
through one typed runner boundary. Keep local execution deterministic and side-effect free.

## Current repo state

- Queue, model, evidence, and tenant contracts exist from PRs 51–53.
- Cloud execution adapters exist, but the domain did not yet have a provider-neutral,
  cell-aware runner contract.
- Local fixture execution is intentionally the default; no AWS apply is part of this PR.

## Research / references used

- `apps/api/src/agentconstruct/contracts.py`
- `apps/api/src/agentconstruct/cloud_execution.py`
- AWS SaaS Lens: https://docs.aws.amazon.com/wellarchitected/latest/saas-lens/saas-lens.html

## Work planned for the PR

- Add typed placement, execution context and outcome contracts.
- Add a fail-closed runner protocol and deterministic fixture runner.
- Add tests and scale/isolation documentation.

## Acceptance criteria

- [x] Typed placement and execution context contracts exist.
- [x] Runner operations are explicitly allowlisted.
- [x] Disabled runner fails closed.
- [x] Fixture runner performs no external side effects and returns safe outputs.
- [x] Credential values are represented only as references.
- [x] Tests cover tenant scope, invalid digest, allowlist denial and fail-closed behavior.
- [x] Scale and isolation boundaries are documented.

## Acceptance status

Met for the typed local execution boundary. Hosted isolated runners and AWS execution remain future deployment work.

## Evidence

Local tests and static validation are required. No customer workload or AWS resources are
created; therefore no `docs/test/test54.md` is produced.

## Tests / validation performed

```bash
make lint
make test
python3 scripts/check_doc_conventions.py
git diff --check
```

Results: 140 tests passed; lint and documentation checks passed.

## Evidence files produced

No customer workload evidence file is produced because this PR has no live execution.

## Boundaries

This PR does not provision AWS resources, execute Terraform, or claim production scale.

## Follow-up work

Connect a hosted runner through the same contract after production identity and execution infrastructure are approved.
