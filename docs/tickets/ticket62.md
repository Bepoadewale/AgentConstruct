# ticket62 — UI accessibility and dynamic-content hardening

- PR: https://github.com/Bepoadewale/AgentConstruct/pull/62
- Branch: `feature/ui-accessibility-hardening`
- Status: ready for review

## Problem / goal

The core UI now has a polished product shell, but dynamic integration and audit content needed stronger accessibility announcements and consistent escaping before it is shown in the browser.

## Current repo state

PR61 added mobile navigation, plan highlights, digest copy, status chips, and plan-generation busy states. GitHub, AWS, audit, repository, and branch values still entered the DOM through interpolated markup without a single escaping boundary, and several status surfaces were not announced to assistive technology.

## Research / references used

- AWS SaaS Lens customer experience: https://docs.aws.amazon.com/wellarchitected/latest/saas-lens/general-design-principles.html
- Pulumi Cloud concepts: https://www.pulumi.com/docs/iac/concepts/pulumi-cloud/

## Work planned for the PR

- Escape dynamic GitHub, AWS, repository, branch, and audit values before HTML insertion.
- Add live-region semantics to workflow status and audit surfaces.
- Keep behavior and API contracts unchanged.

## Acceptance criteria

- [ ] Dynamic integration and audit values are escaped before insertion.
- [ ] GitHub/AWS workflow messages and audit updates are announced politely.
- [ ] Existing plan, approval, and execution behavior remains unchanged.
- [ ] No gradient or decorative AI styling is introduced.
- [ ] Local lint, tests, browser contract, and customer-plan E2E pass.

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

No `docs/test/test62.md`: no customer workload or AWS resource execution occurs in this UI-only PR.

## Boundaries

No backend, authentication, GitHub write, AWS, Terraform, or deployment behavior changes.

## Follow-up work

Visual browser regression screenshots and hosted UI deployment remain separate work.
