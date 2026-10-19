# ticket97

PR: #97
Branch: `fix/production-bedrock-observability`

## Problem / goal

Complete live production hardening by authorizing the account-scoped Nova 2 Lite inference profile,
retaining Lambda logs for a bounded period, and creating actionable API, worker, database, and queue
alarms.

## Current repo state

Production onboarding works and the founder membership is administrator. A real intent request
reached Bedrock but returned `AccessDeniedException` because the Lambda role only authorizes
foundation-model resources. The production stack has a $50 monthly budget but does not yet manage
log retention or operational CloudWatch alarms.

## Research / references used

- Live request against API `u885eka88l` on 2026-10-19.
- `aws bedrock get-inference-profile` for `us.amazon.nova-2-lite-v1:0`.
- Existing production Terraform state and Lambda log groups.
- Existing GitHub OIDC plan and apply role policies.

## Work planned for the PR

- Authorize only the selected Nova inference profile and its backing foundation-model family.
- Manage bounded retention for all production Lambda log groups.
- Add CloudWatch alarms for API errors, worker errors, API Gateway 5xx responses, Aurora capacity,
  and dead-letter queue messages.
- Add an SNS email subscription when the existing budget notification address is configured.
- Extend the GitHub Terraform plan and apply roles with the minimum observability permissions.
- Add deterministic contract tests and validation evidence.

## Acceptance criteria

- Live intent interpretation reaches Nova 2 Lite successfully.
- No wildcard Bedrock model family is authorized.
- Production logs have explicit retention.
- Critical failures and unusual database capacity have CloudWatch alarms.
- The email action uses the already configured operator address and requires AWS confirmation.
- The state-aware plan has no destructive changes beyond any explicitly reviewed imports.
- One required clean-room validation cycle passes.

## Acceptance status

Complete in the reviewed branch. Live production validation remains the post-merge release gate.

## Tests / validation performed

- Focused serverless runtime and Terraform contract tests: 15 passed.
- Terraform validation passed before the clean-room cycle.
- One complete clean-room cycle passed, including all demos, API contract, customer-plan E2E,
  tracing, Terraform validation, lint, 232 tests, OpenAPI consistency, and cleanup.
- Authenticated state-aware plans contained no deletes or replacements:
  - operations bootstrap: 0 add, 1 in-place update, 0 destroy;
  - control plane: 4 imports, 8 adds, 6 in-place updates, 0 destroy.

## Evidence files produced

- `docs/test/test97.md`

## Boundaries

This PR does not configure Google OAuth, SES production sending, GitHub App credentials, or Slack.
SNS email delivery remains inactive until the recipient confirms AWS's subscription message.

## Follow-up work

Apply the release, confirm the SNS subscription, and finish the live customer-path smoke test.
