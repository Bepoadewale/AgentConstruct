# ticket90: Select the production plan automatically

PR: #90

Branch: `feat/automatic-production-plan-selection`

## Problem / goal

The manual Terraform apply form currently asks the founder to copy a successful plan run ID and
run attempt. Remove those two operator inputs without weakening the saved-plan safety boundary.

## Current repo state

AgentConstruct has one production plan workflow and one production state. Apply requires an exact
run ID and attempt, verifies the selected GitHub run, downloads its encrypted manifest and plan,
checks the digest, and applies only the saved plan.

## Research / references used

- Current Terraform plan and apply workflow contracts.
- GitHub Actions workflow-runs API response fields and filtering behavior.
- Saved-plan manifest version 2 and production marker introduced by PR #89.

## Work planned for the PR

- Remove plan run ID and run-attempt inputs from the apply dispatch form.
- Resolve the newest successful manual plan for the exact current `main` commit.
- Fail closed if no matching plan exists.
- Retain workflow path, event, branch, attempt, manifest, digest, and production checks.
- Update tests and operator documentation.

## Acceptance criteria

- [ ] Apply asks only for the explicit confirmation phrase.
- [ ] Apply automatically selects a successful manual plan for the exact current `main` commit.
- [ ] A stale plan from an older commit cannot be selected.
- [ ] Manifest version, production marker, run identity, and digest remain verified.
- [ ] Operator documentation reflects the simplified form.
- [ ] One required clean-room validation cycle passes.
- [ ] Required GitHub checks pass.

## Acceptance status

Implementation and validation are pending.

## Tests / validation performed

Pending.

## Evidence files produced

- `docs/test/test90.md`

## Boundaries

- This PR must not run Terraform apply.
- This PR must not create or modify AWS resources.
- Automatic selection must fail closed rather than fall back to an older commit.
- The separate protected apply environment and founder review remain required.

## Follow-up work

After merge, run a new production plan from `main`. The apply form can then resolve it without
manual run identifiers.
