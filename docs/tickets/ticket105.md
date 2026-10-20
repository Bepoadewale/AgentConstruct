# ticket105

PR: #105
Branch: `fix/supply-chain-scan-config`

## Problem / goal

Fix the pre-existing Trivy workflow warning discovered during PR #104 so both HIGH and CRITICAL
findings are passed as one valid severity input, and update the scanner action from the obsolete
`v0.9.2` release.

## Current repo state

CI passes, but GitHub reports `HIGH` as an unexpected standalone action input because the unquoted
comma-separated severity value is parsed incorrectly in the YAML flow mapping. The Trivy action is
also many releases behind the current official release.

## Research / references used

- GitHub run `39473857915` annotations.
- Official `aquasecurity/trivy-action` latest release API, reporting `v0.36.0` published
  2026-04-22.
- Trivy action input contract for `severity`.

## Work planned for the PR

- Update `aquasecurity/trivy-action` to `v0.36.0`.
- Express its inputs as normal YAML keys and quote `CRITICAL,HIGH`.
- Verify the supply-chain job runs without the unexpected-input warning.

## Acceptance criteria

- Trivy receives `CRITICAL,HIGH` as one severity value.
- The current supported Trivy action release runs successfully.
- Required CI passes without the prior `Unexpected input(s) 'HIGH'` annotation.

## Acceptance status

In progress.

## Tests / validation performed

Pending.

## Evidence files produced

No customer workload evidence is required. This PR only repairs CI scanner configuration.

## Boundaries

This PR does not change application runtime, AWS infrastructure, Terraform state, or customer
workloads.

## Follow-up work

Pending implementation and CI.
