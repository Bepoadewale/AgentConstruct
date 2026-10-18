# ticket89: Use one production control plane

PR: #89

Branch: `feat/single-production-control-plane`

## Problem / goal

AgentConstruct does not need separate staging and production control planes yet. Simplify the
manual Terraform workflow to one production deployment, one remote state object, one resource
namespace, and one Cognito domain.

## Current repo state

The plan workflow currently asks the operator to select `staging` or `production`, stores separate
state objects, and adds the environment name to resource and Cognito names. A staging plan exists,
but no serverless control-plane apply has ever run and neither state object exists.

## Research / references used

- Current Terraform plan and apply workflow contracts.
- Current serverless-control-plane Terraform variables and resource names.
- Successful plan-only run `39140954204` and its versioned manifest.
- AWS absence checks recorded by PR #88.

## Work planned for the PR

- Remove the environment selector from the plan workflow.
- Use one fixed remote state key and production manifest contract.
- Remove environment parameterization from the Terraform root.
- Use the canonical `agentconstruct` resource namespace and Cognito domain prefix.
- Reject previously saved environment-specific plans during apply.
- Update tests and operator documentation.

## Acceptance criteria

- [x] The plan workflow has no environment selector.
- [x] Plan and apply use one fixed state key.
- [x] Terraform has no configurable deployment-environment variable.
- [x] Resource names use one canonical production namespace.
- [x] Old staging or environment-specific saved plans cannot be applied.
- [x] Operator documentation describes one production deployment.
- [x] One required clean-room validation cycle passes.
- [x] Required GitHub checks pass for implementation commit `eb199b4`.

## Acceptance status

Complete. The current deployment contract contains one production control plane, one fixed state
object, one resource namespace, and no environment selection. The old staging saved plan fails the
new manifest-version and production-deployment checks.

## Tests / validation performed

- One clean-room cycle passed from clean through final clean.
- Smoke, simple, complex, degraded, Day-2, policy-failure, readiness-failure, and trace checks
  passed.
- Ruff, OpenAPI snapshot, Compose configuration, and documentation checks passed.
- `make verify`: 226 tests passed with one upstream deprecation warning.
- `make terraform-validate`: all Terraform roots passed.
- Authenticated plan against the fixed production state: 39 additions, no changes, no destroys.
- Post-plan AWS checks confirmed that the state object and control-plane resources remain absent.
- All seven required GitHub checks passed for implementation commit `eb199b4`.

## Evidence files produced

- `docs/test/test89.md`

## Boundaries

- This PR must not run Terraform apply.
- This PR must not create or modify AWS resources.
- Existing prerequisite buckets, keys, roles, state storage, and locks remain unchanged.
- The previously saved staging plan must remain unusable after this contract change.

## Follow-up work

After merge, manually run a new production-only plan from `main`, review it, and apply it only when
the live deployment is explicitly authorized.
