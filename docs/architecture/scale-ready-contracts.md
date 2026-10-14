# Scale-ready platform contracts

The millions-customer goal is implemented as stable boundaries before it is implemented as distributed infrastructure.

## Contracts

`apps/api/src/agentconstruct/contracts.py` defines versioned, transport-neutral contracts for:

- `TenantScope`: organization, workspace, project, environment and actor context;
- `EvidenceRef`: source, provenance, timestamp, digest and limitations;
- `ModelRequest`, `ModelUsage` and `ModelResponse`: provider/model/prompt version, budget and validated output metadata;
- `JobEnvelope`: typed job kind, idempotency key, retries, timeout, trace and payload;
- `CapabilityRequirement` and `ProviderCapability`: provider-neutral architecture capabilities;
- `CostEvidence`: estimate ranges, catalog version, assumptions and actual-billing distinction;
- `UsageEvent`: future quota and billing input.

## Evolution rule

The local PostgreSQL worker is allowed to carry these contracts today. A future queue, model provider, execution runner or regional cell must preserve the same semantics. Transport, provider and deployment topology are implementation details; tenant scope, provenance, policy and approval are not.

## Security rule

Contracts carry references and digests, not reusable credentials or secrets. Model responses are proposals. They do not contain execution authority. Every later execution request must still pass policy, exact-plan approval and bounded adapter checks.

## Scale rule

Every new platform operation must accept or derive `TenantScope`. Every asynchronous operation must have a stable idempotency key, bounded timeout, retry limit and correlation/trace ID. Every recommendation must identify its evidence and catalog version.

These contracts do not claim current million-customer capacity. They make future queue, cell, usage, evidence and execution scaling possible without rewriting the product domain.

