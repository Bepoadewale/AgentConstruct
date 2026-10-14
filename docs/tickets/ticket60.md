# ticket60 — Workspace navigation and plan visualizations

PR: [#60 — feat: add workspace navigation and plan visualizations](https://github.com/Bepoadewale/AgentConstruct/pull/60)

Branch: `feature/ui-workspace-ux`

Status: ready for review

## Problem / goal

The first UI shell pass established visual foundations. Finish the product-level interaction
surfaces without gradients or decorative AI effects: workspace navigation, onboarding, quick
actions, architecture visualization and lifecycle status.

## Current repo state

- PR #59 added the flat visual shell, responsive styling and preserved existing element IDs.
- The app still has one long page and no workspace shortcut rail, command palette, architecture
  map or visible plan lifecycle timeline.

## Research / references used

- Render dashboard patterns: https://render.com/docs/render-dashboard
- Vercel dashboard navigation: https://vercel.com/changelog/dashboard-navigation-redesign-rollout
- Pulumi Cloud concepts: https://www.pulumi.com/docs/iac/concepts/pulumi-cloud/
- AWS SaaS Lens customer experience: https://docs.aws.amazon.com/wellarchitected/latest/saas-lens/general-design-principles.html

## Work planned for the PR

- Add a flat-color workspace shortcut rail and onboarding checklist.
- Add keyboard-accessible quick actions and command palette.
- Add architecture resource-flow visualization from the selected plan.
- Add plan lifecycle timeline tied to draft/submitted/approved/observed state.
- Keep the local/cloud evidence boundary explicit and preserve existing API behavior.

## Acceptance criteria

- [x] No gradients or decorative AI visual effects are used.
- [x] Existing API actions and JavaScript element IDs remain compatible.
- [x] Sidebar shortcuts, onboarding links and command palette work locally.
- [x] Architecture map renders from actual selected-plan components.
- [x] Lifecycle timeline reflects the current plan state.
- [x] Responsive and reduced-motion behavior remains available.

## Acceptance status

Met for the local workspace interaction and visualization surfaces.

## Tests / validation performed

```bash
node --check apps/web/app.js
make lint
make test
python3 scripts/check_doc_conventions.py
git diff --check
```

Results: 145 tests passed; JavaScript syntax, lint, documentation and diff checks passed.

## Evidence files produced

No customer workload or AWS execution occurs; no `docs/test/test60.md` is produced.

## Boundaries

This PR does not add a frontend framework, real sign-in, cloud deployment or hosted visual telemetry.

## Follow-up work

Add browser screenshot regression and remote design-token instrumentation when the web runtime is hosted.
