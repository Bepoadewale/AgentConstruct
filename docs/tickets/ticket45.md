# ticket45 — Customer workload execution history and evidence export

PR: [#45 — feat: add customer workload execution history evidence](https://github.com/Bepoadewale/AgentConstruct/pull/45)

Branch: `feature/execution-history-evidence`

Status: ready for review.

## Problem / goal

Customers and administrators need a durable history of workload execution attempts, including exact plan digest, source commit, Terraform status, resources/outputs, destroy proof, failure reason and an exportable evidence bundle. PR #44 introduced guarded cloud execution run records; this PR makes those records easier to inspect and export.

## Current repo state

- Cloud execution runs can be requested for approved App Runner plans.
- Runs are administrator-only and blocked by default unless future cloud-apply gates are enabled.
- Runs have attempt numbers, command evidence and boundary text.
- There is no dedicated execution-history API, export endpoint or richer UI view for customer/auditor review.

## Research / references used

Local repo references:

- `apps/api/src/agentconstruct/models.py`
- `apps/api/src/agentconstruct/service.py`
- `apps/api/src/agentconstruct/main.py`
- `apps/web/app.js`
- `docs/test/test42.md`
- `docs/tickets/ticket44.md`

## Work planned for the PR

- Add execution-history list/detail/export APIs.
- Include attempt number, approved digest, source repository/branch/commit, selected AWS account/region, command sequence, Terraform states, outputs/resources, destroy proof and failure reason where available.
- Add customer-plan review UI/history rendering for execution attempts.
- Add export-ready evidence JSON structure.
- Add tests for history visibility, tenant scoping, evidence content and blocked/default execution status.
- Keep AWS mutation disabled.

## Acceptance criteria

- [x] Users can list execution history for their organization.
- [x] Execution evidence includes attempt, digest, source repo/branch/commit, profile, account/region and command boundary.
- [x] Evidence export includes outputs/resources and destroy/failure placeholders without claiming execution.
- [x] Tenant isolation is enforced.
- [x] UI shows customer workload execution history in readable form.
- [x] No AWS resources are created by this PR.
- [x] Tests pass.

## Acceptance status

Met for execution-history/evidence export APIs and readable UI history.

## Tests / validation performed

```bash
make lint
make test
python3 scripts/check_doc_conventions.py
GITHUB_EVENT_NAME=pull_request GITHUB_PR_NUMBER=45 python3 scripts/check_doc_conventions.py
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
- Documentation convention checks passed, including PR #45 mode.
- `git diff --check` passed.
- Docker services rebuilt and restarted.
- `make smoke` passed.
- `make browser-contract` passed.
- `make customer-plan-e2e` passed: developer submission, admin decision, self-approval, local dry-run execution, readiness failure, governed destroy and audit.
- `make verify` passed.

## Evidence files produced

No customer workload cloud test is planned for this PR. If an explicitly authorised App Runner apply/destroy is run, evidence must be recorded in `docs/test/test45.md`.

## Boundaries

- No Terraform apply.
- No AWS mutation.
- No GitHub writes.
- Evidence export is product/audit evidence for recorded runs; it is not cloud execution proof unless a run contains observed AWS outputs/resources from a future apply path.

## Follow-up work

- Wire real App Runner apply/destroy output ingestion into this evidence export.
- Add downloadable file export from the browser.
- Add timeline grouping by project/environment.
