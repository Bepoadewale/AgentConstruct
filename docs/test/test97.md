# test97

Date: 2026-10-19
Execution type: Local clean-room validation, deterministic regression tests, and authenticated AWS
state inspection
Customer repository: Local davdeploy fixture workflows
Commit: `fix/production-bedrock-observability` worktree before final evidence commit
AWS account: 654654474502
AWS region: us-east-1

## Scope

This evidence covers exact Nova 2 Lite authorization, bounded Lambda log retention, and production
alarms and notifications. No infrastructure was applied during PR validation.

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

Focused tests and authenticated AWS state inspection also ran `pytest`, `terraform init`,
`terraform plan`, and `terraform show` against the existing production state with profile
`ai-platform-pilot-key`.

## Observed result

- All services became ready from a clean bootstrap.
- Simple, complex, Day-2, degraded, policy-failure, readiness-failure, API contract,
  customer-plan, and trace checks passed.
- All Terraform roots validated and Ruff passed.
- All 232 tests passed, including deterministic Bedrock resource-scope, log-retention, and alarm
  regressions.
- The OpenAPI snapshot and Compose configuration matched.
- Final cleanup removed project containers, network, volume, virtual environment, and local state.
- One upstream Starlette `httpx` deprecation warning remained and did not affect results.

Authenticated state-aware plans reported:

```text
operations bootstrap: 0 add, 1 change, 0 destroy
serverless control plane: 4 imports, 8 add, 6 change, 0 destroy
```

The four imports adopt existing automatically created Lambda log groups. The additions are the
previously absent policy Lambda log group, one SNS topic, one pending email subscription, and five
CloudWatch alarms. The in-place changes update IAM, Lambda dependencies, log retention and tags.
Neither plan contained a replacement or deletion.

## Teardown

`make clean-local` removed the local containers, network, PostgreSQL volume, virtual environment,
and local application state. Neither authenticated Terraform plan was applied.

## Final boundary

This evidence does not prove live Nova inference or alarm delivery. Those checks require merge, a
fresh GitHub OIDC plan, a separately approved manual apply, an authenticated production smoke test,
and recipient confirmation of the SNS email subscription.
