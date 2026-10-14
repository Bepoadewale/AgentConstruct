# ticket66 — High-signal workspace overview and bounded activity surfaces

- PR: pending
- Branch: `fix/ui-information-density`
- Status: in progress

## Problem / goal

The screen navigation introduced in PR 65 still exposed raw arrays and an unbounded activity stream. The Overview joined every project, connection, and plan into running text, while Activity could become an overwhelming event dump. This makes the product feel like a debug console rather than a calm customer workspace.

## Current repo state

The app has separate Overview, History, Review, and Activity destinations, but Overview renders collection contents as comma-separated text. History and Activity have filters but no bounded page model. Branding also lacked consistent spacing between the mark and label.

## Research / references used

- Material navigation hierarchy: https://m2.material.io/design/navigation/
- Carbon data-table accessibility: https://www.carbondesignsystem.com/building-blocks/core/components/data-table/accessibility
- GOV.UK filtering and pagination: https://design-system.service.gov.uk/components/pagination/
- Atlassian navigation system: https://atlassian.design/components/navigation-system/migration-guide

## Work planned for the PR

- Replace collection dumps with numeric workspace metrics and compact recent-project/activity lists.
- Add bounded pagination to plan history and activity while preserving search and filters.
- Shorten sensitive/long digests in activity rows without removing the canonical value from review.
- Improve admin queue labels and empty states.
- Fix brand-mark spacing and add responsive dashboard list behavior.
- Preserve flat-color styling, governed workflows, and backend contracts.

## Acceptance criteria

- [ ] Overview never renders full project, connection, or plan arrays as a single text line.
- [ ] Overview shows counts plus compact recent items with links to History and Activity.
- [ ] History remains separate, searchable, filterable, and paginated.
- [ ] Activity remains separate, searchable, filterable, and paginated.
- [ ] Long plan digests are abbreviated in lists but remain copyable/canonical in review.
- [ ] Desktop and mobile layouts remain usable.
- [ ] No backend authorization, AWS, Terraform, or deployment behavior changes.
- [ ] No gradients or decorative AI effects are introduced.

## Acceptance status

Pending CI and review.

## Tests / validation performed

- `node --check apps/web/app.js`
- `make lint`
- `make smoke`
- `make browser-contract`
- `git diff --check`
- Served rebuilt Docker image and verified the new Overview markup/styles.

## Evidence files produced

No `docs/test/test66.md`: this is a local UI information-density change with no customer workload or AWS execution.

## Boundaries

No backend schema, authentication, GitHub write, AWS, Terraform, or deployment behavior changes.

## Follow-up work

Screenshot-level browser QA remains dependent on the host CUA connector restoring its missing internal module.
