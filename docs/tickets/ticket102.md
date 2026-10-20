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

## Work to be done

- Map each implemented architecture profile to matching simulated output and resource metadata.
- Use provider-neutral fixture references for unknown future profiles.
- Share the mapping between embedded and local HTTP fixture executors.
- Add regression tests and run one complete clean-room cycle.
- Deploy the reviewed correction and repeat the live customer journey.

## Acceptance criteria and status

- [ ] Lambda plans report Lambda fixture metadata without App Runner labels.
- [ ] App Runner, ECS, and EKS profiles report their matching resource families.
- [ ] Unknown profiles remain explicitly simulated and provider-neutral.
- [ ] Local and embedded executors share one mapping.
- [ ] One complete clean-room validation cycle passes.
- [ ] Live post-deployment customer journey passes with governed teardown.

## Validation performed

Pending.

## Evidence files

- `docs/test/test102.md`

## Boundaries

All resource identifiers remain deterministic fixture evidence. This PR does not provision or
delete a customer cloud workload.

## Follow-up work

Pending final validation.
