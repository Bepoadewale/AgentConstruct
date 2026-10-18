# ticket86: Bootstrap protected Terraform GitHub operations

PR: #86

Branch: `feat/terraform-github-bootstrap`

## Problem / goal

Add and validate the reviewable Terraform needed to create or safely adopt the AWS prerequisites
for manual GitHub plan and apply workflows. Leave both the bootstrap apply and serverless control
plane apply until this PR is merged.

## Current repo state

The repository contains manually dispatched plan and apply workflows, older Terraform bootstrap
roots, and historical local state. GitHub currently has no `terraform-plan` or `terraform-apply`
environment. AWS already has a suitable state bucket, state-lock table, and GitHub OIDC provider.

## Research / references used

- Existing Terraform bootstrap, identity, and serverless-control-plane roots.
- Existing manual plan and apply workflows.
- Current AWS identity and tagged-resource inventory.
- GitHub Actions OIDC trust and environment configuration requirements.

## Work planned for the PR

- Inventoried existing state, lock, artifact, IAM, OIDC, and KMS resources.
- Added a dedicated Terraform operations bootstrap root.
- Defined separate least-privilege GitHub OIDC plan and apply roles.
- Defined private KMS-encrypted saved-plan and versioned release storage.
- Adopted the existing state bucket, lock table, and GitHub OIDC provider as data sources.
- Produced and reviewed an authenticated saved bootstrap plan without applying it.
- Documented the post-merge bootstrap apply and GitHub configuration sequence.

## Acceptance criteria

- Existing suitable resources are reused or their replacement is justified.
- Terraform defines separate plan and apply roles using short-lived GitHub OIDC credentials with
  exact environment restrictions.
- Planned saved-plan and release buckets are private, encrypted, versioned, and lifecycle-limited.
- Existing state storage, state locking, and GitHub OIDC are adopted rather than duplicated.
- The authenticated bootstrap plan contains no destructive changes.
- One required clean-room validation cycle passes for the repository changes.

## Acceptance status

All PR-scoped criteria met. Post-merge creation and GitHub environment configuration remain in the
follow-up operational PR.

## Tests / validation performed

- Existing account `654654474502` inventory verified in `us-east-1`.
- Existing state bucket, lock table, and GitHub OIDC provider verified.
- Authenticated saved bootstrap plan: 25 to add, 0 to change, 0 to destroy.
- One clean-room cycle passed: clean, bootstrap, smoke, simple, complex, degraded, Day-2, policy
  failure, readiness failure, trace check, verify, Terraform validation, clean.
- Full test suite: 224 passed, 1 dependency deprecation warning.

## Evidence files produced

- `docs/test/test86.md`

## Boundaries

- This PR creates no AWS resource.
- The post-merge operational follow-up may create only the low-cost bootstrap resources.
- The serverless control-plane apply workflow must not run.
- Customer workloads must not be created.
- Long-lived AWS credentials must not be added to GitHub.

## Follow-up work

After merge, apply only a newly reviewed bootstrap plan from `main`, configure the two GitHub
environments from its verified outputs, and run the manual staging plan. Record those actions in a
follow-up operational PR. Do not run the serverless control-plane apply.
