# ADR-007: Start as a modular monolith

## Context

A solo-founder V1 needs simple operations and fast testing.

## Decision

Keep domain components in one deployable API with explicit module boundaries.

## Alternatives

Deploy a separate service for every logical capability.

## Consequences

Components can be extracted later when execution load requires it.

## Security and operations

Fewer trust boundaries make the local proof smaller and easier to observe.
