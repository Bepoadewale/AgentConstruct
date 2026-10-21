# ticket109

PR: #109
Branch: `feat/108-invitation-delivery`

## Problem / goal

Workspace invitations are securely accepted, but production does not deliver the invitation link
and administrators cannot inspect, resend, or cancel invitations. Complete that lifecycle with a
bounded Amazon SES adapter.

## Current repo state

The backend creates a tenant-scoped, expiring, hashed invitation token and validates the verified
recipient email during onboarding. The raw token is returned only by the local fixture.

## Research / references used

- Existing Cognito verified-email onboarding and invitation acceptance contract.
- Amazon SES v2 `SendEmail` API and identity-scoped IAM authorization.
- Existing serverless runtime variables for a verified SES identity and From address.

## Work planned for the PR

- Add an SES invitation adapter and deterministic local fixture.
- Track delivery status, provider, send count, and lifecycle timestamps.
- Add tenant-scoped administrator list, resend, and cancel endpoints.
- Rotate the raw token on every resend and never return it from hosted execution.
- Add migration, OpenAPI, IAM, runtime configuration, tests, and operating documentation.

## Acceptance criteria

- Hosted invitation links are delivered only through the configured verified SES identity.
- Failed delivery is explicit and remains recoverable through resend.
- Resend rotates the token and refreshes expiry.
- Cancelled and accepted invitations cannot be reused or resent.
- Non-administrators and other tenants cannot inspect or mutate invitations.
- No customer cloud infrastructure is created.

## Acceptance status

Implementation is complete. Clean-room and CI evidence are recorded in the paired test file.
Live delivery requires a verified SES sender and production sending access.

## Tests / validation performed

See `docs/test/test109.md`.

## Evidence files produced

- `docs/test/test109.md`

## Boundaries

The email adapter sends one transactional invitation. It has no customer-cloud, repository,
approval, planning, or execution authority.

## Follow-up work

Verify the selected sender identity and obtain SES production sending access before inviting
unverified external recipients.
