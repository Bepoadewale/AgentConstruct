# ticket127: Deliver durable worker wake-ups through SQS

PR: #127
Branch: fix/event-driven-worker-wakeup

## Problem / goal

After the periodic worker heartbeat was removed, durable discovery and customer-execution records were committed but did not emit an SQS message. They could remain queued until an unrelated event arrived.

## Current repo state

The worker Lambda already consumes the SQS queue and CodeBuild completion events already reach that queue. The API/worker IAM role did not have `sqs:SendMessage`, and the API runtime had no queue URL.

## Research / references used

- Existing `lambda_worker.py` claim-and-process boundary.
- Existing serverless worker queue, event-source mapping, and least-privilege IAM policy.
- Existing durable discovery and cloud-execution state machines.

## Work planned for the PR

- Supply the worker queue URL to hosted Lambda runtimes.
- Grant only `sqs:SendMessage` in addition to existing worker queue permissions.
- Emit a minimal, post-commit, non-sensitive wake-up for discovery and approved cloud execution jobs.
- Cover local and hosted failure behavior.

## Acceptance criteria

- [x] A committed verification or execution job wakes the SQS worker without a permanent poller.
- [x] The message contains no tenant data, credentials, plan content, or customer commands.
- [x] Hosted mode fails closed if the wake-up queue is absent or unavailable.
- [x] The worker remains the only component that claims and runs durable work.

## Acceptance status

Implemented and focused validation passed. Merge and a reviewed manual Terraform plan/apply remain required before the hosted worker receives wake-up messages.

## Tests / validation performed

See `docs/test/test127.md`.

## Evidence files produced

- `docs/tickets/ticket127.md`
- `docs/test/test127.md`

## Boundaries

This PR wakes existing bounded work only. It does not alter customer Terraform, broaden IAM beyond one queue action, or create customer cloud resources.

## Follow-up work

- Merge, deploy, and verify an actual customer discovery job is consumed through SQS.
