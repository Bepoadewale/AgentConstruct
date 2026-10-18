# Scale-ready local boundaries

davdeploy keeps the first deployment small while making the product contracts
safe to distribute later. This document describes the local implementations and
the replacement seams; it is not evidence of a cloud deployment.

## Current local boundaries

- `contracts.py` carries versioned, tenant-scoped envelopes, evidence refs, jobs,
  model calls, capabilities, cost evidence, usage, execution outcomes, and
  named v1 workload/plan/approval/observation/resource/output records.
- `boundaries.py` provides required tenant context, feature flags, lifecycle
  export/deletion/archive contracts, capability registration, evidence links,
  separate cost/complexity/risk/reliability/capacity engines, rollout targeting,
  and runner limits.
- `queue.py` exposes `enqueue`, `claim`, `heartbeat`, `retry`, `cancel`, and
  `dead_letter`, plus stale-job recovery. PostgreSQL is only the current
  transport adapter.
- `model_gateway.py` applies provider, token, and timeout admission before a
  gateway call and exposes structured generation, cost, and output validation.
  The deterministic fixture is deliberately non-authoritative.
- `execution_runner.py` exposes prepare/execute/observe/destroy/cancel/evidence
  lifecycle methods and fails closed unless a bounded runner is configured.
- `production_readiness.py` provides a tenant-scoped SQLite seam for local
  export, backup, archive, soft-delete, and recovery tests, plus concurrent
  idempotency and entitlement admission probes.
- `policy.py`, `client.py`, `cli.py`, and `mcp.py` expose independent
  authorization and explicit v1 protocol/schema metadata.

## Replacement seams

The control plane owns plans, policy, approvals, audit, evidence, entitlements,
and recommendations. Runners receive an `ExecutionContext` containing a plan
digest and credential reference, never reusable credentials or raw model output.

The following can be replaced without changing business semantics:

| Local implementation | Future adapter |
| --- | --- |
| PostgreSQL job queue | managed queue or workflow service |
| deterministic model gateway | approved model provider |
| fixture pricing catalog | live catalog/billing adapter |
| in-memory capability registry | provider catalog service |
| in-memory lifecycle ledger | durable retention/export service |
| fixture execution runner | isolated customer-account runner |

## Required invariants

1. Every job, evidence node, model request, usage event, and execution context
   carries tenant scope.
2. Every privileged operation includes actor, tenant, plan digest, policy result,
   approval, and scope.
3. Every recommendation records evidence, provenance, limitations, and catalog
   or policy versions.
4. A model may propose structured content; it cannot authorize or execute it.
5. Runners are bounded by operation allowlists, timeouts, network policy, and
   output limits.
6. Feature flags default off and can target a tenant without changing code.
7. Export and deletion are explicit lifecycle operations with auditable due dates.
8. API, CLI, and MCP clients advertise a stable contract version.

## What remains intentionally unimplemented

This boundary work does not claim a production identity provider, durable hosted
retention service, live billing, customer workload execution, or multi-region
cells. Those are deployment and operations work after the local contracts and
regression gates are proven.
