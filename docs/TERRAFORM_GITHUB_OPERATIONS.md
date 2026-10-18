# Manual Terraform plan and apply

AgentConstruct uses two separate, manually dispatched GitHub Actions workflows for the serverless
control plane. Merging Terraform code never provisions infrastructure.

## Safety sequence

1. Merge a reviewed PR containing the Terraform change.
2. Manually run **Terraform plan** from `main` with `PLAN_SERVERLESS_CONTROL_PLANE`.
3. Review the complete successful plan run and copy its run ID and run attempt.
4. Manually run **Terraform apply** from `main` with that run ID, run attempt, and
   `APPLY_SAVED_SERVERLESS_PLAN`.
5. The apply workflow verifies that the selected run was a successful manual plan from `main`,
   checks its workflow path and attempt, checks out its exact commit, downloads its encrypted saved
   plan, verifies its SHA-256 digest, and applies only that plan.

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
- `COGNITO_DOMAIN_PREFIX` for `terraform-plan`; the workflow appends `-staging` or `-production`
  so both environments have globally distinct Cognito domains

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
scope. Both trust policies should restrict the repository, branch, and GitHub environment.

## Current boundary

These workflows are implementation only. They have not been dispatched, and no AWS resource was
created or changed by this PR.
