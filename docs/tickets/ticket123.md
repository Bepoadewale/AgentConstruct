# ticket123: Governed customer cloud lifecycle

PR: #123
Branch: feat/customer-cloud-lifecycle

## Problem / goal

Implement one tenant-scoped, approval-gated customer cloud lifecycle that the web UI, REST API, CLI, and MCP use through the same backend contracts: connection verification, live discovery and pricing evidence, Terraform plan, apply, observation, and governed destroy.

## Current repo state

DavDeploy has a customer AWS connection contract, approval controls, an event-driven worker, and fixture execution. The live customer workload execution path, live pricing evidence, observed outputs, and governed deletion proof need to be made complete and truthfully exposed.

The first implementation slice is complete on this branch: verified connection inventory, catalog and Cost Explorer provenance, separate discovery/execution roles, and API/CLI/MCP lifecycle request contracts exist. Authenticated apply now additionally requires the exact approved revision to name a verified customer connection with a bounded execution role. A fixture or an unverified connection cannot become an apply request merely by enabling process flags.

## Research / references used

- Existing DavDeploy tenant, approval, Terraform-render, CloudFormation-role, worker, API, CLI, and MCP contracts.
- AWS IAM least-privilege and CodeBuild event delivery conventions already used by the control-plane Terraform.

## Work planned for the PR

- Inspect and extend existing provider, policy, execution, API, CLI, and MCP boundaries.
- Keep every privileged operation tenant-scoped, audit-backed, plan-digest-bound, and approval-gated.
- Implement bounded AWS-first adapters without granting browsers or models credentials or shell access.
- Add focused tests and one clean-room validation cycle because this changes execution lifecycle and Terraform behavior.

## Acceptance criteria

- [ ] Supported lifecycle operations share the same governed service contracts across API, CLI, and MCP.
- [ ] Live discovery and pricing evidence are explicitly labeled with provenance and fallback behavior.
- [ ] Apply and destroy remain impossible without the correct approved immutable plan and policy result.
- [ ] Outputs and observed state are persisted and exposed without claiming success before verification.
- [ ] Tests and clean-room evidence are recorded truthfully.

## Acceptance status

In progress. The connection, discovery, execution-boundary, and event-driven runner foundations are implemented. Real saved-plan artifact ingestion and the complete customer lifecycle remain to be validated before merge.

## Tests / validation performed

- Full Python suite and Ruff were run before the final artifact-review changes.
- Terraform formatting and offline validation were run for both control-plane and customer-workload modules.
- Final clean-room evidence will be recorded in `docs/test/test123.md` before merge.

## Evidence files produced

- `docs/tickets/ticket123.md`
- `docs/test/test123.md` (to be completed after the single required clean validation cycle)

## Boundaries

No customer workload is created, changed, or destroyed until a specific plan is reviewed and explicitly approved. No long-lived credentials, private keys, or secrets are committed.

## Follow-up work

- Configure a real customer account only after the production runner has been provisioned and the reviewed Terraform plan artifact is visible in the product.
