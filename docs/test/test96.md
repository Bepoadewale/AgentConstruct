# test96

Date: 2026-10-19
Execution type: Local clean-room validation, deterministic regression tests, and authenticated AWS
state inspection
Customer repository: Local davdeploy fixture workflows
Commit: `fix/production-runtime-resume` worktree before final evidence commit
AWS account: 654654474502
AWS region: us-east-1

## Scope

This evidence covers the production runtime correction for the Bedrock provider selector and the
bounded Aurora Serverless v2 resume guard. No infrastructure was applied by this PR validation.

## Resources created

- Ephemeral local Compose containers, network, PostgreSQL volume, and validation files.
- No AWS resources.

## Commands executed

```text
make clean-local
make bootstrap-local
make smoke
make demo-simple
make demo-complex
make demo-day2
make demo-degraded
make demo-failure
make demo-readiness-failure
make api-contract
make customer-plan-e2e
make trace-check
make terraform-validate
make verify
make clean-local
```

The AWS state inspection also ran `terraform init`, `terraform state show`, `terraform plan`, and
`terraform show` against the existing production backend with profile `ai-platform-pilot-key`.

## Observed result

- All services became ready from a clean bootstrap.
- Simple, complex, Day-2, degraded, policy-failure, readiness-failure, API contract,
  customer-plan, and trace checks passed.
- All Terraform roots validated.
- Ruff passed.
- All 230 tests passed, including deterministic Aurora resume, exhaustion, 503 response, and
  Bedrock provider-selector regressions.
- The OpenAPI snapshot and Compose configuration matched.
- Final cleanup removed project containers, network, volume, virtual environment, and local state.
- One upstream Starlette `httpx` deprecation warning remained and did not affect results.

## Authenticated AWS state inspection

The production state was refreshed using AWS profile `ai-platform-pilot-key` and the existing
remote state backend. The plan reused the currently deployed immutable Lambda object so that it
could isolate Terraform configuration changes before merge.

Observed plan:

```text
Plan: 0 to add, 4 to change, 0 to destroy.
create: 0
update: 4
delete: 0
replace: 0
```

The changes were in-place Lambda environment updates from `bedrock-nova` to `bedrock`, plus an
AWS Budgets notification normalization caused by the locally supplied address. No AWS resource was
created, updated, or deleted because the saved local plan was not applied.

## Teardown

`make clean-local` removed the local containers, network, PostgreSQL volume, virtual environment,
and local application state. The local Terraform plan was not applied.

## Final boundary

This evidence does not prove the new Lambda package in production. That requires merge, a fresh
GitHub OIDC Terraform plan, a separately approved manual apply, and a live authenticated smoke test.
