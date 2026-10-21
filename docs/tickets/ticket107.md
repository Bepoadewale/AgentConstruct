# ticket107

PR: #107
Branch: `feat/106-public-github-planning`

## Problem / goal

Production uses the deterministic GitHub fixture until a GitHub App is configured. Authenticated
customers therefore cannot truthfully select and analyze an otherwise public repository. Add a
bounded public-repository reader without weakening private-repository authorization.

## Current repo state

The GitHub integration supports deterministic fixtures and an installation-scoped GitHub App.
Repository discovery delegates entirely to that configured adapter.

## Research / references used

- Existing `GitHubConnection` and `GitHubAppReadOnlyConnection` contracts.
- GitHub REST repository, branch, and contents endpoints.
- Existing repository-analysis evidence and tenant-scoped planning flow.

## Work planned for the PR

- Add a canonical-URL, public-only GitHub reader.
- Add an authenticated inspection endpoint.
- Route non-installed public repositories through real bounded evidence collection.
- Retain fixture and GitHub App behavior for their authorized repositories.
- Update OpenAPI and regression coverage.

## Acceptance criteria

- Only canonical `https://github.com/owner/repository` URLs are accepted.
- GitHub must explicitly report the repository as public.
- Requests carry no GitHub credential and never write to GitHub.
- Bounded manifest evidence is marked `EXECUTED_PUBLIC_READ_ONLY`.
- Existing integration behavior and full validation remain green.
- No customer infrastructure is executed or deployed.

## Acceptance status

Implementation, direct public-repository evidence, focused tests, and one clean-room cycle are
complete. Production customer evidence follows the reviewed deployment.

## Tests / validation performed

See `docs/test/test107.md`.

## Evidence files produced

- `docs/test/test107.md`

## Boundaries

This capability reads public repository metadata, branches, and a fixed manifest allowlist. It does
not read arbitrary source files, use credentials, write repositories, or request cloud execution.

## Follow-up work

Configure the GitHub App for private customer repositories.
