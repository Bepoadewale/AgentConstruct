# ticket103

PR: #103
Branch: `test/final-live-customer-journey`

## Problem / goal

Record a fresh, complete authenticated production journey after the profile-aware bounded fixture
executor was merged and deployed.

## Current repo state

Production runs the serverless control plane at main commit
`4910d57dc67bda27f7bb0c6cc521610632a93a59`. Terraform plan run `39417977019` reported zero
additions, five in-place Lambda updates, and zero deletions. Apply run `39418139543` succeeded.

## Research / references used

- `AGENTS.md` customer workload evidence requirements.
- PR #101 original live customer journey and worker correction.
- PR #102 profile-aware fixture metadata correction.
- Production API and Cognito configuration from the reviewed Terraform state.

## Work planned for the PR

- Create temporary, separate developer and administrator identities.
- Complete onboarding, intent interpretation, planning, review, submission, and approval.
- Verify unauthorized and stale-digest actions fail closed.
- Execute and observe bounded staging and production fixture environments.
- Verify Lambda-profile outputs contain no App Runner metadata.
- Complete governed teardown, audit, and usage verification.
- Delete temporary identities and local response artifacts.

## Acceptance criteria

- The complete supported journey reaches governed teardown.
- Role, tenant, and exact-digest boundaries fail closed.
- Both fixture environments reach READY with Lambda resource metadata.
- Both environments and all observed records reach DESTROYED.
- Audit and usage records are observable.
- Temporary identities and local response artifacts are removed.
- No customer cloud workload is created or deleted.

## Acceptance status

Complete. The final production journey passed every acceptance criterion. Two earlier harness
attempts failed only in test-side polling and response-shape assertions. Their four fixture
environments were recovered through the governed teardown APIs and independently verified as
DESTROYED with cleanup evidence.

## Tests / validation performed

- Verified the live Cognito, API Gateway, Lambda, Aurora Data API, SQS, EventBridge, Bedrock Nova,
  policy, approval, audit, and metering path.
- Verified cross-tenant access, developer approval, and stale plan-digest attempts fail closed.
- Verified the selected `aws-lambda-api` profile produces `lambda_function` metadata and no App
  Runner metadata.
- Verified staging and production reach READY, then DESTROYED through their respective governed
  teardown paths.
- Verified every Live QA 103 environment from all attempts is DESTROYED with
  `cleanup_verified=true`.
- Verified Cognito contains zero `qa103-*` temporary users.

## Evidence files produced

- `docs/test/test103.md`

## Boundaries

This is a real production control-plane test with deterministic fixture execution. It does not
authorize Terraform apply or workload provisioning in a customer cloud account.

## Follow-up work

None for this ticket.
