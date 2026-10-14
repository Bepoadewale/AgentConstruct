# Usage and entitlement boundaries

AgentConstruct records typed `UsageEvent` values with tenant and correlation metadata.
`Entitlement` defines a tenant-scoped limit, unit, event type and time window. The local
ledger deterministically returns a `UsageDecision` before work is admitted.

This is intentionally not billing. It does not charge a card, calculate an invoice, or
claim production usage accuracy. A hosted implementation can move the ledger to a
durable, partitioned store and publish events to a billing system without changing the
domain contract.

The millions-customer path is explicit: meter by organization/workspace, keep the
admission decision close to the queue, and retain a policy version and correlation data.
Cross-tenant events are denied, and rejected attempts are not counted as consumption.
