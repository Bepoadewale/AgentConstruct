# ticket77: Enforce the PR-only repository workflow

- PR: #77
- Branch: `docs/pr-only-workflow-77`
- Status: complete

## Problem / goal

The repository prohibited direct pushes to `main`, but the rule did not define
the complete branch, draft-PR, validation, merge, incident, and cleanup sequence.
A documentation-only provider decision was consequently committed directly to
`main` as `b0f5bed`.

The goal is to make the PR-only workflow explicit enough that contributors and
agents consistently follow it.

## Current repo state

- `AGENTS.md` says not to push directly to `main`.
- Every PR requires a PR-numbered ticket under `docs/tickets/`.
- GitHub requires a branch to differ from `main` before it can open a draft PR.
- Historical tickets 68–76 were committed directly to `main` without matching
  GitHub PRs. Closed PRs #68 and #69 exposed the collision; closed reconciliation
  issues #70–#76 preserve the numbering, allowing this change to use PR #77
  without overwriting any historical ticket.

## Research / references used

- Repository-local `AGENTS.md` development and PR-ticket rules.
- Repository-local `docs/tickets/README.md` ticket conventions.
- GitHub's observed requirement that a PR branch differ from its base branch.

## Work planned for the PR

- State that all repository changes use focused branches and GitHub PRs.
- Require checks and review before `main` changes.
- Define the minimal bootstrap commit needed to obtain a PR number.
- Define direct-push incident handling and prohibit unrequested history rewrites.
- Require pre-merge readiness checks and post-merge branch cleanup.

## Acceptance criteria

- The rule covers code, documentation, configuration, tests, and cleanup.
- Draft-PR and ticket sequencing handles GitHub's initial-commit constraint.
- Direct-to-main incidents have a safe, transparent response.
- Merge readiness and branch cleanup expectations are explicit.
- Documentation convention checks pass.

## Acceptance status

- [x] All repository change types are covered.
- [x] Draft-PR and ticket sequencing is defined.
- [x] Incident handling is defined.
- [x] Merge readiness and cleanup are defined.
- [x] Documentation convention checks pass.

## Tests / validation performed

- `uv run python scripts/check_doc_conventions.py`
- `git diff --check`

## Evidence files produced

None. This PR changes repository process documentation only.

## Boundaries

- No application behavior, provider configuration, credentials, or AWS resources
  are changed.
- Shared Git history is not rewritten.

## Follow-up work

- Configure GitHub branch protection or a ruleset for `main` when repository
  permissions allow it, so the documented workflow is also server-enforced.
