# ticket104

PR: #104
Branch: `chore/config-security-validation-policy`

## Problem / goal

Audit GitHub Actions configuration after the repository became public, keep sensitive values in
GitHub Secrets, document why public browser configuration cannot be secret, and replace the
blanket local clean-room gate with risk-based validation.

## Current repo state

The Terraform workflows use environment-scoped variables for deployment metadata and an
environment secret for the budget notification address. The contributor guide requires a full
local clean-room cycle for every runnable change, even when focused tests and required CI provide
proportionate evidence.

## Research / references used

- GitHub Actions variables and secrets documentation.
- Current `terraform-plan` and `terraform-apply` environment configuration names.
- Workflow references under `.github/workflows/`.
- Existing CI, PR template, and validation documentation.

## Work planned for the PR

- Record a value-free classification of every Actions configuration name.
- Keep secrets and non-secret configuration in their correct GitHub stores.
- Repair any required non-secret Terraform environment configuration found missing by the audit.
- Add checks that prevent known sensitive names from being referenced through `vars`.
- Make local clean-room validation mandatory only for high-risk and release changes.
- Preserve required CI and targeted local testing for every runnable PR.

## Acceptance criteria

- Public visitors cannot obtain sensitive values from repository configuration or source.
- Sensitive configuration uses the `secrets` context and non-sensitive metadata uses `vars`.
- Browser-embedded public configuration is explicitly documented as public.
- Terraform workflows retain all required environment configuration.
- CI detects obvious secret-to-variable regressions.
- The validation policy is clear, proportionate, and enforceable.

## Acceptance status

Complete. The value-free audit classified every workflow reference. The only sensitive configured
value was already stored as a GitHub environment secret. No credential migration was necessary.
The two required state configuration variables that were absent from `terraform-plan` were restored
as non-secret environment variables.

## Tests / validation performed

- Listed repository and environment variable and secret names without printing their values.
- Confirmed the frontend repository has no GitHub Actions variables or secrets.
- `make config-check`: passed with 15 classified metadata names and one classified secret name.
- `python3 scripts/check_doc_conventions.py`: passed.
- `python3 -m py_compile scripts/check_actions_configuration.py`: passed.
- `git diff --check`: passed.
- Searched tracked non-evidence files for the Cloudflare token prefix: no matches.
- The local clean-room gate was not due because this PR changes static policy, documentation, and
  CI configuration validation, not runtime product, database, worker, provider, or Terraform code.
  Required CI supplies the fresh-runner integration gate.

## Evidence files produced

No customer workload evidence is required. This PR changes documentation, policy, and static
configuration validation only.

## Boundaries

This PR does not rotate credentials, change AWS infrastructure, dispatch Terraform, or expose
configuration values in repository files or logs.

## Follow-up work

Required PR CI remains pending.
