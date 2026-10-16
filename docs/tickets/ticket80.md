# ticket80 — Isolate the same-account platform and customer pilot

- PR: #80
- Branch: `feat/same-account-pilot-boundaries`
- Status: in progress

## Problem / goal

Prepare one AWS account to host AgentConstruct and a controlled customer-sandbox
pilot without creating AWS Organizations member accounts. The platform and
customer sides need explicit network, IAM, Terraform state, tagging, budget,
and teardown boundaries so operators cannot confuse the sandbox with the
control plane.

## Current repo state

- The account has one default VPC and no active App Runner or RDS resource.
- The hosted runtime contract can create its own VPC and private RDS database.
- The customer workload pilot creates App Runner resources but no customer VPC.
- Terraform state keys and resource names are fixed for earlier pilot scripts.
- The existing AWS Organization contains only the management account; this work
  must not create or invite any member account.

## Research / references used

- AWS Well-Architected account-separation guidance.
- AWS IAM least-privilege and temporary-credential guidance.
- Existing AgentConstruct runtime, customer connection, workload pilot, budget,
  state-lock, and validation contracts.

AWS describes an account as the stronger isolation boundary. This pilot is an
explicit same-account compromise and must not be presented as cross-account
customer isolation.

## Work planned for the PR

- Add explicit `platform` and `customer-sandbox` placement metadata and tags.
- Add a low-cost customer-sandbox VPC contract with private subnets and an App
  Runner connector, without a NAT gateway.
- Separate Terraform state keys, names, IAM roles, security groups and resource
  discovery by pilot scope.
- Add exact account/region/scope guards and teardown/absence checks.
- Add static tests, documentation and operator commands.

## Acceptance criteria

- No AWS Organizations account action exists in the implementation.
- Platform and customer-sandbox CIDRs, names, state keys and tags cannot collide.
- The customer sandbox uses a dedicated VPC and least-privilege runtime role.
- Same-account limitations are visible in operator and customer evidence.
- Terraform validates offline and automated tests require no AWS credentials.
- Destructive operations require exact confirmation and verify resource absence.

## Acceptance status

- [ ] No member-account operation is introduced.
- [ ] Platform and customer scopes are collision-resistant.
- [ ] Customer sandbox VPC and role boundaries are implemented.
- [ ] Shared-account limitations are documented.
- [ ] Offline validation passes.
- [ ] Teardown and absence checks are bounded.

## Tests / validation performed

Pending implementation.

## Evidence files produced

No real customer workload will be created in this contract-only PR. Live AWS
execution will be recorded in the later PR that performs the customer pilot.

## Boundaries

- Account `654654474502` remains a single AWS account.
- Separate VPCs and IAM roles reduce accidental overlap but do not create an AWS
  account security, quota, billing, or blast-radius boundary.
- This PR does not create, modify or delete AWS resources.
- No long-lived credential, secret or customer data is committed.

## Follow-up work

- Apply the platform runtime with durable persistence and Nova after review.
- Apply and exercise the customer sandbox in a separately evidenced PR.
- Move to true cross-account customer isolation before onboarding unrelated
  external customer AWS accounts at scale.
