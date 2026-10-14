# ticket65 — Screen-based product navigation, history, and filtering

- PR: https://github.com/Bepoadewale/AgentConstruct/pull/65
- Branch: `feature/ui-screen-navigation-and-history`
- Status: ready for review

## Problem / goal

The previous UI presented nearly the entire product as one long scrolling document. That made history, review, activity, and planning compete for attention and made the product feel like an internal demo instead of a customer application.

## Current repo state

The merged UI already had a workspace sidebar, command palette, plan visualization, mobile navigation, status treatment, and design tokens. It did not yet use those destinations as real screens, and there was no separate filtered plan-history view or filtered activity view.

## Research / references used

- Material navigation guidance: https://m1.material.io/patterns/navigation.html
- Material navigation hierarchy: https://m2.material.io/design/navigation/
- Carbon data-table accessibility: https://www.carbondesignsystem.com/building-blocks/core/components/data-table/accessibility
- GOV.UK pagination/filtering guidance: https://design-system.service.gov.uk/components/pagination/
- Atlassian navigation system: https://atlassian.design/components/navigation-system/migration-guide

## Work planned for the PR

- Turn top-level destinations into true screens: Overview, New plan, Plan, Review, History, and Activity.
- Add a dedicated plan-history screen with search and state filtering.
- Add a dedicated activity screen with event-type and text filters.
- Add explicit forward navigation from generated plan to review.
- Keep the existing API and governed workflows unchanged.
- Preserve responsive mobile navigation and flat-color visual language.

## Acceptance criteria

- [ ] The app no longer renders every major surface as one long page.
- [ ] Sidebar, header, mobile navigation, and command actions open the same screen destinations.
- [ ] Plan history is separate from activity and supports search/status filtering.
- [ ] Activity is separate from history and supports text/event filtering.
- [ ] A generated plan can open its review explicitly.
- [ ] Existing plan generation, approval, dry-run, and destroy flows remain functional.
- [ ] Screen changes do not create AWS resources or alter backend authorization.
- [ ] No gradients or decorative AI effects are introduced.

## Acceptance status

Pending CI and review.

## Tests / validation performed

- `node --check apps/web/app.js`
- `make lint`
- `make test`
- `make smoke`
- `make browser-contract`
- `make customer-plan-e2e`
- `python3 scripts/check_doc_conventions.py`
- `git diff --check`
- `rg -n "gradient|linear-gradient|radial-gradient" apps/web`

## Evidence files produced

No `docs/test/test65.md`: this is a local UI navigation change with no customer workload or AWS execution.

## Boundaries

No backend schema, authentication, GitHub write, AWS, Terraform, or deployment behavior changes.

## Follow-up work

Screenshot-level browser QA remains dependent on the host CUA connector restoring its missing internal module. Further visual changes should preserve this screen model rather than returning to long-scroll composition.
