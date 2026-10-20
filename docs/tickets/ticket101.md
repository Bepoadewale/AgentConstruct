# ticket101

PR: #101
Branch: `test/live-customer-journey-evidence`

## Problem / goal

Record the final bounded production customer journey after the Nova extraction correction from PR
#100 was deployed through the reviewed saved-plan workflow.

## Current repo state

The production serverless control plane and frontend are deployed. Authentication, onboarding,
tenant-scoped projects, Aurora persistence, Nova 2 Lite, plan governance, the SQS fixture worker,
observed state, usage, and audit APIs are live. Customer workload provisioning remains disabled.

## Research / references used

- `AGENTS.md` customer-workload evidence requirements.
- The versioned production API contract.
- PR #99 and PR #100 production diagnostics and release evidence.
- Existing customer-plan E2E coverage.

## Work planned for the PR

- Create a typed production intent and architecture plan.
- Create, submit, and independently approve an immutable customer review.
- Verify forbidden developer actions and stale-digest rejection.
- Execute and observe only the bounded fixture environments.
- Create, approve, and execute a governed fixture teardown.
- Verify audit and usage evidence.
- Delete temporary Cognito identities and clean local response artifacts.

## Acceptance criteria

- The complete supported journey reaches governed teardown.
- Role, tenant, and exact-digest boundaries fail closed.
- Audit and usage evidence are observable.
- Temporary identities are removed.
- No customer AWS workload resource is created or deleted.

## Acceptance status

In progress.

## Tests / validation performed

Pending the final production journey.

## Evidence files produced

- `docs/test/test101.md`

## Boundaries

This is a control-plane and bounded fixture-execution test. It does not authorize customer AWS
workload provisioning or a customer-cloud Terraform apply.

## Follow-up work

Record only issues directly demonstrated by this final run.
