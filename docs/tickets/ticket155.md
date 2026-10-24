# ticket155 — Permit bounded reconciliation tags on owned customer resources

PR: Pending
Branch: `fix/customer-execution-reconciliation-tag-permissions`

## Problem / goal

The guarded customer foundation apply failed while reconciling ownership tags on already-created
customer resources. Its role allowed tag requests only when every ownership tag was supplied in the
request; Terraform updates existing tags incrementally.

## Work planned for the PR

- Correct the CloudWatch Logs tagging action to `logs:TagResource`.
- Permit tag reconciliation only when the target already carries this connection's two ownership
  tags.
- Retain the request-tag guard for newly created resources and all existing delete guards.

## Acceptance criteria

- [ ] The CloudFormation template validates.
- [ ] Existing owned VPC, ECR, App Runner, and log resources can receive bounded tag updates.
- [ ] Resources without both davdeploy ownership tags remain outside the reconciliation grant.
- [ ] Tests and CI pass.

## Boundaries

This changes IAM permissions only for resources already tagged `ManagedBy=davdeploy` and with the
current connection ID. It does not delete resources or enable a destroy operation.

## Evidence files produced

- `docs/test/test155.md`
