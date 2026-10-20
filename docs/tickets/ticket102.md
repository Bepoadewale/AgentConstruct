# ticket102

PR: #102
Branch: `fix/profile-aware-fixture-metadata`

## Problem / goal

Ensure bounded fixture execution reports the resource family selected by the approved architecture
profile instead of labelling every simulated resource as App Runner.

## Current repo state

The production Lambda worker can now complete bounded fixture execution without network, shell, or
cloud authority. A live Lambda-profile journey revealed that its simulated output still used an
App Runner output name, ARN, and resource type.

## Research / references used

- `AGENTS.md` truthfulness and fixture-labelling rules.
- The four implemented AWS execution profiles.
- PR #101 live production evidence.

## Work planned for the PR

- Map each implemented architecture profile to matching simulated output and resource metadata.
- Use provider-neutral fixture references for unknown future profiles.
- Share the mapping between embedded and local HTTP fixture executors.
- Add regression tests and run one complete clean-room cycle.

## Acceptance criteria and status

- [x] Lambda plans report Lambda fixture metadata without App Runner labels.
- [x] App Runner, ECS, and EKS profiles report their matching resource families.
- [x] Unknown profiles remain explicitly simulated and provider-neutral.
- [x] Local and embedded executors share one mapping.
- [x] One complete clean-room validation cycle passes.

## Acceptance status

All PR acceptance criteria are met.

## Tests / validation performed

Focused Ruff and six embedded-executor tests passed. One clean-room cycle passed from a clean
bootstrap through smoke, API contract, simple, complex, degraded, Day-2, canonical,
policy-failure, readiness-failure, customer-plan E2E, seeded-data persistence after API restart,
trace verification, Ruff, 241 tests, OpenAPI snapshot, Compose configuration, OPA 3/3, and all
Terraform roots. Final cleanup removed the local containers, network, volume, virtual environment,
and generated local state. The only warning was the existing upstream Starlette `httpx`
deprecation warning.

## Evidence files produced

- `docs/test/test102.md`

## Boundaries

All resource identifiers remain deterministic fixture evidence. This PR does not provision or
delete a customer cloud workload.

## Follow-up work

After merge, deploy the reviewed Lambda package through the saved-plan workflow and record a fresh
live authenticated journey in a separate PR-numbered evidence change.
