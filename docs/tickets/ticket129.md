# ticket129: Reconcile CodeBuild completion events from their ARN form

PR: #129
Branch: fix/codebuild-completion-identifiers

## Problem / goal

EventBridge emits the CodeBuild ARN while the execution adapter stores CodeBuild's short build ID. The trusted worker could receive a completion event but fail to find the submitted run.

## Current repo state

The runner produces integrity-checked result artifacts and EventBridge delivers completion events to SQS. Reconciliation matches only a short ID.

## Research / references used

- Existing CodeBuild adapter output shape.
- Existing EventBridge completion handler.
- AWS CodeBuild ARN shape in the live completion event.

## Work planned for the PR

- Normalize the final build identifier path segment for CodeBuild API lookup.
- Match either the persisted short ID or persisted build ARN.
- Add a regression test covering the EventBridge ARN.

## Acceptance criteria

- [x] A CodeBuild ARN completion event reconciles the correct submitted run.
- [x] CodeBuild is queried using the normalized short ID.
- [x] No arbitrary build is accepted; only a stored submitted run matches.

## Acceptance status

Implemented and focused validation passed. Merge and a reviewed manual Terraform deployment remain required before the live completion event can reconcile the existing saved plan.

## Tests / validation performed

See `docs/test/test129.md`.

## Evidence files produced

- `docs/tickets/ticket129.md`
- `docs/test/test129.md`

## Boundaries

This fixes completion identity matching only. It does not change runner permissions or make a plan/apply/destroy decision.

## Follow-up work

- Deploy and reconcile the already completed authenticated customer plan artifact.
