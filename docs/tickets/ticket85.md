# ticket85: Migrate the hosted control plane to serverless AWS

PR: #85

Branch: `feat/serverless-control-plane`

## Problem / goal

Replace the proposed always-on App Runner and NAT-based hosted runtime with a cost-conscious
serverless control plane using API Gateway, Lambda, Aurora Serverless v2 through the RDS Data API,
Cognito, SES, SQS, and an isolated policy Lambda. Add Google federation and passwordless email OTP
while keeping tenant membership and roles authoritative in the backend.

## Current repo state

The local product is a FastAPI modular monolith with SQLAlchemy persistence, a PostgreSQL-backed
job contract, external OPA over HTTP, and trusted OIDC verification. The prior hosted Terraform
contract was App Runner-oriented and could require a NAT Gateway. No serverless stack has been
applied.

## Research / references used

- AWS Lambda can call regional AWS APIs without joining a customer VPC.
- Aurora PostgreSQL Serverless v2 supports the RDS Data API.
- Cognito choice-based authentication supports email OTP on an eligible user-pool tier.
- Cognito managed login supports Google federation through OIDC.
- API Gateway HTTP API JWT authorizers validate Cognito tokens before Lambda invocation.
- Saved Terraform plans can contain sensitive values, so this public repository stores them only
  in a private KMS-encrypted S3 bucket rather than GitHub artifacts.

## Work planned for the PR

- Add Lambda adapters for FastAPI, background work, Cognito identity linking, and policy checks.
- Add Aurora Data API persistence while retaining local PostgreSQL and SQLite development.
- Add SQS wake-up and dead-letter contracts behind the existing worker boundary.
- Add Cognito user-pool contracts for Google federation and email OTP.
- Add a serverless Terraform root with no NAT Gateway and no application Lambda VPC attachment.
- Add exact CORS, IAM, logging, budget, secret, deletion-protection, and artifact boundaries.
- Add separate manual Terraform plan and apply workflows. Apply must consume the exact successful
  saved plan selected by run ID and can never trigger automatically.
- Reduce the repository clean-room rule to one complete clean cycle.
- Update contracts, tests, validation scripts, operator documentation, and deployment handoff.

## Acceptance criteria

- [x] FastAPI runs behind a Lambda adapter.
- [x] Hosted SQL uses Aurora Serverless v2 Data API without a database socket.
- [x] Background work has SQS and DLQ behavior with explicit retry boundaries.
- [x] Policy evaluation runs through an isolated Lambda boundary and fails closed.
- [x] Cognito supports Google federation and passwordless email OTP without browser secrets.
- [x] API Gateway authorizes tokens while the application resolves server-side membership.
- [x] Terraform contains no NAT Gateway and does not attach application Lambdas to a VPC.
- [x] Manual Terraform plan and apply are separate, and apply uses only a verified saved plan.
- [x] Local behavior and existing contracts remain functional.
- [x] Static Terraform validation and one clean validation cycle pass.

## Acceptance status

All code acceptance criteria are met locally. Live AWS, Cognito, Google, SES, Data API, plan, and
apply behavior remains intentionally unexecuted until the required accounts, roles, buckets,
identities, and GitHub environments are configured.

## Tests / validation performed

- Two complete clean cycles passed before the rule changed, each ending with 216 passing tests.
- The required current gate is one clean cycle and is therefore satisfied.
- Canonical, simple, complex, degraded, Day-2, policy-failure, readiness-failure, customer-plan,
  seed, tracing, lint, test, OpenAPI, and Compose checks passed in each cycle.
- `make terraform-validate` passed for every Terraform root.
- The Lambda package built and its ZIP integrity was checked during CI-oriented validation.
- Workflow syntax and final repository checks are rerun after the governance additions.

## Evidence files produced

- `docs/test/test85.md`
- `docs/SERVERLESS_DEPLOYMENT.md`
- `docs/TERRAFORM_GITHUB_OPERATIONS.md`

## Boundaries

- This PR does not apply Terraform, create AWS resources, configure Google credentials, verify SES
  identities, or claim live authentication.
- Aurora Data API and Cognito require live validation after deployment.
- Tenant membership, roles, approvals, policy, and execution authority remain backend concerns.
- Manual workflows remain unusable until least-privilege OIDC roles and private encrypted state,
  plan, and release buckets are configured.

## Follow-up work

Configure GitHub environments and AWS OIDC roles, run the manual plan, review its exact cost and
resource changes, then manually apply its saved plan. Record deployed endpoints, Cognito IDs, SES
identity, Google configuration, live auth smoke results, and teardown evidence in a deployment PR.
