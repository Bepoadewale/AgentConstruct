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

- [ ] The plan workflow has no environment selector.
- [ ] Plan and apply use one fixed state key.
- [ ] Terraform has no configurable deployment-environment variable.
- [ ] Resource names use one canonical production namespace.
- [ ] Old staging or environment-specific saved plans cannot be applied.
- [ ] Operator documentation describes one production deployment.
- [ ] One required clean-room validation cycle passes.
- [ ] Required GitHub checks pass.

## Acceptance status

Implementation and validation are pending.

## Tests / validation performed

Pending.

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
