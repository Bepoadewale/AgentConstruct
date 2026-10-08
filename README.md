# AgentConstruct

AgentConstruct turns an AI workload request into a governed infrastructure plan. A customer describes the outcome, reviews the design, cost and risks, approves the exact plan, and sees a safe local deployment result.

**Delivery state: executable local V1 foundation; cloud-pilot contracts and future operator workflow validated statically.** The local workflow is real: FastAPI, PostgreSQL, OPA, a bounded execution fixture, Prometheus, Tempo and Grafana run in Docker Compose. The AWS/EKS/GitOps design, GitHub OIDC workflow and operator commands exist, but no AWS resource, customer GitHub App, customer-cloud role or real deployment has been executed.

## What it does

```text
customer request → typed workload specification → architecture and cost plan
→ policy → immutable plan → independent approval → bounded executor
→ observed READY/FAILED → audit → governed destroy
```

Customers do not have to choose subnets, Helm values or Kubernetes internals to use the demo. They can inspect those decisions and set important constraints.

| Role | Can do | Cannot do |
| --- | --- | --- |
| Developer/founder | Describe a workload, create a plan, inspect cost and request deployment | Choose another organisation, bypass policy, approve their own protected production plan |
| Operator | Independently approve the exact protected plan | Approve a changed or stale plan |
| Intent provider | Propose a typed requirement set | Run shell commands, Terraform, `kubectl`, or cloud mutations |

## Run it locally

```bash
make install
make bootstrap-local
make smoke
make demo
make demo-failure
make demo-readiness-failure
make trace-check
make browser-contract
make verify
make clean-local
```

Open http://localhost:8080. Grafana is at http://localhost:3000 and Prometheus is at http://localhost:9090. The local login is a documented signed fixture, not production identity.

The V1 browser is deliberately plain HTML/CSS/JavaScript; see [ADR-009](docs/decisions/ADR-009-plain-web-ui.md). It keeps the first product flow small and does not move privileged logic into the browser.

## What is real, simulated and next

- **Executed locally:** natural-language fixture interpretation, typed validation, constrained AWS architecture planning, transparent estimated cost range, live OPA policy, PostgreSQL lifecycle/audit state, tenant-scoped GitHub/AWS connection metadata, exact-plan approval, durable queued fixture work, observed status, metrics, traces and dashboards.
- **Simulated locally:** the AI intent provider and the deployment target. The executor can call only fixed fixture endpoints; it has no Docker, Kubernetes, Terraform or AWS authority.
- **Roadmap:** customer AWS role assumption with short-lived credentials, GitHub App installation/webhooks, real GitOps/Argo execution, enterprise OIDC, customer billing and production support.

## Architecture

See the [documentation map](docs/README.md), [V1 architecture](docs/architecture/architecture.md), [planned cloud-pilot architecture](docs/architecture/cloud-pilot.md), [security model](docs/security/security-model.md), [cloud operations](docs/cloud-operations.md), [product vision](docs/product/vision.md), and [validation evidence](docs/VALIDATION.md).

AgentConstruct is private commercial product work. The public portfolio repositories remain independent technical evidence and are not copied wholesale into this product.
