# Validation

## Local V1 clean-room evidence

Date: 2026-10-08. Environment: macOS, Docker Desktop and Python 3.12.

Two clean project-runtime cycles were completed, followed by a third confirmation that rebuilt the Docker images. Before each cycle, `make clean-local` removed only AgentConstruct containers, network, PostgreSQL volume, virtual environment and `.local` data. The first two cycles retained Docker images; the third used `docker compose up -d --build`. No prior runtime state, database data or local files were needed.

Each cycle ran:

```bash
make bootstrap-local
make smoke
make demo
make demo-failure
make demo-readiness-failure
make trace-check
make verify
make opa-test
make clean-local
```

Results from every cycle:

- Smoke checks found the API, fixture executor, PostgreSQL, OPA, Prometheus, Grafana, Tempo and OpenTelemetry Collector ready.
- The success demo created staging and production environments, observed two `READY` results, required a different operator to approve production, destroyed production through the governed path and wrote audit events.
- The budget failure demo was denied by live OPA before execution.
- The readiness failure demo made the bounded executor report failure. The observer recorded `FAILED`; it did not assume `READY` because a command returned.
- Tempo returned traces for `agentconstruct-api` after the demo.
- `ruff` passed; `pytest` passed **12 tests**; `opa test` passed **3/3**; `docker compose config --quiet` passed.
- Each cleanup confirmed that project containers and `.local` data were absent. No broad Docker cleanup command was used.

This evidence is local only. No AWS resources, customer GitHub installation, customer credentials or enterprise identity provider were used.

## Static cloud-contract evidence

On 2026-10-08, `make terraform-validate` passed for the bootstrap and pilot Terraform roots. `make kubernetes-render` rendered the Kubernetes contract. The render did not contact or apply to a Kubernetes cluster. No AWS authenticated plan, apply, image push, Argo reconciliation or cloud destroy occurred.

PR 3 adds strict CI validation for those contracts and a manual GitHub OIDC operator workflow. Neither was dispatched against AWS during this readiness phase.

## V1 hardening clean-room evidence

Date: 2026-10-08. Environment: macOS, Docker Desktop and Python 3.12.

The first hardening cycle ran from a removed AgentConstruct Compose stack and PostgreSQL volume. It rebuilt the API and new worker image, then ran:

```bash
make bootstrap-local
make smoke
make browser-contract
make demo
make demo-failure
make demo-readiness-failure
make trace-check
make verify
make opa-test
make terraform-validate
make kubernetes-render
```

Results:

- The separate worker started and processed durable queued deployment and destroy jobs.
- The browser contract found the editable region, data-classification and budget controls in the real served UI.
- The success flow recorded two `READY` environments, an independently approved production destroy and 12 audit events.
- Budget denial and readiness failure both behaved as expected; the observer recorded `FAILED` rather than assuming success.
- Tempo received API and worker business spans.
- `ruff` passed; `pytest` passed **14 tests**; OPA passed **3/3**; Terraform bootstrap and pilot validation passed; Kubernetes rendering passed.

This is still local/static evidence only. The JWKS adapter, External Secrets, GitHub App delivery, ALB controller, AWS resources and real GitOps reconciliation were not executed.

A second clean cycle repeated the same commands from a removed Compose stack and ended with `make clean-local`. It again passed the browser contract, success, policy-denial, readiness-failure, trace, lint, test and OPA checks; the project Compose containers and local data were absent after cleanup.

## Minimum-necessary planner clean-room evidence

Date: 2026-10-09. Environment: macOS, Docker Desktop, Python 3.12, Terraform and kubectl.

Two clean cycles were completed after the planner change. Both began with `make clean-local`, rebuilt the local stack through `make bootstrap-local`, and ended with `make clean-local`.

Each cycle ran:

```bash
make bootstrap-local
make smoke
make browser-contract
make demo
make demo-failure
make demo-readiness-failure
make trace-check
make verify
make opa-test
make terraform-validate
make kubernetes-render
make clean-local
```

Results from both cycles:

- API, worker, fixture executor, PostgreSQL, OPA, Prometheus, Grafana and Tempo became ready.
- The browser contract passed.
- The canonical governed deployment completed with two observed `READY` environments and a governed destroy. The policy and readiness failure demos remained denied/failed as designed.
- Tempo received traces. Ruff passed. Pytest passed **28 tests**. OPA passed **3/3**. Both Terraform roots formatted and validated with `init -backend=false`. Kubernetes rendered without applying.
- Cleanup removed the project Compose containers, network, PostgreSQL volume, virtual environment and `.local` data.

The first fresh bootstrap exposed a PostgreSQL race between the API and worker creating the migration table. The code now takes a PostgreSQL transaction-scoped advisory lock before migrations. Both recorded cycles passed with that fix.

This evidence proves local planner and runtime behavior only. AWS inventory/pricing remain deterministic fixtures; no AWS account, billable resource, GitHub App, or customer role was contacted.

## Governed agent-interface validation

Date: 2026-10-09. The CLI and stdio MCP server were tested as thin API clients, not as alternate execution authorities.

- The MCP catalogue exposed analysis, planning, comparison, estimate, status, audit, eligible-execution, and destroy-plan operations.
- It deliberately exposed no approval, cloud credential, secret, shell, Terraform or Kubernetes tool.
- CLI request construction preserved the caller's project, repository, cloud-connection reference and idempotency key.
- Unit validation passed with **33 tests**.

