# ADR-004: Convert natural language into typed plans

## Context

Natural language is useful for describing an outcome but ambiguous for security and cost decisions.

## Decision

Convert input into a validated `WorkloadSpec`, retain unknown material facts, and build typed architecture and deployment plans.

## Alternatives

Execute text directly or silently guess critical values.

## Consequences

The UI can ask for missing material information later; deterministic tests can cover the planning path.

## Security and operations

Typed values are policy inputs and audit evidence.
