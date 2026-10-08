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
