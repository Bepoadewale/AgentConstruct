# ticket71 — Full-width workspace frame

- PR: #71
- Branch: main
- Status: complete

## Problem / goal

The latest local screenshot showed excessive unused space beside workspace surfaces. The shared product frame should use the available desktop canvas confidently on every screen while retaining readable content widths and mobile behavior.

## Current repo state

The product shell uses a fixed workspace sidebar and screen panels inside a capped global main container. That cap created a large right-side gutter on wide desktop windows.

## Research / references used

- Latest customer-provided local screenshot from 2026-10-14.
- Existing workspace shell CSS and responsive breakpoints.

## Work planned for the PR

- Remove the global desktop max-width constraint from the application frame.
- Make product screens fill the available area after the sidebar.
- Keep the sidebar offset and collapse cleanly below the desktop breakpoint.
- Tighten vertical frame padding to reduce dead space above content.

## Acceptance criteria

- Desktop screens use the available width without a large right gutter.
- Sidebar and content remain aligned.
- Responsive screens remain full width when the sidebar collapses.
- Existing tests and local service checks pass.

## Acceptance status

- [x] Full-width desktop frame
- [x] Sidebar-aware content width
- [x] Responsive fallback
- [x] Validation complete

## Tests / validation performed

Run after implementation: `node --check apps/web/app.js`, `make lint`, `make test`, `make smoke`, `make browser-contract`, `make customer-plan-e2e`, `python3 scripts/check_doc_conventions.py`, and `git diff --check`.

## Evidence files produced

- This ticket records the screenshot-driven layout change.

## Boundaries

This is a local UI layout adjustment. It does not create AWS resources or change cloud credentials.

## Follow-up work

Capture a fresh desktop and mobile screenshot after the next local browser session for visual confirmation.
