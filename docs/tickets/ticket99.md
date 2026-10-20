# ticket99

PR: #99
Branch: `test/live-customer-journey`

## Problem / goal

Validate the complete supported customer journey against the deployed DavDeploy production control
plane, from Cognito authentication through planning, review, approval, bounded execution,
observation, audit history, and governed teardown.

## Current repo state

The Cloudflare Pages frontend and serverless AWS control plane are deployed. Email OTP, API Gateway
JWT authorization, Aurora Serverless v2 persistence, Nova 2 Lite permissions, the SQS worker,
production alarms, and browser CORS are configured. Google federation and a dedicated SES sender
are intentionally deferred.

## Research / references used

- `AGENTS.md` customer-workload evidence requirements.
- `docs/IMPLEMENTATION_STATUS.md` execution boundaries.
- The versioned OpenAPI contract and production Cognito/API configuration.
- Existing deterministic customer-plan lifecycle tests.

## Work planned for the PR

- Create bounded production test identities and tenant data.
- Authenticate through the deployed Cognito user pool.
- Exercise the deployed planning and recommendation path.
- Submit and decide the exact immutable revision digest.
- Run only the supported bounded dry-run execution path.
- Verify worker completion, outputs, resources, audit records, and governed teardown.
- Remove or deactivate ephemeral test identities and record retained audit data truthfully.

## Acceptance criteria

- Production authentication issues a valid token accepted by the API.
- A customer request produces a persisted architecture recommendation.
- Submission and approval enforce role and exact-digest boundaries.
- Bounded execution reaches an independently observed terminal state.
- Teardown reaches `DESTROYED` without creating customer AWS infrastructure.
- Production audit evidence records the lifecycle.
- No secret, OTP, access token, or customer credential is committed or logged.

## Acceptance status

In progress.

## Tests / validation performed

Pending the controlled production journey.

## Evidence files produced

- `docs/test/test99.md`

## Boundaries

This validates the deployed control plane and its bounded fixture execution adapter. It does not
authorize Terraform apply or creation of a real customer workload in AWS.

## Follow-up work

Record only issues demonstrated by the live run.
