# ADR-009: Keep the V1 frontend as plain JavaScript

## Status

Superseded by [ADR-012](ADR-012-separated-static-frontend.md). This file is
retained as the historical V1 decision.

## Context

The V1 UI is one small product workflow. Adding a TypeScript/React build would add a package manager, lockfile, build pipeline and dependency surface without improving the current evidence.

## Decision

Keep the browser UI as checked-in HTML, CSS and JavaScript for V1. It is tested through API/local demo evidence and basic browser-contract checks. Move to a typed frontend only when the product needs multiple authenticated views, shared state or a component system.

## Consequences

There is no frontend compiler/type-checking step today. The UI must stay small, use accessible labels and avoid putting privileged logic in the browser.
