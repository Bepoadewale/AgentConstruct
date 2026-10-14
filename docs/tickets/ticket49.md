# ticket49 — Guarded App Runner execution worker

PR: [#49 — feat: add guarded App Runner execution worker](https://github.com/Bepoadewale/AgentConstruct/pull/49)

Branch: `feature/guarded-cloud-execution-worker`

Status: ready for review.

## Problem / goal

Approved App Runner runs are currently governance records only. The product needs a durable execution boundary that can queue an explicitly authorized run, invoke only the selected App Runner profile, persist command/output evidence and let the observer determine success or failure.

## Current repo state

- Approved revisions can create `CloudExecutionRun` records.
- The run is blocked by default and records the fixed customer-workload pilot command sequence.
- Local fixture execution is handled by a separate durable worker.
- The App Runner pilot script has account, region, confirmation and destroy guards, but the product worker does not invoke it.

## Research / references used

Local repo references:

- `apps/api/src/agentconstruct/service.py`
- `apps/api/src/agentconstruct/models.py`
- `apps/api/src/agentconstruct/main.py`
- `apps/api/src/agentconstruct/worker.py`
- `scripts/customer-workload-app-runner-pilot.sh`
- `docs/test/test42.md`
- `docs/architecture/profile-execution.md`

## Work planned for the PR

- Add a narrow cloud execution adapter and subprocess runner with bounded timeout.
- Queue only a run in `READY_FOR_OPERATOR_APP_RUNNER_EXECUTION` state.
- Add an administrator-only explicit execute endpoint with exact digest and confirmation checks.
- Add durable worker processing for queued cloud runs.
- Persist command, return code, stdout/stderr-safe summaries, outputs and observed state.
- Keep default adapter disabled and local CI mutation-free.
- Add fake-adapter tests for success/failure and stale/unauthorized execution.

## Acceptance criteria

- [x] Default/local mode cannot queue or execute cloud mutation.
- [x] Only an administrator can execute an approved exact-digest run.
- [x] Execution requires account/region/apply/runtime/confirmation gates.
- [x] Cloud runs are durable queued records and survive process restart.
- [x] Worker invokes only the App Runner profile adapter.
- [x] Output/failure evidence is persisted without secrets.
- [x] Tests pass.

## Acceptance status

Met for the guarded queue/worker boundary and fake-adapter verification. No live AWS workload was executed in this PR.

## Tests / validation performed

```bash
make lint
make test
python3 scripts/check_doc_conventions.py
GITHUB_EVENT_NAME=pull_request GITHUB_PR_NUMBER=49 python3 scripts/check_doc_conventions.py
git diff --check
```

Results:

- `make lint` passed.
- `make test` passed: 121 tests.
- Documentation convention checks passed, including PR #49 mode.
- `git diff --check` passed.

## Evidence files produced

No real AWS execution is planned in routine CI. If an explicitly authorized live run occurs, record it in `docs/test/test49.md` and destroy/verify absence afterward.

## Boundaries

- No arbitrary shell, Terraform, kubectl or cloud credentials are exposed to users or agents.
- No execution occurs without explicit operator gates.
- Local fixture mode remains the default.

## Follow-up work

- Run one guarded live App Runner execution from the product with the customer workload repository.
- Ingest Terraform outputs/resource inventory into `EnvironmentOutput` and `ObservedResource` directly from the live run.
- Add real cloud monitoring evidence and governed destroy UI.
