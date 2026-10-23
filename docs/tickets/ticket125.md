# ticket125: Governed customer execution observation and teardown

PR: #125
Branch: feat/customer-execution-observation-destroy

## Problem / goal

The authenticated runner could produce a reviewed apply plan and execute its saved artifact, but the product did not yet have a symmetric, reviewed destroy-plan path or persist the runner result needed for customer-visible output and absence evidence.

## Current repo state

The isolated CodeBuild executor is provisioned and the live control plane has explicit cloud plan/apply gates enabled. No customer workload is created by this PR.

## Research / references used

- Existing authenticated plan-artifact implementation in `ProductService`.
- Existing bounded customer Terraform runner script.
- Existing CLI and MCP v1 transport contracts.

## Work planned for the PR

- Add authenticated Terraform destroy-plan review mode.
- Require a checksum-bound saved destroy plan and exact destroy confirmation before queueing teardown.
- Ingest runner result artifacts into execution history, including Terraform outputs and verified destroy proof.
- Expose the bounded operations through API, CLI, and MCP contracts.

## Acceptance criteria

- [x] A destroy is never a fresh Terraform command from the control plane.
- [x] A destroy applies only the reviewed saved destroy artifact after checksum verification.
- [x] Destroy completion is successful only with an absence proof artifact.
- [x] CLI and MCP use the same backend-governed API contract.

## Acceptance status

Implemented and focused locally validated. Merge, control-plane deployment, and the explicit live customer pilot remain pending.

## Validation

See `docs/test/test125.md`.

## Tests / validation performed

- Focused customer-review and cloud-execution pytest suite.
- Ruff checks for changed API, CLI, MCP, and test modules.
- Shell syntax validation for the bounded runner.

## Evidence files produced

- `docs/tickets/ticket125.md`
- `docs/test/test125.md`
- Updated `contracts/openapi-v1.json`

## Boundaries

This PR adds product contracts only. It does not create, modify, or destroy customer cloud resources until a later explicit, reviewed live run.

## Follow-up work

- Deploy this reviewed control-plane change.
- Complete the customer UI controls and run the bounded end-to-end customer pilot.
