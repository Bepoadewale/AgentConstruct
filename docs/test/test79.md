# test79 — Governed Nova 2 Lite gateway local evidence

Date: 2026-10-15. Environment: macOS, Docker Desktop, Python 3.12,
Terraform, kubectl, and local fixture identities.

Execution type: local fixture validation with a fake Bedrock Runtime client.

Customer repository: `Bepoadewale/AgentConstruct`.

Commit: `ae25558` plus the PR's final evidence commit.

AWS account: none used.

AWS region: `us-east-1` configured only for offline request construction.

## Classification

This is **local, simulated, and statically validated** evidence. The model
transport was tested with a fake Bedrock Runtime client. No AWS credential was
used, no Nova request was sent, and no AWS, GitHub, Terraform apply, or
Kubernetes mutation occurred.

## Resources created

None. No AWS resource, customer workload, or durable local resource was
created.

## Commands executed

Each cycle began without the project stack, volumes, virtual environment, or
local state and ended with `make clean-local`. Each ran:

```bash
make bootstrap-local
make smoke
make browser-contract
make frontend-contract
make frontend-responsive-contract
make frontend-accessibility-contract
make local-load-smoke
make customer-plan-e2e
make demo-simple
make demo-complex
make demo-degraded
make demo-day2
make demo-failure
make demo-readiness-failure
make trace-check
make verify
make opa-test
make terraform-validate
make kubernetes-render
make clean-local
```

## Observed result

- Both cold bootstraps and all readiness checks passed.
- Browser, interaction, responsive, and accessibility contracts passed twice.
- Both 50-request, concurrency-5 local load smokes passed; observed p95 values
  were 34.5 ms and 27.2 ms. These are local smoke results, not capacity claims.
- The governed customer-plan E2E passed twice, including independent approval,
  denial paths, local dry-run execution, observed failure, destroy, and audit.
- Simple, complex, degraded, and Day-2 demonstrations passed twice.
- Policy denial and readiness-failure demonstrations passed twice.
- Tempo trace checks passed twice.
- Ruff passed twice; pytest passed 186 tests twice with one known upstream
  Starlette/httpx deprecation warning.
- OPA passed 3/3 tests twice.
- Every Terraform root initialized with the shared provider cache and validated
  twice; the Nova App Runner contract remained opt-in and used no static AWS
  credential.
- The Kubernetes contract rendered twice and was never applied.
- Final cleanup removed project containers, the project volume, `.venv`, and
  `.local` after each cycle.

## Nova-specific coverage

Offline tests covered Bedrock Converse request construction, the official Nova
2 Lite geographic inference profile ID, input-digest verification, strict local
schema validation, one bounded repair attempt, incomplete and malformed output,
tenant data-policy admission, timeout/token limits, safe telemetry, token usage
metering, optional versioned pricing, explicit fixture fallback identity, API
503 translation, and least-privilege runtime IAM restricted to the selected
inference profile.

## Teardown

Each clean-room cycle ended with `make clean-local`, which removed the project
containers, volume, virtual environment, and local runtime state.

## Final boundary

This evidence does not prove live Bedrock entitlement, live model quality,
production latency, AWS quota, geographic routing, or a customer rollout. Those
require a separately authorized, budget-capped AWS evaluation after account and
model access are configured.
