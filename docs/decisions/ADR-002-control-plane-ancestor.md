# ADR-002: Use AI Platform Control Plane as the governance ancestor

## Context

The public control plane has the strongest executed governance and cloud-pilot evidence.

## Decision

Adapt its patterns: signed identity, tenant binding, OPA, immutable plans, independent approval, durable audit, observed state and governed destruction.

## Alternatives

Copy an entire public repository or start with an ungoverned LLM/Terraform agent.

## Consequences

AgentConstruct reuses patterns, not a fork. It remains coherent as a commercial product.

## Security and operations

No user or LLM receives raw infrastructure authority.
