# ticket100

PR: #100
Branch: `test/complete-live-customer-journey`

## Problem / goal

Complete the bounded production customer journey after release of the Nova intent repair from PR
#99. Verify planning, immutable review, independent approval, execution, observation, audit, and
governed teardown through the deployed API.

## Acceptance criteria

- Nova produces a persisted typed workload intent.
- The developer receives and reviews an architecture recommendation.
- Submission and approval enforce role and exact-digest boundaries.
- Local fixture execution reaches an independently observed terminal state.
- Governed teardown reaches `DESTROYED`.
- Production audit evidence and usage metering record the lifecycle.
- Temporary Cognito identities are removed.
- No customer AWS workload resources are created.

## Tests / validation performed

- The first post-release production request demonstrated that Nova returned `null` for a required
  boolean capability field on both attempts. The API failed closed with HTTP 503 and persisted no
  false intent or plan.
- A direct call using the same model, generic request, and revised extraction instruction produced
  a valid typed proposal. The instruction now distinguishes nullable fields, absent boolean
  requirements, and missing lists.
- One clean-room repository cycle passed all canonical demos, API contract, customer-plan E2E,
  trace verification, Terraform validation, lint, 234 tests, OpenAPI drift checking, and cleanup.
- Pending continuation of the controlled production journey after governed release.

## Evidence files produced

- `docs/test/test100.md`

## Boundaries

The production control plane is live, but execution remains the bounded fixture adapter. This test
does not authorize Terraform-based creation of customer workload infrastructure.
