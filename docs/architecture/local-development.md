# Local Development

The local stack starts PostgreSQL, OPA, the AgentConstruct API/UI, a bounded fixture executor, Prometheus and Grafana.

The canonical demo request is: deploy a private AWS AI API with 20 average RPS, 100 peak RPS, staging and production, monitoring and a budget below $1,500. The UI shows the typed interpretation, architecture choice, assumptions, cost range and governance result.

The failure demo deliberately asks for a budget above the allowed local policy limit. OPA denies the plan before execution.
