# ticket122

PR: #122
Branch: `chore/event-driven-worker`

## Problem / goal

Make the serverless control-plane worker fully event-driven. It must run when an application
action enqueues a job, rather than receiving a synthetic EventBridge message every minute.

## Current repo state

`serverless-control-plane` already uses an SQS to Lambda event-source mapping. A separate
EventBridge rule sends an empty tick message to the queue every minute and an SQS policy exists
only for that rule. The tick keeps the worker and Aurora Data API active even when no customer
job exists, preventing Aurora Serverless v2 from reaching its configured idle auto-pause.

## Research / references used

- `infrastructure/terraform/serverless-control-plane/main.tf`
- `infrastructure/terraform/serverless-control-plane/README.md`
- `docs/TERRAFORM_GITHUB_OPERATIONS.md`

## Work planned for the PR

- Remove the EventBridge worker tick rule and target.
- Remove the EventBridge-only SQS resource policy.
- Retain the SQS to Lambda event-source mapping, dead-letter queue, alarms, and application job
  enqueue contract.
- Document that delayed or scheduled work requires an explicit attributable job, not a permanent
  polling heartbeat.

## Acceptance criteria

- Terraform contains no permanent worker tick rule or target. Met.
- The SQS to Lambda event-source mapping remains enabled. Met.
- Terraform formatting and validation pass. Met.
- The post-merge reviewed Terraform plan shows only removal of the heartbeat resources. Pending.
- No Terraform apply is performed from this PR. Met.

## Acceptance status

Implementation and local static validation are complete. The PR remains draft until required CI
is complete. The repository deliberately permits manual Terraform plans only from `main`, so the
reviewed plan follows the merge. No apply has been run.

## Tests / validation performed

- `terraform fmt -check -recursive infrastructure/terraform` passed.
- `terraform -chdir=infrastructure/terraform/serverless-control-plane init -backend=false -input=false` completed using the locked AWS provider.
- `terraform -chdir=infrastructure/terraform/serverless-control-plane validate` passed.
- `git diff --check` passed.

## Evidence files produced

No customer workload run occurred. This ticket and the Terraform diff are the implementation
evidence; the manually reviewed Terraform plan will be recorded after merge.

## Boundaries

This PR changes DavDeploy control-plane scheduling only. It does not deploy customer workloads,
change Aurora capacity, or run a Terraform apply.

## Follow-up work

After merge, run the existing manual Terraform plan and apply workflows. Verify the queue is
empty, then observe Aurora become idle and auto-pause without customer work.
