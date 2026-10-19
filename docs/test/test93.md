# test93

Date: 2026-10-19
Execution type: Real AWS Terraform plan and live Cloudflare Pages static deployment validation
Customer repository: No customer workload repository; DavDeploy control-plane and frontend
repositories only
Commit: Backend `5c03b37ab1a46cd96a55a5a7e888167badfc8b3b`; frontend
`38e74a0f9fc1f7ea953179a758d7c224524a5301`
AWS account: `654654474502`
AWS region: `us-east-1`

## Resources created

- GitHub Actions plan run `39167209906` uploaded one immutable, versioned Lambda release package.
- The run uploaded one encrypted saved Terraform plan and its manifest.
- Cloudflare Pages production deployment `24d20eeb-8622-445a-8c6c-c6e9cddac761` rebuilt the static
  frontend from the renamed repository with known production public configuration.
- No serverless control-plane or customer workload resource was created.

## Commands executed

```text
gh workflow run terraform-plan.yml --repo Bepoadewale/davdeploy --ref main \
  -f confirmation=PLAN_SERVERLESS_CONTROL_PLANE
gh run watch 39167209906 --repo Bepoadewale/davdeploy --exit-status
Cloudflare Pages API production deployment for branch main
HTTP smoke checks for /, /login, and /plans/new
Production JavaScript configuration check for the callback origin and Cognito region
AWS IAM trust-policy inventory after migration cleanup
```

## Observed result

- Terraform plan passed in 48 seconds using GitHub OIDC and the renamed plan role.
- The plan workflow validated the expected AWS account before publishing or planning.
- Terraform apply was not dispatched.
- Cloudflare completed the production deployment successfully.
- `/`, `/login`, and `/plans/new` each returned HTTP 200 and contained the DavDeploy brand.
- The production bundle contained `https://davdeploy-frontend.pages.dev/auth/callback` and
  `us-east-1`.
- The former Cloudflare Pages project returned HTTP 404 after removal.
- Legacy IAM roles no longer trust the renamed repository. Their former-name subjects are inert
  after the repository rename.

## Teardown

The obsolete `agentconstruct-frontend` Cloudflare Pages project was removed after the DavDeploy
replacement passed deployment and smoke checks. Its Pages deployments are not recoverable, but all
source and Git history remain in `Bepoadewale/davdeploy-frontend`.

Legacy AWS state, lock, saved-plan, release, and KMS resources were not deleted. They remain isolated
from active GitHub environments for a separately reviewed archival or retirement decision.

## Final boundary

This evidence proves the renamed GitHub OIDC plan path, encrypted plan publication, Cloudflare
static deployment, and live unauthenticated route delivery. It does not prove Terraform apply,
serverless API availability, Cognito sign-in, Google federation, SES delivery, database operation,
or customer-cloud execution.
