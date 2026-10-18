# Ticket 85: Migrate the hosted control plane to serverless AWS

## Goal

Replace the proposed always-on App Runner and NAT-based hosted runtime with a cost-conscious serverless control plane using API Gateway, Lambda, Aurora Serverless v2 through the RDS Data API, Cognito, SES, SQS, and an isolated policy Lambda.

## Current repo state

The local product is a FastAPI modular monolith with SQLAlchemy persistence, a PostgreSQL-backed job contract, external OPA over HTTP, and trusted OIDC verification. The existing hosted Terraform contract is App Runner-oriented and includes networking that can require a NAT Gateway. No serverless stack has been applied.

## Research and references

- AWS Lambda can call public AWS service APIs and the public internet without joining a customer VPC.
- Aurora PostgreSQL Serverless v2 supports the RDS Data API.
- Cognito choice-based authentication supports email one-time passwords when the user pool uses an eligible feature plan and SES email delivery.
- API Gateway HTTP API JWT authorizers validate Cognito access tokens before Lambda invocation.

## Work planned

- Add Lambda adapters for FastAPI, background work, Cognito identity linking, and policy evaluation.
- Add a bounded Aurora Data API SQLAlchemy adapter while retaining local PostgreSQL and SQLite development.
- Add SQS transport support behind the existing queue boundary.
- Add Cognito user-pool contracts for Google federation and email OTP.
- Add a serverless Terraform root with no NAT Gateway and no Lambda VPC attachment.
- Add explicit CORS, IAM, secret, logging, budget, and deletion-protection boundaries.
- Update API contracts, tests, validation scripts, and operator documentation.
- Keep all AWS changes plan-only and unapplied.

## Acceptance criteria

- [ ] FastAPI runs behind a Lambda adapter.
- [ ] Hosted SQL uses Aurora Serverless v2 Data API without a database socket.
- [ ] Background work has an SQS and DLQ adapter with explicit retries.
- [ ] Policy evaluation runs through an isolated Lambda boundary and fails closed.
- [ ] Cognito supports Google federation and passwordless email OTP without putting secrets in the browser.
- [ ] API Gateway authorizes tokens while the application still resolves server-side membership.
- [ ] Terraform contains no NAT Gateway and does not attach application Lambdas to a VPC.
- [ ] Local behavior and existing contracts remain functional.
- [ ] Static Terraform validation and two clean validation cycles pass.

## Validation performed

Pending implementation.

## Evidence files

No customer workload or AWS apply is planned, so no `docs/test/test85.md` is required.

## Boundaries

- This PR does not apply Terraform, create AWS resources, configure Google credentials, verify SES identities, or claim live authentication.
- Aurora Data API and Cognito behavior require live-environment validation after deployment.
- Tenant membership, roles, approvals, policy, and execution authority remain backend responsibilities.

## Follow-up work

Record exact deployed endpoints, Cognito identifiers, verified SES identities, and live smoke evidence in a later deployment PR.
