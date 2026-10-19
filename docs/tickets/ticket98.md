# ticket98

PR: #98
Branch: `fix/production-cors-preflight`

## Problem / goal

Allow browser CORS preflight requests to reach the production API without JWT authorization while
keeping every non-health application request behind the Cognito authorizer.

## Current repo state

The HTTP API secures its `$default` route with JWT authorization. Live launch validation found that
the route also captures `OPTIONS` requests and returns `401`, even though the response contains the
correct CORS headers. This prevents browsers from issuing authenticated cross-origin API requests.

## Research / references used

- Live `OPTIONS /api/v1/dashboard` request from the production Pages origin on 2026-10-19.
- Existing HTTP API CORS and JWT route configuration.
- AWS HTTP API route precedence for explicit routes over `$default`.

## Work planned for the PR

- Add explicit unauthenticated `OPTIONS /` and `OPTIONS /{proxy+}` routes.
- Continue forwarding preflight requests through the API Lambda and its CORS middleware.
- Add deterministic Terraform contract coverage.
- Run the required one-cycle validation gate and a state-aware production plan.

## Acceptance criteria

- Production preflight returns a successful response for the exact Pages origin.
- Preflight advertises the intended methods and request headers.
- Non-preflight application routes remain JWT protected.
- The reviewed Terraform plan has no deletion or replacement.
- One clean-room validation cycle passes.

## Acceptance status

Complete in the reviewed branch. Live production validation remains the post-merge release gate.

## Tests / validation performed

- State-aware production plan: 2 adds, 0 changes, 0 destroys or replacements.
- One clean-room cycle passed, including all demos, API contract, customer-plan E2E, tracing,
  Terraform validation, lint, 233 tests, OpenAPI consistency, and cleanup.

## Evidence files produced

- `docs/test/test98.md`

## Boundaries

The unauthenticated routes accept only `OPTIONS`. Backend JWT authorization continues to protect
all application data and mutations.

## Follow-up work

Merge, run the governed production plan and apply, then repeat live preflight and authenticated API
smoke tests.
