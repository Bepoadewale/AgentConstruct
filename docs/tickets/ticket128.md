# ticket128: Bounded backlog recovery for event-driven worker wake-ups

PR: #128
Branch: fix/bounded-worker-drain

## Problem / goal

One SQS wake-up claimed one oldest durable record. A job queued before wake-up support could consume the signal and leave the newly requested job queued.

## Current repo state

The worker has a direct SQS event source and authoritative jobs remain durable in PostgreSQL. Wake-up messages contain no work payload.

## Research / references used

- Current Lambda worker implementation.
- Durable discovery and cloud-execution claim methods.
- SQS Lambda batch and retry boundary.

## Work planned for the PR

- Reconcile completion events first.
- Drain up to five durable jobs per signal by default, clamped to one through ten.
- Test normal, invalid, and bounded configurations.

## Acceptance criteria

- [x] One wake-up can recover a small pre-existing durable backlog.
- [x] The worker has a hard maximum of ten claims per invocation.
- [x] No unbounded polling loop or permanent worker heartbeat is introduced.

## Acceptance status

Implemented and focused validation passed. Merge and the reviewed manual Terraform deployment remain required before live backlog recovery is available.

## Tests / validation performed

See `docs/test/test128.md`.

## Evidence files produced

- `docs/tickets/ticket128.md`
- `docs/test/test128.md`

## Boundaries

This change changes worker scheduling only. It does not expand customer-cloud permissions or alter any Terraform action.

## Follow-up work

- Deploy and confirm the existing customer verification backlog is consumed.
