# Project Status

## Current state

**AgentConstruct V1 foundation — implemented locally; cloud execution not claimed.**

The GitHub repository has been renamed from `ai-platform-product-strategy` to `AgentConstruct`. It is a private commercial product repository.

## What is implemented

- Multi-organisation product domain and PostgreSQL persistence.
- Signed local development identity fixture and tenant checks.
- Natural-language intent fixture → typed `WorkloadSpec`.
- Small, auditable AWS V1 architecture catalogue and transparent cost range.
- OPA policy, immutable plan hashes, independent production approval and durable audit.
- Bounded execution fixture with observed READY, FAILED and DESTROYED states.
- Web UI, Prometheus metrics and Grafana dashboard provisioning.

## Boundaries

- This does **not** deploy into AWS or a customer account.
- The local identity issuer, intent provider and execution target are fixtures.
- GitHub App, AWS STS/OIDC, GitOps/Argo, enterprise IdP and billing are next work, not evidence.

## Next delivery sequence

1. Complete local V1 product depth, traces and cold-bootstrap evidence.
2. Add cloud-pilot architecture/runtime contracts without AWS creation.
3. Add future OIDC operator workflow and static cloud validation without AWS creation.

## Clean-room reproducibility

Status: validated with two local cycles. The second cycle used already-built images after `make install`; `make bootstrap-local` remains the documented cold-bootstrap command and includes image build.
