# ticket67 — Readable plan review surface

- PR: pending
- Branch: `fix/readable-plan-review`
- Status: in progress

## Problem / goal

The Review screen still presented application analysis, AWS targets, observability, cost, deployment strategy, and risks as raw JSON. That is useful for debugging but not for a customer or administrator reviewing an infrastructure decision.

## Current repo state

The plan review workflow is functional and the data is typed, but most review sections use `<pre>` blocks. Users must parse implementation-shaped JSON instead of seeing labeled facts, lists, and decisions.

## Research / references used

- Material information hierarchy: https://m2.material.io/design/navigation/
- Carbon data table/accessibility guidance: https://www.carbondesignsystem.com/building-blocks/core/components/data-table/accessibility
- GOV.UK progressive disclosure patterns: https://design-system.service.gov.uk/components/

## Work planned for the PR

- Render review objects as readable labeled pairs and lists.
- Keep complete canonical JSON available behind collapsed technical-details disclosures.
- Preserve exact digest, immutable review, approval, and deployment-boundary behavior.
- Add responsive styles for long values and nested lists.

## Acceptance criteria

- [ ] Review does not show raw JSON by default for major plan sections.
- [ ] Application, target, observability, cost, deployment, and risk data remain complete and readable.
- [ ] Technical details remain available without changing the canonical plan.
- [ ] Long values wrap safely on desktop and mobile.
- [ ] Existing approval, dry-run, destroy, and audit flows remain unchanged.
- [ ] No AWS resources or credentials are created or changed.

## Acceptance status

Pending CI and review.

## Tests / validation performed

- `node --check apps/web/app.js`
- `make lint`
- `make test`
- `make smoke`
- `make browser-contract`
- `make customer-plan-e2e`
- `git diff --check`

## Evidence files produced

No `docs/test/test67.md`: this is a local review-presentation change with no customer workload or AWS execution.

## Boundaries

No backend schema, authentication, GitHub write, AWS, Terraform, or deployment behavior changes.

## Follow-up work

Screenshot-level browser QA remains dependent on the host CUA connector restoring its missing internal module.
