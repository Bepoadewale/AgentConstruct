# ticket43 — Deployment outputs and observed resource inventory

PR: [#43 — feat: add deployment outputs and resource inventory](https://github.com/Bepoadewale/AgentConstruct/pull/43)

Branch: `feature/deployment-outputs-inventory`

Status: ready for review.

## Problem / goal

Customers need to see what AgentConstruct created or observed after an approved execution. A deployment result should not be a raw JSON blob; it should expose useful outputs such as URLs, ARNs, log groups, dashboard links and created resources, while preserving destroyed resources as historical evidence.

## Current repo state

- PR #42 proved a real App Runner customer workload can be created, observed, destroyed, recreated and destroyed again through guarded scripts.
- The product UI can approve a customer plan and run a bounded local dry-run execution.
- Local execution currently stores raw `observed_state` on `Environment`.
- There is no first-class, durable, customer-facing `EnvironmentOutput` or observed resource inventory model.
- The UI does not clearly separate deployment outputs from raw observation details.

## Research / references used

Local repo references:

- `apps/api/src/agentconstruct/models.py`
- `apps/api/src/agentconstruct/service.py`
- `apps/api/src/agentconstruct/main.py`
- `apps/api/src/agentconstruct/fixture_executor.py`
- `apps/web/app.js`
- `tests/test_customer_plan_review.py`
- `docs/test/test42.md`

Prior evidence:

- PR #42 customer workload App Runner pilot evidence in `docs/test/test42.md`.

## Work planned for the PR

- Add durable `EnvironmentOutput` records for customer-visible outputs.
- Add durable `ObservedResource` records for resource inventory.
- Add schema migration coverage.
- Populate outputs/resources from observed execution results.
- Preserve output/resource records after destroy with `DESTROYED` status.
- Expose outputs/resources in customer-plan review, environment list and environment detail APIs.
- Update the local fixture executor to return realistic output/resource observations.
- Update the UI to show “Deployment outputs” and “Observed resources” sections.
- Add tests proving output/resource persistence and destroyed-state evidence.
- Keep cloud mutation out of this PR.

## Acceptance criteria

- [x] Environment outputs are persisted separately from raw observed state.
- [x] Observed resources are persisted separately from raw observed state.
- [x] Customer-plan review includes outputs and resources for local dry-run environments.
- [x] Environment list/detail APIs include outputs and resources.
- [x] UI shows deployment outputs and observed resources in readable form.
- [x] Destroy keeps historical records and marks outputs/resources as `DESTROYED`.
- [x] Sensitive values are masked or represented as references, not raw secrets.
- [x] Tests prove READY and DESTROYED inventory behavior.
- [x] No AWS resources are created by this PR.

## Acceptance status

Met for local fixture execution.

## Tests / validation performed

```bash
make lint
make test
python3 scripts/check_doc_conventions.py
GITHUB_EVENT_NAME=pull_request GITHUB_PR_NUMBER=43 python3 scripts/check_doc_conventions.py
git diff --check
docker compose up -d --build api worker fixture-executor
make smoke
make browser-contract
make customer-plan-e2e
make verify
```

Results:

- `make lint` passed.
- `make test` passed: 108 tests.
- `python3 scripts/check_doc_conventions.py` passed.
- PR-number convention check for PR #43 passed.
- `git diff --check` passed.
- Rebuilt local API, worker and fixture-executor containers.
- `make smoke` passed.
- `make browser-contract` passed.
- `make customer-plan-e2e` passed.
- `make verify` passed.

## Evidence files produced

No customer workload cloud test is planned for this PR. If one becomes necessary, evidence will be recorded in `docs/test/test43.md`.

## Boundaries

- Local fixture execution only.
- No Terraform apply.
- No AWS mutation.
- No real customer workload deployment.
- This PR prepares the product data model for future real App Runner execution from the UI, but does not add that cloud execution path.

## Follow-up work

- Add real App Runner execution profile inside the product UI.
- Capture Terraform outputs from real App Runner apply into `EnvironmentOutput`.
- Capture real AWS resource ARNs/statuses into `ObservedResource`.
- Add customer-facing execution history and evidence export.
