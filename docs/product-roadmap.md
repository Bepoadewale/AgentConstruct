# Product wedge and roadmap

## Do not begin as an all-in-one platform

The initial product must solve a painful, bounded workflow better than a customer can assemble themselves.

## Recommended wedge

**Governed multi-tenant AI gateway and model-release controls for Kubernetes-based teams.**

Initial capabilities:

- signed identity and tenant-aware access;
- quotas, concurrency limits, bounded queues, and usage metering;
- approved model aliases and deterministic routing;
- policy-controlled model release, canary, approval, rollback, and audit;
- local/self-hosted deployment with OpenTelemetry/Prometheus evidence.

## Phased roadmap

### Phase 0 — Evidence (now through completion of public projects)

Finish ten independently runnable public reference implementations. Preserve local-first reproducibility and truthful evidence boundaries.

### Phase 1 — Flagship MVP

Integrate the narrow gateway + governed model release vertical slice. Obtain design-partner feedback before adding broad functionality.

### Phase 2 — Paid pilot

Run one customer workflow in a controlled environment. Measure one or two outcomes: quota isolation, approval time, release safety, cost allocation, or incident recovery.

### Phase 3 — Enterprise product

Add SSO/SCIM, advanced RBAC, durable audit retention, policy packs, deployment connectors, support, and a clear operational ownership model.

### Phase 4 — Expansion

Add agent governance, remediation, GPU capacity controls, developer portal integrations, and edge fleet operations only when customers validate the need.

## Product rule

Do not copy all source code from the public labs. Reuse proven ideas and stable contracts; build the flagship as a coherent product with its own threat model, tenancy model, release process, licensing, and test strategy.
