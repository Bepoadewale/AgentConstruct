# Implementation Status

## Executed locally

| Capability | Evidence |
| --- | --- |
| Intent to typed specification | Provider interface, deterministic fixture, schema validation, provenance and material follow-up questions |
| Architecture and cost proposal | Constrained AWS V1 planner with assumptions and cost ranges |
| Governance | Live OPA policy, immutable SHA-256 plan hash, independent approval and audit |
| Durable state | PostgreSQL in Compose; SQLite only in fast unit tests |
| Cloud connection | Tenant-scoped BYOC role-contract metadata only; no AWS credential is stored or used |
| Local execution | API persists a `QUEUED` job; a separate trusted worker invokes only the fixed fixture executor and records READY, FAILED or DESTROYED evidence |
| Identity boundary | Local signed-token fixture plus an unconfigured JWT/JWKS verifier interface for a future trusted issuer |
| UI and monitoring | Plain JavaScript browser UI with editable region/data/budget constraints; `/metrics`, Prometheus, business OTel spans, Tempo and Grafana datasources/dashboard for request, plan-policy and observed-execution outcomes |

## Simulated

- Natural-language understanding uses deterministic parsing, not a paid model.
- The AWS architecture recommendation is a small rule catalogue, not arbitrary design generation.
- Deployment is a bounded local fixture, not AWS, Terraform, Docker or Kubernetes execution.
- Local signed JWT is a development fixture. The JWKS verifier adapter is code, not enterprise OIDC execution evidence.

## Roadmap only

Customer AWS role assumption, GitHub App installation/webhooks, real GitOps/Argo execution, enterprise identity, live price APIs, subscription billing, model runtime controls and automated remediation.

## Statically validated cloud contract

Terraform describes separate state/lock/budget guardrails plus a private VPC, EKS, ECR, RDS, Secrets Manager and IRSA foundation. Kubernetes describes hardened API replicas, probes, a PDB, default-deny policy and placeholder-only secret/image references. Argo CD describes reviewed desired-state reconciliation. Terraform format, offline-backend initialisation and validation passed. None of those resources or controllers has run in AWS.

GitHub Actions also validates the Terraform and Kubernetes contracts. A manual GitHub OIDC workflow has exact plan/apply/destroy confirmations and an account check, but it has not been dispatched and no AWS identity has been assumed.
