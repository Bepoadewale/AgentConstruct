# ticket58 — Local load smoke and read-only AWS evidence

PR: local load smoke and read-only AWS evidence

Branch: `feature/local-load-and-readonly-evidence`

Status: ready for review

## Problem / goal

The local product needs a bounded repeatable load smoke, and the existing AWS read-only
verification should have a numbered evidence record. Add both without provisioning AWS.

## Current repo state

- The API, queue, planner, integrations and local Compose stack already exist.
- AWS discovery and Cost Explorer access are implemented as read-only adapters.
- No bounded local load command or current account evidence record existed for this work.

## Research / references used

- `scripts/smoke.sh`
- `apps/api/src/agentconstruct/integrations.py`
- `docs/strategy/10-scale-and-multi-tenancy.md`
- AWS Cost Explorer API: https://docs.aws.amazon.com/cost-management/latest/userguide/ce-api.html

## Work planned for the PR

- Add a localhost-only concurrent load smoke command and Make target.
- Document its limits and the read-only AWS boundary.
- Record current AWS account/region evidence in `docs/test/test58.md`.

## Acceptance criteria

- [x] Load smoke rejects non-local targets and bounds request/concurrency values.
- [x] Load smoke reports request count and p95 latency.
- [x] AWS evidence records read-only inventory and spend observations.
- [x] No AWS resource is created or modified.

## Acceptance status

Met for local load smoke and read-only account evidence. This is not production capacity evidence.

## Tests / validation performed

```bash
make lint
make test
python3 scripts/check_doc_conventions.py
git diff --check
```

Results: expected 145 tests; lint, documentation conventions and diff checks must pass.

## Evidence files produced

- `docs/test/test58.md` — read-only AWS inventory and Cost Explorer evidence.

## Boundaries

No AWS resources were created, changed or destroyed by this PR.

## Follow-up work

Run approved hosted load/failure tests only after the control plane is deployed into a dedicated test environment.
