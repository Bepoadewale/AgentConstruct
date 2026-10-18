# ticket92

PR: #92
Branch: `chore/davdeploy-runtime-configuration`

## Problem / goal

Finish the operational side of the DavDeploy rename after PR #91 by correcting secret
classification, aligning operator guidance with the current input-free saved-plan selection, and
recording the verified production prerequisite migration.

## Current repo state

The repositories and current source use the DavDeploy name. New AWS state, locking, saved-plan,
release, KMS, and GitHub OIDC prerequisites have been created without modifying or destroying the
old recoverable resources. GitHub environment variables now point at the new prerequisites. The
plan summary still tells operators to provide a plan run ID even though apply now selects it
automatically, and the optional notification address is still modeled as a public variable.

## Research / references used

- Repository `AGENTS.md` and Terraform operations documentation.
- Current `terraform-plan` and `terraform-apply` workflow contracts.
- Verified AWS prerequisite outputs in account `654654474502`, region `us-east-1`.
- Verified GitHub environment configuration for `terraform-plan` and `terraform-apply`.

## Work planned for the PR

- Read the budget notification address from an encrypted GitHub environment secret.
- Remove obsolete plan-run-ID instructions from the Terraform plan summary.
- Document the exact active DavDeploy prerequisite names and the retained legacy boundary.
- Run focused workflow, documentation, secrets, and Terraform validation.
- Run and record one real manual Terraform plan after merge, without dispatching apply.

## Acceptance criteria

- Sensitive notification configuration is not stored as a public GitHub variable.
- Plan and apply instructions match the current automatic saved-plan selection.
- Documentation truthfully identifies active and retained prerequisite resources.
- Static validation passes before merge.
- The post-merge manual plan authenticates with the renamed OIDC role and creates no control-plane
  resources.

## Acceptance status

- Met for the reviewed repository change. The post-merge manual plan remains the final external
  validation step and will be added to `docs/test/test92.md` through a follow-up PR if its immutable
  run result must be recorded in-repository.

## Tests / validation performed

- `make install`
- `make verify`: Ruff, 226 Pytest tests, OpenAPI snapshot, and Compose validation passed.
- `make terraform-validate`: every Terraform root passed.
- PR #92 documentation conventions passed.
- Every GitHub workflow parsed as YAML and `git diff --check` passed.

## Evidence files produced

- `docs/test/test92.md`

## Boundaries

- This PR does not dispatch Terraform apply.
- It does not create the serverless control plane or customer workload resources.
- Google OAuth and SES values remain unset until those provider resources exist.
- Legacy stateful prerequisites remain recoverable and are not deleted in this change.

## Follow-up work

- Configure post-deployment frontend API and OIDC values after a separately authorized apply.
- Review legacy prerequisite retirement only after the new production workflow is proven.
