# ticket121

PR: #121
Branch: `docs/120-domain-email-checklist`

## Problem / goal

Keep the domain-dependent Amazon SES activation work visible in the current product roadmap without enabling email delivery before DavDeploy owns a production domain.

## Current repo state

The bounded SES invitation adapter, identity-scoped IAM contract, invitation lifecycle, and failure states are implemented. Production invitation delivery remains disabled because there is no verified sender domain or SES production-sending approval.

## Research / references used

- Existing invitation sender and serverless Terraform contracts.
- `docs/TERRAFORM_GITHUB_OPERATIONS.md` and `docs/CONFIGURATION_SECURITY.md`.
- AWS SES identity verification, suppression-list, and production-access requirements.

## Work planned for the PR

- Add a concise post-domain SES activation checklist to the current roadmap.
- Preserve manual Terraform plan and apply gates.
- Preserve the current fail-closed invitation boundary until live delivery is verified.

## Acceptance criteria

- The roadmap identifies DNS, SES production access, suppression, GitHub secrets, deployment, and end-to-end validation.
- The checklist is explicitly deferred until a production domain exists.
- No provider setting, secret, infrastructure, or runtime is changed.

## Acceptance status

All documentation acceptance criteria are met. Required GitHub CI remains the merge gate.

## Tests / validation performed

- `python3.12 scripts/check_doc_conventions.py`
- `git diff --check`

## Evidence files produced

- This PR ticket and the updated current product roadmap.

## Boundaries

Documentation only. No domain, DNS record, SES identity, credential, email, cloud resource, or application configuration is created or changed.

## Follow-up work

Execute the roadmap checklist through a separately reviewed PR after the production domain is available.
