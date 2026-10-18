# ticket86: Bootstrap protected Terraform GitHub operations

PR: #86

Branch: `feat/terraform-github-bootstrap`

## Goal

Create or safely adopt the AWS and GitHub prerequisites required by the manual Terraform plan and
apply workflows while leaving the serverless control plane itself unapplied.

## Current repository state

The repository contains manually dispatched plan and apply workflows, older Terraform bootstrap
roots, and historical local state. GitHub currently has no `terraform-plan` or `terraform-apply`
environment. The existing AWS account must be inventoried before deciding which resources can be
reused.

## Research and references

- Existing Terraform bootstrap, identity, and serverless-control-plane roots.
- Existing manual plan and apply workflows.
- Current AWS identity and tagged-resource inventory.
- GitHub Actions OIDC trust and environment configuration requirements.

## Work to be done

- Inventory existing state, lock, artifact, IAM, OIDC, and KMS resources.
- Add a dedicated idempotent Terraform operations bootstrap root or safely extend an existing root.
- Create least-privilege GitHub OIDC plan and apply roles.
- Create private encrypted state, saved-plan, and versioned release storage plus state locking.
- Apply only the bootstrap layer after reviewing its plan.
- Configure the GitHub environments and required variables from verified outputs.
- Validate that manual plan can authenticate and produce a saved plan without applying the control
  plane.
- Record all real AWS mutations and retained resources.

## Acceptance criteria

- Existing suitable resources are reused or their replacement is justified.
- `terraform-plan` and `terraform-apply` environments exist.
- Both environments contain the required non-secret variables.
- GitHub Actions uses short-lived OIDC credentials with branch and environment restrictions.
- State, saved-plan, and release buckets are private and encrypted.
- Release bucket versioning is enabled.
- State locking is available.
- A manual staging plan succeeds and no serverless control-plane apply is run.
- One required clean-room validation cycle passes for the repository changes.

## Acceptance status

Pending inventory, implementation, and validation.

## Validation performed

Pending.

## Evidence files

- `docs/test/test86.md`

## Boundaries

- This work may create low-cost AWS bootstrap resources and GitHub configuration.
- It must not run the serverless control-plane apply workflow.
- It must not create customer workloads.
- It must not add long-lived AWS credentials to GitHub.

## Follow-up work

Review the saved serverless-control-plane plan before separately authorizing any apply.
