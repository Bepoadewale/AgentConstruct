# Local Development

The local stack starts PostgreSQL, OPA, the AgentConstruct API/UI, a bounded fixture executor, Prometheus, OpenTelemetry Collector, Tempo and Grafana. The browser can create a tenant-scoped GitHub repository record and an AWS BYOC role-contract record. They contain metadata only; no real GitHub or AWS credentials are accepted.

The canonical demo request is: deploy a private AWS AI API with 20 average RPS, 100 peak RPS, staging and production, monitoring and a budget below $1,500. The UI shows the typed interpretation, architecture choice, assumptions, cost range and governance result.

`make demo-failure` deliberately asks for a budget above the allowed local policy limit. OPA denies the plan before execution. `make demo-readiness-failure` deliberately makes the bounded fixture report a failed readiness result; the observer records `FAILED` and never calls it READY.

`make demo-simple` proves a low-traffic containerised API selects App Runner rather than EKS. `make demo-complex` proves an explicit multi-service GPU/Kubernetes request selects the specialised EKS profile. `make demo-day2` uses deterministic high-latency telemetry, persists an incident and recommendation, requires a separate operator to approve the production change, runs the same durable worker, observes the fixed result, then completes governed destruction. `make demo-degraded` proves a degraded state creates a durable open incident. These are local simulations, not cloud monitoring or automatic remediation.

Run `make trace-check` after a demo. Grafana can then query the local Tempo datasource. The browser can also request the governed production-destroy path; the local fixture requires an independent operator approval and records observed cleanup. These are local evidence only, not production observability or cloud-execution claims.
