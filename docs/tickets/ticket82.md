# ticket82 — Deploy and verify the platform foundation

- PR: #82
- Branch: `feat/deploy-platform-foundation`
- Status: canceled after verified cleanup

## Problem / goal

Apply the reviewed AgentConstruct platform foundation in the owner AWS account,
prove its safety and recovery controls, and retain only the bounded foundation
needed for later hosted-service activation. Do not create an AWS Organizations
member account or customer-sandbox workload.

## Current repo state

- PR #81 merged the durable platform runtime contract and all CI checks passed.
- Its authenticated plan proposed 20 additions with no change or destroy.
- Foundation mode creates no App Runner service, NAT gateway, Internet gateway
  or fixture signing key.
- Account `654654474502`, Region `us-east-1`, platform VPC `10.42.0.0/16` and
  the platform-specific Terraform state key are the reviewed placement.
- The hosted service remains gated on real Google Workspace-compatible identity,
  HTTPS OPA and an immutable image.

## Research / references used

- `docs/architecture/platform-runtime-readiness.md`.
- `docs/test/test81.md` authenticated plan and Nova evidence.
- AWS RDS snapshot/restore, CloudWatch alarm and AWS Budgets contracts encoded
  and validated in PR #81.
- Repository PR-only, evidence and clean-room rules in `AGENTS.md`.

## Work planned for the PR

- Re-run and review the authenticated foundation plan from merged `main`.
- Apply the platform foundation with exact account, Region, scope and
  confirmation guards.
- Verify private encrypted RDS, backups, deletion protection, three database
  alarms, the platform budget, platform VPC and Nova inference profile.
- Create one manual snapshot, restore it to the exact temporary drill target,
  verify encrypted/private readiness, then delete the temporary database.
- Record created and retained resources, recurring-cost boundaries, commands,
  observed results and teardown/absence evidence in `docs/test/test82.md`.
- Run repository validation and required clean-room cycles before merge.

## Acceptance criteria

- No AWS Organizations member account or customer-sandbox resource is created.
- The apply targets the exact reviewed account, Region, VPC CIDR and state key.
- RDS is available, encrypted, private, backed up and deletion-protected.
- The platform budget and at least three actionable RDS alarms exist.
- No App Runner service, NAT gateway or public platform subnet is retained.
- A manual snapshot becomes available and a temporary private encrypted restore
  succeeds; the temporary database is deleted afterward.
- Evidence contains no credential, secret, email address, prompt or model output.
- Required local verification and CI pass.

## Acceptance status

- [x] Exact account, Region, scope and state guards passed.
- [ ] Foundation apply completes from the merged reviewed contract — canceled
  by the owner before completion.
- [ ] Database, alarm, budget, VPC and Nova verification passes — intentionally
  not retained or claimed.
- [ ] Snapshot and restore/delete drill passes — not run; the empty transient
  database was deleted without a snapshot.
- [x] App Runner, NAT, database, snapshot and platform resources are absent.
- [x] Interrupted operation, cleanup and cost boundary are documented.
- [ ] Required documentation CI is pending remote execution.

## Tests / validation performed

- Authenticated plan confirmed 20 additions, zero changes and zero destroys.
- Apply was interrupted at the owner's request and the surviving background
  Terraform process was explicitly terminated.
- Two state-backed destroy passes and an exact RDS delete removed all partially
  created resources.
- Absence verification returned Terraform state 0, tagged platform resources
  0, budget 0, alarms 0, snapshots 0 and NAT gateways 0.

## Evidence files produced

`docs/test/test82.md` is the PR-numbered source of truth for the interrupted AWS
operation, exact cleanup and final absence checks.

## Boundaries

- This is a platform foundation, not a customer-ready service.
- Platform and customer sandbox are separate VPC/state/IAM/tag scopes inside one
  AWS account; a VPC is not an account security boundary.
- RDS and retained snapshots incur charges. No idle NAT or App Runner service is
  authorized in this PR.
- The operator profile is a pilot credential path and must be replaced by a
  short-lived operator role before routine production operations.

## Follow-up work

- Revisit a smaller platform architecture and lower cost guardrail only in a
  new reviewed PR after explicit owner approval.
- Do not retry this foundation deployment from this PR.
