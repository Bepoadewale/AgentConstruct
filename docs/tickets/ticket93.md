# ticket93

PR: #93
Branch: `docs/record-davdeploy-runtime-validation`

## Problem / goal

Record the immutable post-rename production configuration results after PR #92 and distinguish the
active DavDeploy deployment path from deliberately retained migration data.

## Current repo state

The active GitHub environments use renamed AWS prerequisites. Terraform plan run `39167209906`
passed from `main`, Cloudflare production deployment `24d20eeb-8622-445a-8c6c-c6e9cddac761`
passed, and the former Cloudflare project was removed after smoke testing the replacement. Terraform
apply has not run.

## Research / references used

- GitHub Actions run `39167209906` and its reviewed `main` commit.
- Cloudflare Pages API result and live-route smoke checks.
- AWS IAM trust-policy, S3 bucket, and DynamoDB table inventories.
- GitHub environment variable and secret inventories.

## Work planned for the PR

- Record the successful renamed manual Terraform plan.
- Record Cloudflare production deployment and route smoke results.
- Document which legacy resources remain and why they are not active.
- Document the post-apply values that cannot truthfully exist yet.

## Acceptance criteria

- The operations guide identifies the successful current plan run.
- Evidence distinguishes created prerequisites and saved-plan artifacts from unapplied runtime
  infrastructure.
- Missing API and OIDC outputs are documented rather than fabricated.
- Documentation conventions and whitespace validation pass.

## Acceptance status

- Pending documentation and validation.

## Tests / validation performed

- Pending.

## Evidence files produced

- `docs/test/test93.md`

## Boundaries

- No Terraform apply is authorized or dispatched.
- No serverless control-plane or customer workload resource is claimed as deployed.
- Legacy stateful AWS resources are retained for recovery.

## Follow-up work

- After an explicitly authorized apply, set the Cloudflare API base URL and OIDC authority/client
  values from real Terraform outputs, then rebuild and test live authentication.
