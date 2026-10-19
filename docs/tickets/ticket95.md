# ticket95

PR: #95
Branch: `fix/apply-managed-secret-and-stage-tags`

## Problem / goal

Add the two narrowly scoped permissions required by the second production reconciliation apply and
preserve all successfully created resources in Terraform state.

## Current repo state

Apply run `39271445733` created the API Gateway HTTP API and JWT authorizer and updated the two
existing Lambda packages. It then stopped because the apply role could not create Aurora's
AWS-managed master-password secret or tag the API Gateway stage.

## Research / references used

- Failed GitHub Actions apply run `39271445733`.
- Current Terraform operations-bootstrap role policy.
- AWS resource ARNs returned in the authorization failures.
- Production Terraform state after the failed-closed run.

## Work planned for the PR

- Permit API Gateway stage tag and untag operations within the existing DavDeploy API scope.
- Permit lifecycle operations only for RDS-managed cluster secrets.
- Add regression assertions for the exact action and resource boundaries.
- Record real AWS evidence and validate all Terraform roots and tests.

## Acceptance criteria

- The apply role can tag managed API Gateway resources without broad unrelated access.
- The apply role can create the RDS-managed master secret within its service name pattern.
- Regression tests enforce both boundaries.
- Existing partial resources remain managed and no destroy is proposed.
- Required CI passes before merge.

## Acceptance status

- Met. The scoped permissions and regression assertions are implemented, all repository checks
  pass, and a state-aware plan proposes 12 additions with no changes or destruction.

## Tests / validation performed

- `pytest -q tests/test_terraform_operations_bootstrap.py tests/test_serverless_runtime.py`: 15 passed.
- `make terraform-validate`: every Terraform root valid.
- `make verify`: Ruff passed, 227 tests passed, OpenAPI matched, and Compose validated.
- State-aware production `terraform plan`: 12 to add, 0 to change, 0 to destroy.
- `git diff --check` and PR document conventions are checked before review readiness.

## Evidence files produced

- `docs/test/test95.md`

## Boundaries

- This PR does not apply infrastructure.
- The next apply must use a fresh post-merge saved plan.
- No manual state edits or resource deletions are permitted.

## Follow-up work

- Apply the operations-bootstrap policy update.
- Run and review a fresh state-aware production plan and apply.
