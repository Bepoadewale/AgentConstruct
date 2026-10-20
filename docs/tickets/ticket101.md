# ticket101

PR: #101
Branch: `test/live-customer-journey-evidence`

## Problem / goal

Record the final bounded production customer journey after the Nova extraction correction from PR
#100 was deployed through the reviewed saved-plan workflow.

## Current repo state

The production serverless control plane and frontend are deployed. Authentication, onboarding,
tenant-scoped projects, Aurora persistence, Nova 2 Lite, plan governance, observed state, usage,
and audit APIs are live. The production run showed that the SQS worker still selected the local
Docker-only HTTP fixture hostname, so queued dry runs could not complete in Lambda. Customer
workload provisioning remains disabled.

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
- Replace the Lambda worker's Docker-only fixture transport with a bounded, stateless embedded
  fixture adapter selected explicitly by hosted Terraform configuration.
- Ensure stateless teardown marks every previously observed output and resource as destroyed.

## Acceptance criteria

- The complete supported journey reaches governed teardown.
- Role, tenant, and exact-digest boundaries fail closed.
- Audit and usage evidence are observable.
- Temporary identities are removed.
- No customer AWS workload resource is created or deleted.

## Acceptance status

In progress.

## Tests / validation performed

- Focused Ruff check passed.
- Focused executor, serverless-runtime, and product tests passed: 48 tests.
- One full clean-room cycle passed: clean, bootstrap, smoke, API contract, customer-plan E2E,
  simple, complex, degraded, Day-2, canonical, policy-failure, readiness-failure, trace, Ruff,
  236 tests, OpenAPI drift, Compose configuration, OPA 3/3, Terraform validation, final clean.

## Evidence files produced

- `docs/test/test101.md`

## Boundaries

This is a control-plane and bounded fixture-execution test. It does not authorize customer AWS
workload provisioning or a customer-cloud Terraform apply.

## Follow-up work

Deploy the reviewed worker correction, resume the queued production fixture jobs, and complete the
governed teardown and final live evidence.
