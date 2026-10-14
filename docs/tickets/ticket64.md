# ticket64 — UI design-system foundation and accessibility states

- PR: https://github.com/Bepoadewale/AgentConstruct/pull/64
- Branch: `feature/ui-design-system-foundation`
- Status: ready for review

## Problem / goal

The product UI needed a durable design-system foundation so future screens remain consistent, responsive, accessible, and operationally calm.

## Current repo state

PRs 60–62 established navigation, plan visualizations, status treatment, and dynamic-content safety. Shared design tokens, consistent focus/touch defaults, semantic feedback surfaces, and a written design contract were still implicit.

## Research / references used

- `design-ui-designer.md` from the repository’s design guidance.
- Render dashboard: https://render.com/docs/render-dashboard
- Pulumi Cloud concepts: https://www.pulumi.com/docs/iac/concepts/pulumi-cloud/

## Work planned for the PR

- Add semantic color, spacing, typography, focus, control-height, and transition tokens.
- Add consistent focus-visible, disabled, success, failure, empty, forced-colors, and mobile touch behavior.
- Add `docs/product/UI_DESIGN_SYSTEM.md` as the developer handoff contract.

## Acceptance criteria

- [ ] Shared tokens are defined in the web stylesheet.
- [ ] Keyboard focus is visibly identifiable across controls and links.
- [ ] Mobile controls meet 44px touch height.
- [ ] Success and failure states are visually distinct and readable.
- [ ] Reduced-motion and forced-colors preferences remain supported.
- [ ] No gradients or decorative AI effects are introduced.
- [ ] Design-system documentation matches implementation.

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

No `docs/test/test64.md`: this is a local UI/design-system change with no customer workload or AWS execution.

## Boundaries

No backend, authentication, GitHub write, AWS, Terraform, or deployment behavior changes.

## Follow-up work

Screenshot-based visual regression requires the host browser automation connector to restore its missing `@oai/cua/tinyskyAlt` module.