Two clean Compose cycles then passed with the installed `agentconstruct-mcp` entry point included in each cycle. Each cycle passed smoke, browser contract, canonical demo, policy failure, readiness failure, Tempo trace check, Ruff, all then-current 32 tests, OPA 3/3, Terraform `fmt`/offline-backend `init`/`validate`, Kubernetes render, MCP `tools/list`, and scoped cleanup. The final 33-test run added a tenant-scoped agent-read test. The MCP contract confirmed the tools were available without an approval tool.

## Governed Day-2 loop clean-room evidence

Date: 2026-10-09. Environment: macOS, Docker Desktop, Python 3.12, Terraform and kubectl.

Two clean cycles began and ended with `make clean-local`. Each rebuilt Compose from scratch and ran:

```bash
make bootstrap-local
make smoke
make browser-contract
make demo
make demo-day2
make demo-failure
make demo-readiness-failure
make trace-check
make verify
make opa-test
make terraform-validate
make kubernetes-render
printf '%s\n' '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' | AGENTCONSTRUCT_TOKEN=fixture-token .venv/bin/agentconstruct-mcp
make clean-local
```

Both cycles passed. The Day-2 demo created a production environment, read deterministic high-latency evidence, created a `CHANGE` plan, required a separate operator to approve the exact plan, observed the fixed local change result, and then used the existing governed destroy path. Ruff passed, pytest passed **36 tests**, OPA passed **3/3**, both Terraform roots formatted and validated with `init -backend=false`, Kubernetes rendered without applying, and the MCP catalogue included the non-mutating recommendation and governed change-plan tools.

This is local fixture evidence only. The telemetry, cost delta and fixed change endpoint do not represent a cloud metric source, actual AWS cost, customer workload, or autonomous remediation.

## Customer planning and degraded-state clean-room evidence

Date: 2026-10-09. Environment: macOS, Docker Desktop, Python 3.12, Terraform and kubectl.

Two clean Compose cycles began and ended with `make clean-local`. Each rebuilt the stack and ran:

```bash
make bootstrap-local
make smoke
make browser-contract
make demo-simple
make demo-complex
make demo-degraded
make demo-day2
make demo
make demo-failure
make demo-readiness-failure
make trace-check
make verify
make opa-test
make terraform-validate
make kubernetes-render
make clean-local
```

Both cycles passed. `demo-simple` selected `aws-app-runner` for the low-traffic container API; `demo-complex` selected `aws-eks-governed` only for the explicit multi-service GPU/Kubernetes request. `demo-degraded` recorded `DEGRADED` state and an open PostgreSQL incident. `demo-day2` persisted a recommendation, required the separate operator to approve the production `CHANGE` plan, observed the fixed local outcome, then resolved the incident. Browser, policy, readiness-failure, traces, Ruff, pytest (**38 tests**), OPA (**3/3**), Terraform offline validation and Kubernetes rendering also passed.

This remains local fixture/static evidence. Neither App Runner, EKS, GPU capacity, Terraform apply nor an AWS account was executed.

## Governed integration-contract clean-room evidence

Date: 2026-10-09. Environment: macOS, Docker Desktop, Python 3.12, Terraform and kubectl.

Two clean Compose cycles began and ended with `make clean-local`. Each cycle ran:

```bash
make bootstrap-local
make smoke
make browser-contract
make demo-simple
make demo-complex
make demo-degraded
make demo-day2
make demo
make demo-failure
make demo-readiness-failure
make trace-check
make verify
make opa-test
make terraform-validate
make kubernetes-render
make clean-local
```

Both cycles passed. The simple workload used `aws-app-runner`; the complex workload used `aws-eks-governed`; each local execution carried the selected profile into the bounded executor. Browser, policy and readiness-failure paths passed. Tempo received traces. Ruff passed, pytest passed **44 tests**, OPA passed **3/3**, both Terraform roots formatted and validated with `init -backend=false`, and Kubernetes rendered without being applied. The final cleanup confirmed that no project Compose container, volume, virtual environment or local state remained.

The GitHub desired-state pull-request/check contract, GitHub webhook contract and customer AWS OIDC/STS role contract are tested as deterministic fixtures only. No GitHub App installation, webhook, repository write, AWS credentials, AWS role assumption, Terraform apply, Argo reconciliation or Kubernetes cluster was contacted.

## Final product-proof clean-room evidence

Date: 2026-10-09. Environment: macOS, Docker Desktop, Python 3.12, Terraform and kubectl.

Two clean cycles began and ended with `make clean-local`. Each cycle rebuilt the Compose stack and ran the full customer and agent-client proof:

```bash
make bootstrap-local
make smoke
make browser-contract
make demo-simple
make demo-complex
make demo-degraded
make demo-day2
make demo
make demo-failure
make demo-readiness-failure
make trace-check
make verify
make opa-test
make terraform-validate
make kubernetes-render
printf '%s\n' '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' | AGENTCONSTRUCT_TOKEN=fixture-token .venv/bin/agentconstruct-mcp
make clean-local
```

Both cycles passed. The browser contract and all three planning stories passed: a small request selected App Runner, a complex GPU/Kubernetes request selected EKS, and degraded Day-2 evidence created a governed change with an independent approval. Policy denial and observed readiness failure passed. Tempo received traces; the MCP catalogue exposed governed tools with no approval tool. Ruff passed, pytest passed **44 tests**, OPA passed **3/3**, both Terraform roots formatted and validated offline, and Kubernetes rendered without an apply. Final cleanup left no project containers, volume, virtual environment or local state.

This is local and static evidence. It is not AWS execution, customer-cloud access, external identity, GitHub App delivery, live agent-client integration, actual cloud billing, or a cloud-pilot claim.
