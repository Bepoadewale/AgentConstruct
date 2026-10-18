# Manual Terraform plan and apply

AgentConstruct uses two separate, manually dispatched GitHub Actions workflows for its single
production serverless control plane. Merging Terraform code never provisions infrastructure.

## Safety sequence

1. Merge a reviewed PR containing the Terraform change.
2. Manually run **Terraform plan** from `main` with `PLAN_SERVERLESS_CONTROL_PLANE`.
3. Review the complete successful plan run.
4. Without changing `main`, manually run **Terraform apply** with
   `APPLY_SAVED_SERVERLESS_PLAN`.
5. The apply workflow automatically selects the newest manual plan for the exact current `main`
   commit. It verifies that the plan succeeded, checks its workflow path and attempt, downloads its
   encrypted saved plan, verifies its manifest and SHA-256 digest, and applies only that plan.

If `main` changes after planning, apply fails closed. Run and review a new plan from the new commit
before applying.

There is no automatic apply trigger. The apply workflow cannot generate a replacement plan.

## Required GitHub environments

Create `terraform-plan` and `terraform-apply`. Configure required reviewers on
`terraform-apply`. Use separate least-privilege OIDC roles for planning and applying.

Required environment variables:

- `AWS_REGION`
- `EXPECTED_AWS_ACCOUNT_ID`
- `AWS_TERRAFORM_PLAN_ROLE_ARN` for `terraform-plan`
- `AWS_TERRAFORM_APPLY_ROLE_ARN` for `terraform-apply`
- `TF_STATE_BUCKET`
- `TF_STATE_LOCK_TABLE`
- `TF_PLAN_BUCKET`
- `TF_PLAN_KMS_KEY_ARN` for `terraform-plan`
- `TF_RELEASE_BUCKET` for `terraform-plan`
- `TF_RELEASE_KMS_KEY_ARN` for `terraform-plan`
- `FRONTEND_ORIGIN` for `terraform-plan`
- `COGNITO_DOMAIN_PREFIX` for `terraform-plan`; this is the single globally unique production
  Cognito domain prefix

Optional `terraform-plan` variables:

- `GOOGLE_IDENTITY_PROVIDER_ENABLED`, default `false`
- `SES_IDENTITY_ARN`
- `SES_FROM_ADDRESS`
- `BUDGET_NOTIFICATION_EMAIL`

The state, plan, and release buckets must already exist. Enable versioning on the release bucket.
Keep both plan and state buckets private. The plan bucket holds sensitive saved plans and must use
KMS encryption. Do not use GitHub artifacts for saved Terraform plans in this public repository.

## AWS role boundary

Both workflows use GitHub OIDC and short-lived AWS credentials. Do not add access keys to GitHub.
The plan role may read state, acquire the state lock, publish versioned release packages, write
encrypted saved plans, and perform the read permissions Terraform needs. The apply role may read
the selected plan and state, acquire the lock, and change only the approved control-plane resource
scope. Both trust policies should restrict the repository, branch, and GitHub environment. This
repository uses GitHub's immutable OIDC subject customization, which includes owner and repository
numeric IDs. Role trust must use that exact subject rather than a name-only repository subject.

## Current boundary

The prerequisite layer is active. The state bucket, state-lock table, and GitHub OIDC provider were
adopted from the existing account. Dedicated plan and release buckets, KMS keys, and least-privilege
GitHub OIDC roles were then created for these workflows.

Historical staging plan run `39140954204` completed successfully from `main` at commit
`3f4fe983a1b34a91e42967c1057bb723c20bdad9`, but it predates the single-production manifest
contract and cannot be applied. Terraform apply has not been dispatched, so no serverless
control-plane or customer workload resource has been created.

The production workflow uses one remote state object at
`serverless-control-plane/terraform.tfstate`, one canonical `agentconstruct` resource namespace,
and one Cognito domain. Future development or staging environments require a separately reviewed
design change rather than an operator choice in the current workflow.

Google identity federation remains disabled. SES sender configuration and budget notification email
are also unset. These optional integrations can be configured before a future plan when their
provider setup is ready.
