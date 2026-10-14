# ticket70 — Premium workflow pass

- PR: #70
- Branch: main
- Status: complete

## Problem / goal

Make the core workspace feel like a premium, high-trust product by reducing navigation noise, clarifying next actions, making history and activity easier to scan, and keeping advanced planning constraints available without overwhelming the first step.

## Current repo state

The local demo has a shared navigation shell, plan history, audit activity, customer review, and a local-only execution boundary. This pass keeps those contracts intact while improving the presentation layer.

## Research / references used

- Existing local screenshots supplied by the customer.
- Existing browser contract, smoke, and customer-plan E2E tests.
- Current AgentConstruct information architecture and design tokens.

## Work planned for the PR

- Group plan history into readable revision clusters and add a compact density mode.
- Add activity event detail inspection without leaving the activity page.
- Group advanced plan constraints behind progressive disclosure.
- Make review actions state-specific with explicit next-step guidance.
- Reduce primary header navigation duplication and improve responsive drawer behavior.

## Acceptance criteria

- History is scannable by revision cluster and supports comfortable/compact density.
- Activity rows are keyboard-focusable and expose full event details in a dismissible drawer.
- New-plan essentials remain visible while advanced constraints are collapsible.
- Review state always explains the next operator action.
- Existing APIs and browser contracts continue to pass.

## Acceptance status

- [x] History revision grouping and density control
- [x] Activity detail drawer
- [x] Progressive disclosure for advanced constraints
- [x] Review next-step guidance
- [x] Navigation and responsive polish

## Tests / validation performed

Run after implementation: `node --check apps/web/app.js`, `make lint`, `make test`, `make smoke`, `make browser-contract`, `make customer-plan-e2e`, `python3 scripts/check_doc_conventions.py`, and `git diff --check`.

## Evidence files produced

- This ticket documents the implementation and validation boundary.

## Boundaries

This is a local product-demo UI pass. It does not create AWS resources, grant credentials, merge GitHub changes, or claim production deployment.

## Follow-up work

Continue with richer project-level history aggregation once the backend exposes a stable project key for every revision.
