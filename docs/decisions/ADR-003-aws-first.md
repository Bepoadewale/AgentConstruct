# ADR-003: AWS first, provider-neutral interfaces

## Context

Early customers need one credible path, not shallow multi-cloud claims.

## Decision

Use AWS concepts in V1 planning while keeping intent, cost and execution interfaces provider-neutral.

## Alternatives

Build GCP/Azure support now, or couple all domain models to AWS resources.

## Consequences

The catalogue is intentionally small and auditable. Other clouds are roadmap work.

## Security and operations

Future AWS access uses customer-scoped short-lived role credentials, not long-lived keys.
