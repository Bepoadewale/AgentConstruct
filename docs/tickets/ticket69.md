# ticket69 — Premium surface polish

- PR: #69
- Branch: `main`
- Status: complete

## Problem / goal

The refreshed product shell was strong, but the Review screen had no useful empty state, Connections appeared active alongside New plan, and the repeated evidence-boundary panel added visual noise to every screen.

## Current repo state

Navigation, history, activity, and review surfaces are functional and use the established compact design system.

## Research / references used

- Material information hierarchy: https://m2.material.io/design/navigation/
- GOV.UK progressive disclosure patterns: https://design-system.service.gov.uk/components/

## Work planned for the PR

- Remove the repeated evidence-boundary panel.
- Add a concise Review empty state with a direct History path.
- Prevent the secondary Connections shortcut from showing as a second active route.

## Acceptance criteria

- [x] Evidence-boundary panel is absent from all pages.
- [x] Review has a useful empty state before a plan is selected.
- [x] Only the current primary route is highlighted.
- [x] Existing plan, approval, execution, and audit behavior remains unchanged.
- [x] No AWS resources or credentials are created or changed.

## Acceptance status

Complete.

## Tests / validation performed

- `node --check apps/web/app.js`
- `make lint`
- `make test`
- `make smoke`
- `make browser-contract`
- `make customer-plan-e2e`
- `python3 scripts/check_doc_conventions.py`
- `git diff --check`

## Evidence files produced

No `docs/test/test69.md`: this is a local presentation change with no customer workload or AWS execution.

## Boundaries

No backend schema, authentication, GitHub write, AWS, Terraform, or deployment behavior changes.

## Follow-up work

Screenshot-level browser QA remains dependent on the host CUA connector restoring its missing internal module.
