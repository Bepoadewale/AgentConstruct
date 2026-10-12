# AgentConstruct

AgentConstruct turns an AI workload request into a governed infrastructure plan. A developer describes the outcome, reviews one recommended AWS design, then submits its exact digest for workspace-administrator approval or rejection. Approval never means deployment.

**Delivery state: executable local V1 foundation; customer-AWS and GitHub App read-only discovery executed; workload runtime not executed in AWS.** The local workflow is real: FastAPI, PostgreSQL, OPA, a bounded execution fixture, Prometheus, Tempo and Grafana run in Docker Compose. Terraform created the customer discovery identity path and AgentConstruct recorded a live inventory snapshot. The GitHub App read real repository metadata through a short-lived installation token. Approved customer-plan revisions can now run a bounded local dry run and observed local destroy. No application, network, database, compute, GitHub write, or GitOps workload was deployed in AWS.

## What it does

```text
customer request → typed workload specification → reusable-cloud inventory fixture
→ simplest viable architecture and cost plan
→ policy → immutable customer-plan review draft
→ submission → administrator decision

After approval, a separate explicit **Execute local dry run** action can queue the bounded fixture worker, observe READY/FAILED/DEGRADED, show health/cost evidence, and create a governed local destroy plan. This remains local execution evidence only.

For the first Day-2 loop, a bounded telemetry fixture can explain elevated latency, propose a replica change with a cost range and rollback, then send that exact change through the same policy, approval, worker and observation path. It never repairs a protected environment automatically.

The planner evaluates viable choices internally, including why simpler options were rejected. The browser presents only the selected AWS design, with its cost range, security controls, observability contract and stated limits.
```

Customers do not have to choose subnets, Helm values or Kubernetes internals to use the demo. They can inspect those decisions, edit important constraints, record assumption decisions and create a new draft revision before submitting for approval.

Developers and AI clients can use the same governed product surface through the REST API, `agentconstruct` CLI, or `agentconstruct-mcp` stdio server. See [agent client strategy](docs/product/agent-client-strategy.md). The approved architecture profile chooses a matching delivery contract: EKS/GitOps is used only when EKS is the selected profile.

| Role | Can do | Cannot do |
| --- | --- | --- |
| Developer/founder | Describe a workload, create/revise/submit a customer-plan review and inspect cost | Choose another organisation, bypass policy, approve or reject a customer plan |
| Workspace administrator | Create and submit a plan; approve or reject submitted workspace plans, including their own | Approve changed/stale revisions or bypass cloud controls |

The local administrator experience includes filtered queues for pending, approved, rejected and self-approved plan revisions, a richer review detail with requester/repository/AWS target/digest/policy/monitoring/cost/risk evidence, an explicit **approved, not deployed** boundary, and a human-readable audit timeline.
| Intent provider | Propose a typed requirement set | Run shell commands, Terraform, `kubectl`, or cloud mutations |

## Run it locally

```bash
make install
make bootstrap-local
make smoke
make demo
make demo-simple
make demo-complex
make demo-day2
make demo-degraded
make demo-failure
make demo-readiness-failure
make customer-plan-e2e
make customer-plan-persistence
make trace-check
make browser-contract
make verify
make clean-local
```

Open http://localhost:8080. Grafana is at http://localhost:3000 and Prometheus is at http://localhost:9090. The local login is a documented signed fixture, not production identity.

For customer AWS onboarding, see [Connect an AWS account](docs/customer-aws-connection.md). The UI includes an account picker, AWS account-ID setup, a Quick Create handoff, and a durable server-side verification job. It is safe by default: customers provide no access keys or administrator access. Production uses a separate runtime identity and managed secret-store contract; it never uses the GitHub Actions role as the control-plane runtime. The public template host, runtime role and live UI verification still need separately approved Terraform apply before this flow can be used against a new account.

The V1 browser is deliberately plain HTML/CSS/JavaScript; see [ADR-009](docs/decisions/ADR-009-plain-web-ui.md). It keeps the first product flow small and does not move privileged logic into the browser.

## What is real, simulated and next

- **Executed locally:** natural-language fixture interpretation, typed validation, AWS candidate comparison, fixture-inventory reuse, transparent estimated cost ranges and complexity scores, live OPA policy, PostgreSQL lifecycle/audit state, tenant-scoped GitHub/AWS connection metadata, exact-plan approval, durable queued fixture work, observed status, persisted incident/recommendation records, bounded Day-2 recommendation/change evidence, metrics, traces and dashboards.
- **Simulated locally:** the AI intent provider, default planner inventory/pricing, GitHub App/desired-state publication, and deployment target. The executor can call only fixed fixture endpoints; it has no Docker, Kubernetes, Terraform, GitHub or AWS authority.
- **Executed discovery:** short-lived AWS STS role chaining, real inventory/Cost Explorer query, a tenant-scoped credential-free snapshot, and GitHub App read-only repository metadata. The AWS discovery role is read-only; the future execution role has no permissions; the GitHub adapter refuses writes.
- **Roadmap:** hosted GitHub OIDC assumption, GitHub webhooks and reviewed desired-state PRs, profile-specific Terraform rendering/deployment, real GitOps/Argo execution, enterprise OIDC, customer billing and production support.

## Architecture

See the [documentation map](docs/README.md), [minimum-necessary infrastructure](docs/product/minimum-necessary-infrastructure.md), [planner](docs/architecture/planner.md), [Day-2 operations](docs/architecture/day2.md), [agent interfaces](docs/architecture/agent-interfaces.md), [why AgentConstruct exists](docs/product/differentiation.md), [profile-aware execution](docs/architecture/profile-execution.md), [governed integrations](docs/architecture/governed-integrations.md), [AWS V1 families](docs/architecture/aws-v1.md), [provider model](docs/architecture/provider-model.md), [single-cloud default](docs/architecture/multicloud.md), [planned cloud-pilot architecture](docs/architecture/cloud-pilot.md), [security model](docs/security/security-model.md), and [validation evidence](docs/VALIDATION.md).

AgentConstruct is private commercial product work. The public portfolio repositories remain independent technical evidence and are not copied wholesale into this product.

See the [current-state audit](docs/product/CURRENT_STATE_AUDIT.md), [product flow](docs/product/PRODUCT_FLOW.md), [approval architecture](docs/architecture/PLAN_APPROVAL_ARCHITECTURE.md), [plan lifecycle](docs/architecture/PLAN_LIFECYCLE.md), and [two-user demo](docs/DEMO.md).
