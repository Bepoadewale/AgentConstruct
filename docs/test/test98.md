# test98

Date: 2026-10-19
Execution type: Local clean-room validation and authenticated AWS state inspection
Customer repository: Local davdeploy fixture workflows
Commit: `fix/production-cors-preflight` worktree before final evidence commit
AWS account: 654654474502
AWS region: us-east-1

## Scope

This evidence covers explicit unauthenticated HTTP API preflight routes while retaining JWT
authorization on the application default route. No infrastructure was applied during PR validation.

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

Authenticated AWS state inspection also ran `terraform init`, `terraform state show`, `terraform
plan`, and `terraform show` against the production backend with profile
`ai-platform-pilot-key`.

## Observed result

- All services became ready from a clean bootstrap.
- Simple, complex, Day-2, degraded, policy-failure, readiness-failure, API contract,
  customer-plan, and trace checks passed.
- All Terraform roots validated and Ruff passed.
- All 233 tests passed, including explicit preflight route and retained JWT boundary coverage.
- The OpenAPI snapshot and Compose configuration matched.
- Final cleanup removed project containers, network, volume, virtual environment, and local state.
- One upstream Starlette `httpx` deprecation warning remained and did not affect results.

The authenticated state-aware plan reported:

```text
Plan: 2 to add, 0 to change, 0 to destroy.
```

The two additions are `OPTIONS /` and `OPTIONS /{proxy+}` API Gateway routes with authorization
type `NONE`. The existing `$default` route remains the only JWT-authorized route. The plan contained
no replacement or deletion.

## Teardown

`make clean-local` removed the local containers, network, PostgreSQL volume, virtual environment,
and local application state. The authenticated Terraform plan was not applied.

## Final boundary

This evidence does not prove browser preflight against production. That requires merge, a fresh
GitHub OIDC plan, a separately approved manual apply, and a live request from the Pages origin.
