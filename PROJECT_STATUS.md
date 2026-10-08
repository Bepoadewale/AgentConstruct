# Project Status

## Current state

**AgentConstruct V1 foundation — implemented locally; cloud-pilot contracts statically validated; cloud execution not claimed.**

The GitHub repository has been renamed from `ai-platform-product-strategy` to `AgentConstruct`. It is a private commercial product repository.

## What is implemented

- Multi-organisation product domain and PostgreSQL persistence.
- Signed local development identity fixture and tenant checks.
- Natural-language intent fixture → typed `WorkloadSpec`.
- Small, auditable AWS V1 architecture catalogue and transparent cost range.
- OPA policy, immutable plan hashes, independent production approval and durable audit.
- Tenant-scoped GitHub repository and AWS BYOC role-contract metadata. No credentials are stored or used.
- Bounded execution fixture with observed READY, FAILED and DESTROYED states.
- Web UI, Prometheus metrics, OpenTelemetry traces, Tempo and Grafana dashboard provisioning.
- Terraform contracts for a separate state/lock/budget foundation and private VPC, EKS, ECR, RDS, Secrets Manager and IRSA runtime.
- Hardened Kubernetes and Argo CD desired-state contracts, plus planned private observability/recovery controls.

## Boundaries

- This does **not** deploy into AWS or a customer account.
- The local identity issuer, intent provider and execution target are fixtures.
- GitHub App, live AWS STS/OIDC execution, GitOps/Argo execution, enterprise IdP and billing are next work, not evidence.

## Next delivery sequence

1. Run a separately authorised cloud pilot: plan, create, smoke, failure proof, observability, cost query, destroy and absence verification.

## Clean-room reproducibility

Status: validated with two clean local-runtime cycles plus one rebuilt-image confirmation, including success, policy-denial, readiness-failure, trace and cleanup evidence. Cached Docker images are not treated as runtime state.

## Cloud contract validation

`terraform fmt`, `init -backend=false` and `validate` passed for both Terraform roots on 2026-10-08. This is static validation only; no authenticated plan or AWS apply occurred.

## Future operator workflow

CI now validates Terraform and Kubernetes contracts. A manual GitHub Actions workflow defines future GitHub OIDC plan/apply/destroy gates, but it has not been dispatched and no AWS role has been assumed.
