# ticket117

PR: #117
Branch: `fix/116-live-response-defects`

## Problem / goal

Live customer validation found that unavailable invitation email delivery persists the expected
failed-delivery evidence but returns an opaque HTTP 500 because the create route does not translate
`InvitationDeliveryUnavailable`. The same run exposed a stray dollar sign in planner recommendation
copy. Return a truthful service-unavailable response and correct the copy.

## Current repo state

Production authentication, invitation listing and cancellation, repository discovery, Nova intent
interpretation, planning, and draft customer review creation work. Invitation delivery remains
deliberately disabled until SES is configured.

## Research / references used

- Authenticated production invitation create/list/cancel responses on 2026-10-21.
- Existing error translation used by invitation resend and onboarding.
- Generated OpenAPI v1 contract and planner recommendation tests.

## Work planned for the PR

- Translate unavailable delivery on invitation creation to HTTP 503.
- Document the 503 response in the route contract.
- Add an API-level regression test that verifies the failed record remains observable.
- Remove the stray dollar sign from recommendation explanations.
- Run focused validation and required GitHub CI.

## Acceptance criteria

- Disabled invitation delivery returns a useful HTTP 503 response rather than HTTP 500.
- The failed invitation remains tenant-visible with `delivery_state=FAILED`.
- OpenAPI documents the unavailable-delivery response.
- Recommendation text is clean and readable.
- No customer infrastructure is deployed or executed.

## Acceptance status

Implementation and focused local validation are complete. Required GitHub CI and the reviewed
production release remain pending.

## Tests / validation performed

Ruff, 49 focused tests, OpenAPI snapshot regeneration, OpenAPI parity, and `git diff --check`
passed. See `docs/test/test117.md`.

## Evidence files produced

- `docs/test/test117.md`

## Boundaries

This is a narrow control-plane response and copy correction. SES activation and customer-cloud
execution remain out of scope.

## Follow-up work

Configure a verified SES sender and production sending access before claiming automatic invitation
email delivery is live.
