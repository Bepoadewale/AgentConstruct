# ADR-005: LLMs cannot mutate infrastructure directly

## Context

Generated text cannot be trusted as privileged execution authority.

## Decision

LLMs and fixtures propose only. Policy, approval and a bounded deterministic executor control mutations.

## Alternatives

Let an agent run arbitrary shell, Terraform or `kubectl`.

## Consequences

The product is slower than unchecked automation for protected changes, but is reviewable and safer.

## Security and operations

The executor uses only explicit, audited integrations.
