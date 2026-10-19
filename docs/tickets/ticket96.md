# ticket96

PR: #96
Branch: `fix/production-runtime-resume`

## Problem / goal

Correct two defects found by the first live authenticated production smoke test: the Terraform
model-provider selector does not match the implemented Bedrock adapter, and an authenticated request
can surface a 500 while Aurora Serverless v2 resumes from zero capacity.

## Current repo state

Production infrastructure and migrations are live. Health, static hosting, exact-origin CORS, JWT
validation, and missing-membership rejection work. Product service construction fails with the
unsupported `bedrock-nova` selector. The first database request after pause also produced an AWS
`DatabaseResumingException` before succeeding on retry once Aurora was awake.

## Research / references used

- Terraform apply run `39272982862`.
- Live Lambda logs for request IDs `8399ea45-53c0-4d77-ade2-3b93b5bfb87f` and
  `5efe1a6b-db99-4f1f-8242-0cf1df3c0749`.
- `apps/api/src/davdeploy/model_gateway.py` supported provider names.
- Aurora Data API `DatabaseResumingException` behavior.

## Work planned for the PR

- Select the implemented `bedrock` model gateway in production Terraform.
- Add a bounded Aurora Data API readiness guard for hosted database-backed requests.
- Convert a database that remains unavailable into a controlled 503 with `Retry-After`.
- Add deterministic regression tests and real AWS evidence.

## Acceptance criteria

- Production constructs the Nova 2 Lite Bedrock adapter.
- Scale-to-zero remains enabled.
- A transient Aurora resume is retried within the API timeout.
- Exhausted resume attempts fail as 503 rather than an unhandled 500.
- Required validation passes and the state-aware plan has no destruction.

## Acceptance status

- [x] Production selects the implemented `bedrock` model gateway.
- [x] Aurora retains minimum capacity zero and the existing 900-second auto-pause setting.
- [x] Transient resume responses are retried through a bounded 20-second backoff budget.
- [x] Exhausted resume attempts return a controlled 503 with `Retry-After`.
- [x] One required clean-room cycle passed.
- [x] The authenticated state-aware plan contains no deletion or replacement.
- [ ] Live deployment and post-apply validation remain follow-up operations after merge.

## Tests / validation performed

- Focused Ruff and Pytest validation passed with 21 tests.
- One complete clean-room cycle passed with all 230 tests.
- All Terraform roots, OpenAPI, Compose, API contract, customer-plan, demo, failure, readiness,
  and trace checks passed.
- Authenticated production state plan: 0 add, 4 in-place changes, 0 delete, 0 replace.

## Evidence files produced

- `docs/test/test96.md`

## Boundaries

This PR does not apply infrastructure. A fresh saved plan and manual apply remain required.

## Follow-up work

Apply the release, rerun authenticated onboarding, validate Nova inference, and inspect alarms.
