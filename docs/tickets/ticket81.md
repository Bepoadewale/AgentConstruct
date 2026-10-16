# ticket81 — Ready the durable platform runtime

- PR: #81
- Branch: `feat/platform-runtime-readiness`
- Status: in progress

## Problem / goal

Prepare the AgentConstruct platform placement for an owner-operated AWS pilot:
durable PostgreSQL, governed Nova 2 Lite inference, actionable monitoring,
budget controls, backup/restore operations, release verification and a bounded
operator runbook. The platform must remain separate from the customer sandbox
and must not create an AWS Organizations member account.

## Current repo state

- The platform runtime Terraform can create App Runner, ECR, a private RDS
  database, one NAT gateway and a Nova-scoped runtime role.
- Nova 2 Lite is implemented but has only fake-client evidence.
- RDS backups exist in the Terraform contract, but no AWS backup/restore drill
  or platform alarm contract has been executed.
- Hosted mode correctly refuses to start without a real JWKS/OIDC provider.
  Google Workspace identity has not been configured yet.
- Account `654654474502` currently has no AgentConstruct App Runner service or
  RDS instance.

## Work planned for the PR

- Add platform budget and actionable CloudWatch alarm contracts.
- Add bounded live Nova evaluation, health/readiness, backup and restore-drill
  operator commands with exact account and platform-scope guards.
- Make durable database, Nova, monitoring and identity activation explicit in
  Terraform and runtime scripts.
- Add retention, encryption, final-snapshot, deletion and recovery safeguards.
- Add static and offline tests, operator documentation and release gates.
- Run authenticated Terraform plans and a budget-capped live Nova evaluation.

## Acceptance criteria

- No member-account or customer-sandbox resource operation is introduced.
- Hosted service creation fails before apply when OIDC/JWKS settings are absent.
- Nova access is limited to the reviewed inference profile and evaluation calls
  have strict token, count, timeout and cost-evidence bounds.
- Platform alarms cover App Runner service health and RDS capacity/connection
  signals, and budget notifications are configurable.
- RDS is encrypted, private, deletion-protected, backed up and final-snapshotted.
- Backup/restore and release verification commands are bounded and auditable.
- Two clean-room cycles and all CI checks pass.

## Acceptance status

- [ ] Account and placement guards are enforced.
- [ ] Hosted identity is a hard service activation gate.
- [ ] Nova live evaluation is bounded and evidenced.
- [ ] Budget and actionable alarms are implemented.
- [ ] Database recovery safeguards are implemented.
- [ ] Operations and release gates are documented and tested.
- [ ] Two clean-room cycles and CI pass.

## Evidence files produced

Live platform and Nova evidence will be recorded under `docs/test/test81.md`.
It will distinguish created AWS resources, API calls, plans and offline checks.

## Boundaries

- The platform uses VPC `10.42.0.0/16` and the platform Terraform state key.
- A VPC is not an AWS-account boundary.
- This PR does not provision a public customer-ready service without configured
  external identity. Foundation-only resources must not be described as a live
  customer deployment.
- No credential, token, database password or model prompt output is committed.

## Follow-up work

- Configure Google Workspace OIDC and then activate the hosted App Runner
  service through the reviewed service gate.
- Exercise the separate customer-sandbox workload lifecycle in its own PR and
  evidence record.
