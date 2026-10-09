# Implementation Status

## Executed locally

| Capability | Evidence |
| --- | --- |
| Intent to typed specification | Provider interface, deterministic fixture, schema validation, provenance and material follow-up questions |
| Architecture and cost proposal | Constrained AWS V1 candidate planner: hard-constraint rejection, fixture inventory reuse, component cost ranges, complexity scores, rejected alternatives and upgrade triggers |
| Governance | Live OPA policy, immutable SHA-256 plan hash, independent approval and audit |
| Durable state | PostgreSQL in Compose; SQLite only in fast unit tests |
| Customer AWS discovery | Executed: Terraform-created read-only discovery role, permissionless future-execution role, GitHub OIDC control-plane identity, STS chain, live inventory and Cost Explorer query. AgentConstruct stores only connection metadata and a credential-free inventory snapshot. |
| GitHub repository discovery | Executed: the selected GitHub App installation issued a short-lived token to read `Bepoadewale/ai-platform-control-plane` metadata. The live adapter refuses write, PR publication and webhook processing. |
| Local execution | API persists a `QUEUED` job; a separate trusted worker invokes only the fixed fixture executor and records READY, FAILED or DESTROYED evidence |
| Day-2 change loop | Deterministic latency evidence → explanation → immutable `CHANGE` plan → production approval → durable worker → observed recovery and audit |
| Customer decision view | Browser renders viable leanest/scale-ready/specialised choices, fixture cost ranges, complexity, assumptions, rejected alternatives and upgrade triggers |
| Incident evidence | PostgreSQL persists local degraded-health incidents and the recommendation lifecycle from proposed to applied/resolved |
| Identity boundary | Local signed-token fixture plus an unconfigured JWT/JWKS verifier interface for a future trusted issuer |
| UI and monitoring | Plain JavaScript browser UI with editable region/data/budget constraints; `/metrics`, Prometheus, business OTel spans, Tempo and Grafana datasources/dashboard for request, plan-policy and observed-execution outcomes |
| Agent clients | Authenticated REST API, thin CLI, and stdio MCP server. They use the same API and do not expose approval, cloud credentials, shell, Terraform, Kubernetes, or secrets. The full local Compose proof exercises MCP tool discovery. |

## Simulated

- Natural-language understanding uses deterministic parsing, not a paid model.
- The default planner inventory and pricing remain local fixtures. The separately recorded customer discovery snapshot is live, read-only evidence; it does not grant deployment permission.
- Deployment and Day-2 change application are bounded local fixtures, not AWS, Terraform, Docker or Kubernetes execution.
- Local signed JWT is a development fixture. The JWKS verifier adapter is code, not enterprise OIDC execution evidence.

## Roadmap only

GitHub-hosted control-plane OIDC assumption, GitHub webhooks/reviewed PR publication, profile-specific Terraform rendering/deployment, real GitOps/Argo execution, enterprise identity, external agent-client installation, subscription billing, model runtime controls and automated remediation.

## Statically validated cloud contract

Terraform describes separate state/lock/budget guardrails plus a private VPC, EKS, ECR, RDS, Secrets Manager and IRSA foundation. Kubernetes describes hardened API replicas, probes, a PDB, default-deny policy and placeholder-only secret/image references. Argo CD describes reviewed desired-state reconciliation. Terraform format, offline-backend initialisation and validation passed. None of those resources or controllers has run in AWS.

GitHub Actions runs lint, tests, dependency audit, secret scan, OPA tests, SBOM, filesystem scan, image build, Terraform/Kubernetes contract checks, and the full local proof (simple, complex, degraded, Day-2, policy/readiness failure, traces and MCP tool discovery). A manual GitHub OIDC workflow has exact plan/apply/destroy confirmations and an account check, but it has not been dispatched. The live control-plane role was verified locally through a temporary owner chain that was removed afterward; the GitHub OIDC route remains unexecuted.
