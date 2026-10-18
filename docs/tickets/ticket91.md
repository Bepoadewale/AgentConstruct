# ticket91
PR: #91
Branch: feat/davdeploy-rebrand

## Problem / goal

Rename the product and backend repository-facing configuration from AgentConstruct to davdeploy, prepare the external repository rename safely, and configure every currently knowable GitHub environment value without inventing unavailable credentials.

## Current repo state

The backend repository, Python package, infrastructure defaults, API contract, documentation, and deployment configuration use the former AgentConstruct name. Existing AWS prerequisite resources and GitHub environment variables also use former-name physical identifiers. The repository is on a focused branch with draft PR #91.

## Research / references used

- Repository `AGENTS.md` and current architecture and operations documentation.
- Existing Terraform bootstrap and production workflow configuration.
- Current GitHub environment configuration and AWS prerequisite inventory.
- GitHub repository rename and OIDC trust behavior, verified against the repository's immutable-subject implementation.

## Work planned for the PR

- Rename current product, package, API, infrastructure, automation, and documentation identifiers to davdeploy where safely upgradeable.
- Update synchronized API contracts and compatibility tests.
- Preserve immutable historical evidence and explicitly document any transitional physical cloud identifiers.
- Add or update GitHub environment values that are presently knowable.
- Document unavailable third-party credentials and post-deployment outputs as narrow follow-up inputs.
- Validate the backend through the required single clean-room cycle.

## Acceptance criteria

- Current backend source and product documentation use davdeploy.
- The backend remains independently installable, testable, and deployable.
- Terraform and GitHub automation remain safe across the repository rename.
- No secrets are committed or exposed.
- Known GitHub environment values are configured and missing values are documented truthfully.
- Required clean-room validation passes once from a clean state.

## Acceptance status

- In progress.

## Tests / validation performed

- Pending implementation.

## Evidence files produced

- `docs/test/test91.md` will record the clean-room validation.

## Boundaries

- No Terraform apply or billable cloud deployment is authorized by this PR.
- Missing Google OAuth and email-delivery credentials will not be fabricated.
- Existing stateful AWS prerequisites will only be changed through a recoverable migration path.
- Historical tickets and test evidence remain immutable records of the former product name.

## Follow-up work

- Rename the GitHub repository after this PR is merged.
- Update live external integrations whose identifiers can only change after the repository rename.
