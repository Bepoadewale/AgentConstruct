# ticket44 — App Runner execution path from the product UI/API

PR: [#44 — feat: execute approved App Runner plans from product](https://github.com/Bepoadewale/AgentConstruct/pull/44)

Branch: `feature/app-runner-product-execution`

Status: ready for review.

## Problem / goal

AgentConstruct proved a real App Runner customer-workload pilot through guarded scripts in PR #42, but the product UI/API still stops at approval, fixture PRs, Terraform contract preview and plan-only review. The next product step is an explicit cloud execution boundary that is tied to the approved digest and can later run the real App Runner Terraform profile safely.

## Current repo state

- Approved customer-plan revisions can render App Runner Terraform contracts.
- Administrators can run cloud-readiness preflight and Terraform plan-only review records.
- Local dry-run execution persists customer-facing outputs and observed resources.
- Real App Runner create → validate → destroy evidence exists in `docs/test/test42.md`, but it was script-driven, not initiated through a product execution record.
- There is no durable customer workload execution-history entity for the product UI.

## Research / references used

Local repo references:

- `infrastructure/terraform/customer-workload-app-runner-pilot/`
- `scripts/customer-workload-app-runner-pilot.sh`
- `apps/api/src/agentconstruct/models.py`
- `apps/api/src/agentconstruct/service.py`
- `apps/api/src/agentconstruct/main.py`
- `apps/web/app.js`
- `docs/test/test42.md`

Prior evidence:

- PR #42 real App Runner pilot: two create → smoke → destroy cycles.
- PR #43 first-class local outputs/resource inventory.

## Work planned for the PR

- Add a durable cloud execution run/history model.
- Bind each run to organization, project, revision, approved digest, Terraform render, preflight and plan-review evidence.
- Add an administrator-only API/UI action for “Execute in AWS”.
- Default to a blocked/safe state unless explicit runtime flags are enabled.
- Record exact command/evidence shape for the App Runner execution profile.
- Surface execution history in customer-plan review.
- Keep approval separate from execution.
- Keep AWS mutation disabled in automated tests.
- Add tests for digest binding, missing preflight/plan-review blockers, administrator-only access and no accidental apply.

## Acceptance criteria

- [x] Approved App Runner customer-plan review can create a cloud execution run record.
- [x] Run is bound to exact revision digest, Terraform render, preflight and plan-review.
- [x] Developers cannot create cloud execution runs.
- [x] Missing or stale render/preflight/plan-review blocks execution.
- [x] Default local mode records `BLOCKED_CLOUD_EXECUTION_NOT_ENABLED` and exposes exact boundary text.
- [x] UI shows “Execute in AWS” and execution history without implying deployment happened.
- [x] No AWS resources are created by automated tests or local default mode.
- [x] Tests pass.

## Acceptance status

Met for the safe product execution-history boundary. Real Terraform apply remains follow-up work.

## Tests / validation performed

```bash
make lint
make test
python3 scripts/check_doc_conventions.py
GITHUB_EVENT_NAME=pull_request GITHUB_PR_NUMBER=44 python3 scripts/check_doc_conventions.py
git diff --check
docker compose up -d --build api worker fixture-executor
make smoke
make browser-contract
make customer-plan-e2e
make verify
```

Results:

- `make lint` passed.
- `make test` passed: 110 tests.
- Documentation convention checks passed, including PR #44 mode.
- `git diff --check` passed.
- Rebuilt local API, worker and fixture-executor containers.
- `make smoke` passed.
- `make browser-contract` passed.
- `make customer-plan-e2e` passed.
- `make verify` passed.

## Evidence files produced

No customer workload cloud test is planned for the default PR validation. If an explicitly authorised App Runner apply/destroy is run from the product path, evidence must be recorded in `docs/test/test44.md`.

## Boundaries

- No default Terraform apply.
- No default AWS mutation.
- No GitHub writes.
- This PR creates the product execution-history boundary. A subsequent explicitly authorised run may exercise the real App Runner apply/destroy path and record cloud evidence.

## Follow-up work

- Wire the guarded execution run to actually invoke the App Runner pilot script when `ALLOW_CLOUD_APPLY=true` and operator confirmation are both present.
- Ingest real Terraform outputs and AWS observations into `EnvironmentOutput` and `ObservedResource`.
- Add downloadable evidence export for every execution run.
