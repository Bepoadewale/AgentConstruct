# ticket124: Grant the reviewed executor project permission

PR: #124
Branch: fix/codebuild-executor-bootstrap-permission

## Problem / goal

The reviewed control-plane Terraform apply stopped before creating the bounded CodeBuild customer executor because the GitHub apply role does not have CodeBuild project-management permission.

## Current repo state

PR #123 is merged. Its saved plan ran successfully and its apply safely created the executor role and policy, then failed on `codebuild:CreateProject`. No customer workload resource was created.

## Research / references used

- The failed GitHub Actions apply log for run `39898200552`.
- Existing least-privilege `terraform-operations-bootstrap` apply-role policy.

## Work planned for the PR

- Permit only the DavDeploy customer executor CodeBuild project lifecycle required by the reviewed control-plane Terraform.
- Validate the bootstrap Terraform root and record the reviewed local plan before apply.

## Acceptance criteria

- [ ] The apply role can create, update, tag, untag, and delete only the bounded executor project.
- [ ] The bootstrap plan is reviewed before it is applied.
- [ ] The control-plane saved-plan apply can resume without broad administrator access.

## Acceptance status

Implemented and locally validated. The reviewed bootstrap plan changes one inline policy only; merge and exact saved-plan application remain pending.

## Tests / validation performed

- `terraform -chdir=infrastructure/terraform/terraform-operations-bootstrap fmt -check -recursive`
- `terraform -chdir=infrastructure/terraform/terraform-operations-bootstrap init -backend=false -input=false`
- `terraform -chdir=infrastructure/terraform/terraform-operations-bootstrap validate`
- `python3 scripts/check_doc_conventions.py`
- Authenticated remote plan using the production bootstrap state, saved at `/tmp/davdeploy-bootstrap-permission.tfplan`: 0 add, 1 change, 0 destroy.

## Evidence files produced

- `docs/tickets/ticket124.md`
- `docs/test/test124.md`

## Boundaries

This PR changes only the GitHub apply role. It does not enable customer execution or create a customer workload.

## Follow-up work

- Re-run the saved control-plane plan, then apply it only after review.
