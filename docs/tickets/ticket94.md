# ticket94

PR: #94
Branch: `fix/serverless-apply-reconciliation`

## Problem / goal

Correct the two verified blockers from production apply run `39269651252`, preserve its partial
Terraform state, and prepare a safe reconciliation plan.

## Current repo state

The guarded apply created and recorded a subset of the approved resources, then stopped. AWS no
longer offers Aurora PostgreSQL `16.6` in `us-east-1`, and API Gateway rejected tag creation because
the apply role only allowed `/apis*`, not the separate `/tags/*` endpoint. Terraform recorded the
successful resources in the production remote state.

## Research / references used

- Failed GitHub Actions apply run `39269651252`.
- Live `DescribeDBEngineVersions` and `DescribeOrderableDBInstanceOptions` results from AWS in
  `us-east-1`.
- Current serverless control-plane and Terraform operations-bootstrap configuration.
- Production Terraform state and GitHub OIDC role boundary.

## Work planned for the PR

- Pin an available Aurora PostgreSQL 16 Serverless v2 version.
- Add the minimum API Gateway tag endpoint permission required for tagged API creation.
- Add regression coverage for both deployment assumptions.
- Record the failed apply and reconciliation evidence truthfully.
- Run the repository validation gate before merge.

## Acceptance criteria

- Aurora uses an orderable PostgreSQL 16 Serverless v2 version in `us-east-1`.
- The apply role can tag only the API Gateway scope needed by this stack.
- Static tests detect regression of both fixes.
- Existing successful resources remain in Terraform state and are not recreated blindly.
- Required CI passes before merge.

## Acceptance status

- Met for the reviewed repository change. Post-merge bootstrap reconciliation, saved planning, and
  apply remain controlled operational steps.

## Tests / validation performed

- Focused Terraform regression suite: 15 tests passed.
- `make terraform-validate`: every Terraform root passed.
- `make verify`: Ruff, 227 Pytest tests, OpenAPI snapshot, and Compose validation passed.
- A real read-only plan against the partial production state proposed 14 additions, zero changes,
  and zero deletions.

## Evidence files produced

- `docs/test/test94.md`

## Boundaries

- This PR does not apply infrastructure.
- Reconciliation apply occurs only from a fresh post-merge saved plan.
- No state surgery, manual resource deletion, or blind retry is permitted.

## Follow-up work

- Apply the operations-bootstrap update after merge.
- Run and review a fresh production plan, then manually approve its saved apply.
- Continue frontend connection and production validation only after successful reconciliation.
