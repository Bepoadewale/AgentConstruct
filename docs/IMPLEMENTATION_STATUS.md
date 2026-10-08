# Implementation Status

## Executed locally

| Capability | Evidence |
| --- | --- |
| Intent to typed specification | Provider interface, deterministic fixture, schema validation, provenance and material follow-up questions |
| Architecture and cost proposal | Constrained AWS V1 planner with assumptions and cost ranges |
| Governance | Live OPA policy, immutable SHA-256 plan hash, independent approval and audit |
| Durable state | PostgreSQL in Compose; SQLite only in fast unit tests |
| Local execution | Fixed fixture executor reports READY, FAILED or DESTROYED; API observes the result |
| UI and monitoring | Browser UI, `/metrics`, Prometheus and provisioned Grafana dashboard for request, plan-policy and observed-execution outcomes |

## Simulated

- Natural-language understanding uses deterministic parsing, not a paid model.
- The AWS architecture recommendation is a small rule catalogue, not arbitrary design generation.
- Deployment is a bounded local fixture, not AWS, Terraform, Docker or Kubernetes execution.
- Local signed JWT is a development fixture, not enterprise OIDC/JWKS validation.

## Roadmap only

Customer AWS role assumption, GitHub App installation/webhooks, real GitOps/Argo execution, enterprise identity, live price APIs, subscription billing, model runtime controls and automated remediation.
