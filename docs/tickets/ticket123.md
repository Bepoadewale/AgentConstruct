# Ticket 123: Governed customer cloud lifecycle

## Goal

Implement one tenant-scoped, approval-gated customer cloud lifecycle that the web UI, REST API, CLI, and MCP use through the same backend contracts: connection verification, live discovery and pricing evidence, Terraform plan, apply, observation, and governed destroy.

## Current state

DavDeploy has a customer AWS connection contract, approval controls, an event-driven worker, and fixture execution. The live customer workload execution path, live pricing evidence, observed outputs, and governed deletion proof need to be made complete and truthfully exposed.

The first implementation slice is complete on this branch: verified connection inventory, catalog and Cost Explorer provenance, separate discovery/execution roles, and API/CLI/MCP lifecycle request contracts exist. Authenticated apply now additionally requires the exact approved revision to name a verified customer connection with a bounded execution role. A fixture or an unverified connection cannot become an apply request merely by enabling process flags.

## Work

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

## Boundaries

No customer workload is created, changed, or destroyed until a specific plan is reviewed and explicitly approved. No long-lived credentials, private keys, or secrets are committed.
