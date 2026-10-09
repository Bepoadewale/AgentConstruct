# Project Status

## Current state

**AgentConstruct V1 foundation — implemented locally; cloud-pilot contracts statically validated; cloud execution not claimed.**

The GitHub repository has been renamed from `ai-platform-product-strategy` to `AgentConstruct`. It is a private commercial product repository.

## What is implemented

- Multi-organisation product domain and PostgreSQL persistence.
- Signed local development identity fixture, tenant checks and a production-facing JWT/JWKS verifier interface.
- Natural-language intent fixture → typed `WorkloadSpec`.
- Small, auditable AWS V1 catalogue that considers static, serverless, managed application, managed containers, VM, Kubernetes, managed-AI, CPU and GPU options. It rejects hard-constraint failures, reuses fixture-approved resources, and selects the lowest-complexity option in the configurable cheapest viable cost band.
- OPA policy, immutable plan hashes, independent production approval and durable audit.
- Tenant-scoped GitHub repository and AWS BYOC role-contract metadata. No credentials are stored or used.
- Durable local execution jobs processed by a separate bounded worker, with observed READY, FAILED and DESTROYED states.
- Web UI with editable region, data and budget constraints; Prometheus metrics, OpenTelemetry business traces, Tempo and Grafana dashboard provisioning.
- One governed REST API shared by the browser, a thin CLI, and a stdio MCP server. Agent clients can analyse, plan, compare, estimate, inspect, request eligible execution, and create a destroy plan; they cannot self-approve or receive cloud, shell, Terraform, Kubernetes, or secret access.
- Fixture GitHub App contracts for repository discovery, signed-webhook shape and reviewed desired-state pull-request checks; fixture AWS BYOC OIDC/STS role contracts that return no credentials. Execution selects the approved architecture profile, so GitOps/Kubernetes is required only when EKS was selected.
- A bounded Day-2 loop: deterministic latency evidence, a transparent replica recommendation, immutable `CHANGE` plan, independent production approval, durable worker, observed result and audit. It is local fixture evidence, not autonomous remediation or cloud monitoring.
- A customer decision view that makes the planner comparison visible, plus durable local incident and recommendation records for degraded and Day-2 evidence.
- Terraform contracts for a separate state/lock/budget foundation and private VPC, EKS, ECR, RDS, Secrets Manager and IRSA runtime.
- Hardened Kubernetes and Argo CD desired-state contracts, External Secrets and artifact-storage contracts, plus planned private observability/recovery controls.

## Boundaries

- This does **not** deploy into AWS or a customer account. AWS discovery and pricing are deterministic fixtures, not live account or billing evidence.
- The local identity issuer, intent provider and execution target are fixtures. The JWKS adapter is implemented but not connected to an enterprise issuer.
- GitHub App installation, live AWS STS/OIDC execution, GitOps/Argo execution, enterprise IdP, external agent-client installation and billing are next work, not evidence.

## Next delivery sequence

1. Run a separately authorised cloud pilot: plan, create, smoke, failure proof, observability, cost query, destroy and absence verification.

## Clean-room reproducibility

Status: the earlier V1 proof completed two clean local-runtime cycles plus one rebuilt-image confirmation. This hardening change records two additional clean-room cycles with the durable worker and browser contract. Cached Docker images are not treated as runtime state.

## Cloud contract validation

`terraform fmt`, `init -backend=false` and `validate` passed for both Terraform roots on 2026-10-08. This is static validation only; no authenticated plan or AWS apply occurred.

## Future operator workflow

CI now validates Terraform and Kubernetes contracts. A manual GitHub Actions workflow defines future GitHub OIDC plan/apply/destroy gates, but it has not been dispatched and no AWS role has been assumed.
