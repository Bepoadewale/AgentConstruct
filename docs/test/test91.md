# test91
Date: 2026-10-18
Execution type: Local clean-room validation with deterministic fixtures and static Terraform validation
Customer repository: Local davdeploy fixture workflows
Commit: b751ad0
AWS account: 654654474502, identity not used by this validation
AWS region: us-east-1, no AWS resources created

## Resources created

- Ephemeral Docker Compose network, PostgreSQL volume, API, worker, bounded fixture executor, OPA, Prometheus, Grafana, Tempo, and OpenTelemetry collector.
- Temporary Terraform initialization directories with a shared local provider cache.
- No AWS or customer-cloud resources.

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

## Observed result

- All local services reported ready.
- Simple, complex, Day-2, and degraded demonstrations passed.
- Policy failure denied execution and readiness failure did not assume readiness.
- API/CORS, customer-plan lifecycle, audit, and Tempo trace checks passed.
- Every Terraform root initialized without a backend and validated successfully.
- Ruff passed, 226 Pytest tests passed, OpenAPI matched, and Compose configuration validated.
- One upstream Starlette `httpx` deprecation warning was reported; it did not affect results.

## Teardown

`make clean-local` removed the Compose containers, network, local database volume, virtual environment, and local runtime data.

## Final boundary

This proves the renamed local control-plane, contracts, workflows, and static Terraform configuration. It does not prove a live AWS deployment, live customer-cloud execution, Google federation, SES delivery, or production authentication.
