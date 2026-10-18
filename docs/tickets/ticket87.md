# ticket87: Trust the immutable GitHub OIDC subject

PR: #87

Branch: `fix/immutable-github-oidc-subject`

## Problem / goal

The first manual staging plan failed closed because GitHub issued an immutable customized OIDC
subject containing owner and repository IDs, while the new roles trusted the standard name-only
subject. Align both roles with the exact subject observed in AWS CloudTrail and record the
post-merge bootstrap operations.

## Current repo state

PR #86 merged and its exact reviewed prerequisite plan was applied. Both artifact buckets, both
KMS keys, and both GitHub workflow roles exist. GitHub environments and variables are configured.
No serverless control-plane resource has been applied.

## Research / references used

- AWS CloudTrail `AssumeRoleWithWebIdentity` denial events.
- Live IAM trust policies for both workflow roles.
- GitHub OIDC subject customization and environment subject behavior.

## Work planned for the PR

- Parameterize the immutable repository subject prefix.
- Restrict plan and apply role trust to their exact environment subjects.
- Add regression coverage and operator documentation.
- Re-run validation, merge, apply only the trust-policy correction, and retry manual plan.

## Acceptance criteria

- [x] Trust uses owner and repository IDs observed in CloudTrail.
- [x] Plan and apply environments remain distinct.
- [x] No wildcard subject is introduced.
- [x] Required local validation passes.
- [x] Required GitHub checks pass.
- [ ] Post-merge Terraform changes only the two trust policies.
- [ ] Manual staging plan succeeds without applying the control plane.

## Acceptance status

Implementation plus local and GitHub validation are complete. Post-merge operational checks remain
pending and will be recorded in a follow-up PR.

## Tests / validation performed

- One clean-room cycle passed from clean through final clean.
- Smoke, simple, complex, degraded, Day-2, policy-failure, readiness-failure, and trace checks
  passed.
- `make verify`: 224 passed with one dependency deprecation warning.
- `make terraform-validate`: all 12 roots passed.
- Authenticated plan: 0 additions, 2 trust-policy updates, 0 destroys.

## Evidence files produced

- `docs/test/test87.md`

## Boundaries

- The failed plan created no release or plan object because OIDC authentication failed first.
- This PR must not run the serverless-control-plane apply workflow.
- Only workflow support resources and encrypted artifacts may remain.

## Follow-up work

Review the successful saved staging plan before separately authorizing any control-plane apply.
