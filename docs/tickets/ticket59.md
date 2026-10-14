# ticket59 — Product UI shell and interaction polish

PR: product UI shell and interaction polish

Branch: `feature/ui-product-shell`

Status: ready for review

## Problem / goal

The local product flow is functional, but the plain form layout does not yet communicate
the confidence and clarity of a modern developer platform. Upgrade the visual hierarchy
and interaction surfaces without changing API contracts or product truth boundaries.

## Current repo state

- `apps/web` is a plain JavaScript application with working plan, review, audit and
  local-execution actions.
- Existing element IDs are used by `app.js`; the redesign must preserve them.
- No component framework or build step is required for this phase.

## Research / references used

- Render dashboard patterns: https://render.com/docs/render-dashboard
- Vercel dashboard navigation redesign: https://vercel.com/changelog/dashboard-navigation-redesign-rollout
- Pulumi Cloud concepts: https://www.pulumi.com/docs/iac/concepts/pulumi-cloud/
- AWS SaaS Lens customer experience principles: https://docs.aws.amazon.com/wellarchitected/latest/saas-lens/general-design-principles.html

## Work planned for the PR

- Add a modern product shell, workspace context, journey stepper and dashboard summary hierarchy.
- Add accessible skip/navigation/status affordances while preserving existing actions.
- Redesign typography, spacing, cards, form controls, review surfaces and responsive behavior.
- Keep local/simulated/cloud evidence labels explicit.

## Acceptance criteria

- [x] Existing UI actions and element IDs remain compatible with `app.js`.
- [x] The primary journey is visually ordered: Connect, Describe, Review, Govern, Observe.
- [x] Dashboard state and next actions are easier to scan.
- [x] Review and audit surfaces distinguish state, evidence and boundary messaging.
- [x] Responsive and reduced-motion styles are included.
- [x] No product claim or API behavior is changed.

## Acceptance status

Met for the local product shell and interaction polish. Browser visual review remains local evidence.

## Tests / validation performed

```bash
make lint
make test
python3 scripts/check_doc_conventions.py
git diff --check
```

Results: expected 145 tests; lint, tests and documentation checks must pass.

## Evidence files produced

No customer workload or AWS execution occurs; no `docs/test/test59.md` is produced.

## Boundaries

This PR does not introduce a frontend framework, real authentication, cloud deployment or production visual telemetry.

## Follow-up work

Add browser screenshot regression and hosted design-token instrumentation when the control plane has a deployed web runtime.
