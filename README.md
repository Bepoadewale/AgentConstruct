# AgentConstruct

AgentConstruct turns an AI workload request into a governed infrastructure plan. A developer describes the outcome, reviews one recommended AWS design, then submits its exact digest for workspace-administrator approval or rejection. Approval never means deployment.

**Delivery state: executable local V1 foundation plus an AWS-hosted control-plane runtime for customer-AWS discovery.** The local workflow is real: FastAPI, PostgreSQL, OPA, a bounded execution fixture, Prometheus, Tempo and Grafana run in Docker Compose. Terraform created the customer discovery identity path and AgentConstruct recorded live inventory snapshots. The GitHub App read real repository metadata through a short-lived installation token and has a guarded reviewed-PR publisher for desired-state packages. The AgentConstruct API is also deployed to AWS App Runner for read-only customer-account connection verification. The static React frontend now lives in the private [`agentconstruct-frontend`](https://github.com/Bepoadewale/agentconstruct-frontend) repository and is prepared for Cloudflare Pages Free; it has not been deployed there yet. A durable hosted PostgreSQL/RDS contract is implemented and statically validated but has not yet been applied. Approved customer-plan revisions can still run only a bounded local dry run and observed local destroy. No customer workload, VPC, database, compute service, GitOps sync, or Terraform apply for workload infrastructure has been executed by the product UI.

## What it does

```text
customer request → typed workload specification → reusable-cloud inventory fixture
→ simplest viable architecture and cost plan
→ policy → immutable customer-plan review draft
→ submission → administrator decision
```

After approval, a separate explicit **Execute local dry run** action can queue the bounded fixture worker, observe READY/FAILED/DEGRADED, show health/cost evidence, and create a governed local destroy plan. This remains local execution evidence only.

For the first Day-2 loop, a bounded telemetry fixture can explain elevated latency, propose a replica change with a cost range and rollback, then send that exact change through the same policy, approval, worker and observation path. It never repairs a protected environment automatically.

The planner evaluates viable choices internally, including why simpler options were rejected. The browser presents only the selected AWS design, with its cost range, security controls, observability contract and stated limits.

Customers do not have to choose subnets, Helm values or Kubernetes internals to use the demo. They can inspect those decisions, edit important constraints, record assumption decisions and create a new draft revision before submitting for approval.

Developers and AI clients can use the same governed product surface through the REST API, `agentconstruct` CLI, or `agentconstruct-mcp` stdio server. See [agent client strategy](docs/product/agent-client-strategy.md). The approved architecture profile chooses a matching delivery contract: EKS/GitOps is used only when EKS is the selected profile.

| Role | Can do | Cannot do |
| --- | --- | --- |
| Developer/founder | Describe a workload, create/revise/submit a customer-plan review and inspect cost | Choose another organisation, bypass policy, approve or reject a customer plan |
| Workspace administrator | Create and submit a plan; approve or reject submitted workspace plans, including their own | Approve changed/stale revisions or bypass cloud controls |
| Intent provider | Propose a typed requirement set | Run shell commands, Terraform, `kubectl`, or cloud mutations |

The local administrator experience includes filtered queues for pending, approved, rejected and self-approved plan revisions, a richer review detail with requester/repository/AWS target/digest/policy/monitoring/cost/risk evidence, an explicit **approved, not deployed** boundary, and a human-readable audit timeline.

## Run it locally

```bash
make help
make local-proof
make clean-local
```

`make local-proof` bootstraps the local stack, then runs service readiness, the API/CORS contract, customer-plan E2E, demo-data seeding, Tempo trace verification and `make verify`. Individual setup and demo targets remain available for narrower checks: `make install`, `make bootstrap-local`, `make demo-simple`, `make demo-complex`, `make demo-day2`, `make demo-degraded`, `make demo-failure`, `make demo-readiness-failure`, `make customer-plan-persistence`.

The API is at http://localhost:8080, Grafana at http://localhost:3000 and
Prometheus at http://localhost:9090. Run the frontend repository separately at
http://localhost:5173. The local login is a documented signed fixture, not
production identity.

For customer AWS onboarding, see [Connect an AWS account](docs/customer-aws-connection.md). The UI includes an account picker, AWS account-ID setup, a Quick Create handoff, and a durable server-side verification job. It is safe by default: customers provide no access keys or administrator access. The AWS-hosted App Runner runtime uses a separate runtime IAM role and Secrets Manager-backed ExternalId storage; it never uses the GitHub Actions role as the control-plane runtime. The public CloudFormation template host and hosted read-only verification path have been applied and verified.

The frontend/backend ownership and contract are documented in the
[migration audit](docs/MIGRATION_AUDIT.md) and [ADR-012](docs/decisions/ADR-012-separated-static-frontend.md).

## What is real, simulated and next

- **Executed locally:** natural-language fixture interpretation, typed validation, AWS candidate comparison, fixture-inventory reuse, transparent estimated cost ranges and complexity scores, live OPA policy, PostgreSQL lifecycle/audit state, tenant-scoped GitHub/AWS connection metadata, exact-plan approval, fixture desired-state PR/check-state records, App Runner Terraform contract rendering, cloud-readiness preflight, Terraform plan-only review records, durable queued fixture work, observed status, persisted incident/recommendation records, bounded Day-2 recommendation/change evidence, metrics, traces and dashboards.
- **Simulated locally:** the default AI intent fixture, planner inventory/pricing, fixture GitHub desired-state publication/checks, and deployment target. A governed Nova 2 Lite/Bedrock intent adapter is implemented and disabled by default; see [its activation and authority boundary](docs/architecture/nova-2-lite.md). The executor can call only fixed fixture endpoints; it has no Docker, Kubernetes, Terraform, GitHub or AWS authority.
- **Implemented / unexecuted:** guarded live GitHub desired-state PR publishing, hosted RDS/PostgreSQL persistence contract, and App Runner VPC connector/private database wiring.
- **Executed hosted discovery:** AWS App Runner-hosted AgentConstruct runtime, separate runtime IAM role, ECR image, runtime signing secret in Secrets Manager, public versioned CloudFormation template host, short-lived AWS STS role assumption into a customer read-only discovery role, credential-free inventory snapshots, and GitHub App read-only repository metadata. The AWS discovery role is read-only; no deployment role is granted. GitHub desired-state writes are implemented behind explicit reviewed-write configuration and are not the default local path.
- **Roadmap:** hosted GitHub OIDC assumption, live public GitHub webhooks, authenticated Terraform plan execution and separately authorised deployment, real GitOps/Argo execution, enterprise OIDC, customer billing and production support. Local/provider-neutral private-beta controls and self-hosted diagnostics are implemented; see [API and trust surfaces](docs/api-and-trust.md) and the [administrator runbook](docs/self-hosted-admin-runbook.md).

## Architecture

See the [documentation map](docs/README.md), [minimum-necessary infrastructure](docs/product/minimum-necessary-infrastructure.md), [planner](docs/architecture/planner.md), [Day-2 operations](docs/architecture/day2.md), [agent interfaces](docs/architecture/agent-interfaces.md), [why AgentConstruct exists](docs/product/differentiation.md), [profile-aware execution](docs/architecture/profile-execution.md), [Terraform plan-only review](docs/architecture/terraform-plan-review.md), [governed integrations](docs/architecture/governed-integrations.md), [hosted persistence](docs/architecture/hosted-persistence.md), [AWS V1 families](docs/architecture/aws-v1.md), [provider model](docs/architecture/provider-model.md), [single-cloud default](docs/architecture/multicloud.md), [planned cloud-pilot architecture](docs/architecture/cloud-pilot.md), [security model](docs/security/security-model.md), and [validation evidence](docs/VALIDATION.md).

AgentConstruct is private commercial product work. The public portfolio repositories remain independent technical evidence and are not copied wholesale into this product.

See the [current-state audit](docs/product/CURRENT_STATE_AUDIT.md), [product flow](docs/product/PRODUCT_FLOW.md), [approval architecture](docs/architecture/PLAN_APPROVAL_ARCHITECTURE.md), [plan lifecycle](docs/architecture/PLAN_LIFECYCLE.md), and [two-user demo](docs/DEMO.md).
