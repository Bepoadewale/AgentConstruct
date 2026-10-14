# ticket46 — Real GitHub desired-state PR publishing

PR: [#46 — feat: publish reviewed GitHub desired-state PRs](https://github.com/Bepoadewale/AgentConstruct/pull/46)

Branch: `feature/live-github-desired-state-pr`

Status: ready for review.

## Problem / goal

AgentConstruct can currently create fixture desired-state PR records for approved customer-plan revisions, but it cannot publish a real reviewed desired-state branch and pull request through the GitHub App. Before product-driven cloud execution expands, the code path that hands desired state to the customer repository must be real, reviewable and non-merging.

## Current repo state

- GitHub App repository/branch/manifest reads exist in live read-only mode.
- Signed webhook contracts and fixture desired-state publication records exist.
- The product stores approved plan digests, desired-state package JSON and PR state.
- Live GitHub writes are intentionally disabled and currently raise a read-only error.
- AgentConstruct has no authority to merge customer PRs or deploy from GitHub PR publication.

## Research / references used

Local repo references:

- `apps/api/src/agentconstruct/integrations.py`
- `apps/api/src/agentconstruct/service.py`
- `apps/api/src/agentconstruct/models.py`
- `apps/web/app.js`
- `tests/test_integration_contracts.py`
- `tests/test_customer_plan_review.py`
- `docs/architecture/governed-integrations.md`

GitHub API contracts used conceptually:

- GitHub App installation tokens.
- Git references API for branch creation.
- Contents API for committing package files.
- Pull requests API for opening review.
- Commit statuses API for posting the AgentConstruct review status.

## Work planned for the PR

- Add a guarded live GitHub App desired-state publisher.
- Require explicit `AGENTCONSTRUCT_GITHUB_APP_WRITES_ENABLED=true` before live writes.
- Create a dedicated desired-state branch from the selected base branch.
- Commit package files generated from the exact approved plan digest.
- Open a pull request to the selected branch.
- Post a non-blocking AgentConstruct status/check marker.
- Persist real PR URL, branch, required checks and execution status.
- Keep fixture mode as the local default.
- Keep AgentConstruct unable to self-merge or deploy from this PR.
- Add tests for disabled writes, real publisher request shape and service-level live publication.

## Acceptance criteria

- [x] Fixture desired-state publication still works locally.
- [x] Live GitHub writes are denied unless explicitly enabled.
- [x] When enabled, live publication creates a branch, commits desired-state files, opens a PR and posts status/check evidence.
- [x] The publication remains bound to the exact approved digest.
- [x] AgentConstruct never merges the PR.
- [x] UI/API labels distinguish fixture versus live publication.
- [x] Tests pass.

## Acceptance status

Met for guarded GitHub desired-state PR publishing with mocked GitHub API validation and local fixture publication. No live customer repository PR was created in this PR.

## Tests / validation performed

```bash
make lint
make test
python3 scripts/check_doc_conventions.py
GITHUB_EVENT_NAME=pull_request GITHUB_PR_NUMBER=46 python3 scripts/check_doc_conventions.py
git diff --check
docker compose up -d --build api worker fixture-executor
make smoke
make browser-contract
make customer-plan-e2e
make verify
```

Results:

- `make lint` passed.
- `make test` passed: 112 tests.
- Documentation convention checks passed, including PR #46 mode.
- `git diff --check` passed.
- Docker services rebuilt and restarted.
- `make smoke` passed.
- `make browser-contract` passed.
- `make customer-plan-e2e` passed: developer submission, admin decision, self-approval, local dry-run execution, readiness failure, governed destroy and audit.
- `make verify` passed.

## Evidence files produced

No customer workload cloud test is planned for this PR. No live GitHub PR was created. If a live GitHub PR is created against a customer repository later, record the PR URL and cleanup status here and close the PR unless the user explicitly wants it retained.

## Boundaries

- No Terraform apply.
- No AWS mutation.
- No automatic merge.
- No deployment from GitHub PR publication.
- Live GitHub writes require explicit operator configuration.

## Follow-up work

- Add policy-controlled requirement that cloud execution can require a reviewed/merged desired-state PR.
- Add real GitHub check-run support when the installed App has Checks write permission.
- Add browser-downloadable desired-state evidence export.
