# ticket111

PR: #111
Branch: `fix/110-guarded-release-migrations`

## Problem / goal

The guarded Terraform apply workflow deploys the dedicated migration Lambda but does not invoke
it. After the invitation release, production code expected schema version 20 while Aurora remained
on version 19, so the live invitation list returned HTTP 500. Make migration completion a required
part of every manually approved control-plane apply.

## Current repo state

Terraform exposes `migration_function_name`, and the Lambda returns
`{"status":"migrations-complete"}` after running versioned migrations. The documented release
sequence requires that result, but the workflow stops immediately after `terraform apply`.

## Research / references used

- Existing dedicated `davdeploy.lambda_migrate` handler.
- Existing single-production saved-plan workflow and OIDC apply role.
- AWS Lambda invocation response contract, including `FunctionError`.

## Work to be done

- Give the apply role narrowly scoped invocation permission for only the migration Lambda.
- Invoke the function after the saved Terraform plan is applied.
- Fail the workflow on a Lambda function error or a missing completion response.
- Update release documentation and regression tests.
- Apply the reviewed release, confirm migration completion, then rerun the live customer journey.

## Acceptance criteria

- Plan and apply remain separate, manual workflows.
- The apply workflow invokes migrations only after applying the reviewed saved plan.
- Migration invocation is scoped to the dedicated migration function.
- Missing or failed migration confirmation fails the release.
- The production invitation list succeeds after deployment.
- No customer workload is deployed or executed.

## Acceptance status

All implementation and local acceptance criteria are met. GitHub CI and the reviewed production
plan/apply release remain before the live acceptance checks can be marked complete.

## Validation performed

Focused tests and one complete clean-room cycle passed. See `docs/test/test111.md`.

## Evidence files

- `docs/test/test111.md`

## Boundaries

This change migrates only the DavDeploy control-plane database. It does not submit, approve,
provision, change, or destroy customer infrastructure.

## Follow-up work

None identified yet.
