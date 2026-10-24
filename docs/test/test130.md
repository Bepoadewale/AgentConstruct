# test130 — Live customer cloud pilot

Date: 2026-10-24
Execution type: Real AWS customer-style execution, partially complete
Customer repository: Pending live private-GitHub onboarding
Commit: Pending repository selection
AWS account: `654654474502`
AWS region: `us-east-1`

## Resources created

- Customer-sandbox VPC, two private subnets, security group, App Runner VPC connector, CloudWatch
  log group and ECR repository, created by the successful foundation apply recorded below.
- No App Runner service has been created.

## Commands executed

- AWS read-only identity, resource-tag, ECR, App Runner, CodeBuild, Lambda, API Gateway, Aurora
  and S3-artifact inspection using the existing scoped operator profile.
- Cognito `USER_AUTH` for the founder account and authenticated `GET /api/v1/me`.
- Authenticated `GET /api/v1/github/connection`,
  `GET /api/v1/admin/customer-plan-revisions`, and `GET /api/v1/cloud-connections`.
- HTTPS checks for the API health endpoint, `davdeploy.tech`, and
  `davdeploy-frontend.pages.dev`.

## Observed result

- AWS account `654654474502`, region `us-east-1`; the API health endpoint returned `200`.
- Cognito founder authentication and `/api/v1/me` returned an administrator identity.
- The founder workspace currently has no customer-plan revisions or cloud connections.
- Its GitHub endpoint reports `execution=SIMULATED`; no GitHub App credentials are configured in
  the production API, so private-repository onboarding is not yet live.
- The existing customer connection ID `0dc9b546-6ec6-4d46-a498-b078d1fc273c` has a successful
  foundation apply run `9187d820-c769-40dd-93ff-01b90f804fd9` and successful image build run
  `70935f5c-1f71-43fc-9d1e-561c2b47f43d`.
- Retained workload resources are the scoped VPC, two private subnets, security group, App Runner
  VPC connector, CloudWatch log group, and ECR repository. No App Runner service exists.
- Cloudflare Pages production deployment is healthy for both `davdeploy.tech` and
  `davdeploy-frontend.pages.dev`.

## Teardown

No teardown command ran. The retained customer-sandbox workload resources require a separately
reviewed saved destroy plan and explicit owner approval after service smoke testing.

## Final boundary

The run uses the customer's scoped connection roles, a reviewed immutable plan digest, an approved
revision, a checksum-bound saved Terraform plan, and the bounded CodeBuild runner. No credentials
or external IDs are included in this record. Private GitHub onboarding, App Runner service apply,
and governed destroy are not claimed as complete.

## Evidence to record before completion

- Customer repository and pinned commit.
- Account and region.
- Plan-only review result and artifact location class.
- Apply result, actual resources, outputs, and observations.
- Separately reviewed destroy-plan result.
- Destroy result and direct absence checks.
- Retained control-plane and customer-connection resources.
- Known limitations, including any fixture-only evidence.

## Current blocker

The existing customer workspace cannot be resumed until authorised customer authentication is
restored. Private GitHub onboarding additionally requires a configured, installed GitHub App.
No claim of private repository discovery, service apply, or destroy is made until those controls
are live and validated.

