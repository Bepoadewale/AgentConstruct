# Ticket 122: Remove the permanent worker heartbeat

## Goal

Make the serverless control-plane worker fully event-driven. The worker must run when an
application action enqueues a job, rather than receiving a synthetic EventBridge message every
minute.

## Current state

`serverless-control-plane` already uses an SQS to Lambda event-source mapping. A separate
EventBridge rule sends an empty tick message to the queue every minute and an SQS policy exists
only for that rule. The tick keeps the worker and Aurora Data API active even when no customer
job exists, which prevents Aurora Serverless v2 from reaching its configured idle auto-pause.

## References

- `infrastructure/terraform/serverless-control-plane/main.tf`
- `infrastructure/terraform/serverless-control-plane/README.md`
- `docs/TERRAFORM_GITHUB_OPERATIONS.md`

## Work

- Remove the EventBridge worker tick rule and target.
- Remove the EventBridge-only SQS resource policy.
- Retain the SQS to Lambda event-source mapping, dead-letter queue, alarms, and application job
  enqueue contract.
- Document that delayed or scheduled work must use an explicit, attributable job rather than a
  permanent polling heartbeat.

## Acceptance criteria

- [x] Terraform contains no permanent worker tick rule or target.
- [x] The SQS to Lambda event-source mapping remains enabled.
- [x] Terraform formatting and validation pass.
- [ ] A reviewed Terraform plan shows only removal of the heartbeat resources.
- [ ] No Terraform apply is performed from this PR.

## Boundaries

This PR changes DavDeploy control-plane scheduling only. It does not deploy customer workloads,
change Aurora capacity, or run a Terraform apply.

## Validation

- `terraform fmt -check -recursive infrastructure/terraform` passed.
- `terraform -chdir=infrastructure/terraform/serverless-control-plane init -backend=false -input=false` completed using the locked AWS provider.
- `terraform -chdir=infrastructure/terraform/serverless-control-plane validate` passed.
- `git diff --check` passed.

## Follow-up

After merge, run the existing manual Terraform plan and apply workflows. Verify the queue is
empty, then observe Aurora become idle and auto-pause without customer work.
