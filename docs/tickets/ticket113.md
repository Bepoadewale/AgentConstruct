# ticket113

PR: #113
Branch: `fix/112-refresh-release-oidc`

## Problem / goal

PR #111 added a least-privilege migration invocation policy during Terraform apply. The first apply
session was issued before that new identity policy existed, so AWS correctly denied migration
invocation for the already-running session. Refresh the short-lived OIDC session after apply and
before the migration gate.

## Current repo state

Terraform apply run `39652878720` completed the reviewed saved plan, including the migration-only
invoke policy and in-place Lambda updates. Its following migration step failed closed with
`AccessDeniedException`. The control-plane schema remains unmigrated, and the invitation endpoint
still fails safely rather than claiming success.

## Research / references used

- AWS IAM session permissions are established when the role session is issued.
- Existing GitHub OIDC apply role and `aws-actions/configure-aws-credentials` integration.
- Failed apply run `39652878720` and its exact AWS authorization error.

## Work planned for the PR

- Reassume the same apply role after Terraform finishes.
- Clear the current temporary credentials before obtaining the new OIDC session.
- Keep migration invocation after the credential refresh.
- Add regression tests for exact workflow order and two credential configurations.
- Repeat the reviewed production plan/apply and authenticated live checks.

## Acceptance criteria

- The workflow uses a fresh short-lived apply session for migration invocation.
- The refresh occurs only after the saved plan is applied.
- Migration verification remains mandatory and fail-closed.
- Production invitations list successfully after the release.
- No customer workload is deployed or executed.

## Acceptance status

Implementation and local validation are complete. GitHub CI and the reviewed production retry
remain pending.

## Tests / validation performed

Focused workflow tests and one complete clean-room cycle passed. See `docs/test/test113.md`.

## Evidence files produced

- `docs/test/test113.md`

## Boundaries

The refreshed role is the same reviewed, least-privilege GitHub OIDC apply role. No long-lived AWS
credential is created or exposed.

## Follow-up work

None identified yet.
