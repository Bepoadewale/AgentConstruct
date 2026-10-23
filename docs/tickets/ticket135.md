# Ticket 135: Retry migration after Aurora wake-up

## Goal

Make the guarded Terraform apply workflow tolerate Aurora Serverless resuming from
auto-pause before it verifies database migrations.

## Current state

Terraform apply run `40011947189` applied the saved infrastructure plan, then the
migration Lambda returned Aurora's `DatabaseResumingException`. A manually retried,
idempotent migration invocation succeeded once Aurora was available.

## Work

- Retry only the post-apply migration verification up to six times.
- Wait ten seconds between unsuccessful attempts.
- Preserve a hard failure with the final migration response after the bounded retry.

## Acceptance criteria

- [x] Normal Aurora resume does not falsely mark a completed Terraform apply as failed.
- [x] The retry is bounded to at most one minute.
- [x] A real migration failure still fails the workflow and prints the final response.
- [ ] Focused validation and required CI pass.

## Validation

- Pending: workflow syntax and repository CI.

## Boundaries and follow-up

- This does not retry Terraform apply or change any customer workload action.
- The workflow will still fail after six unsuccessful migration attempts.
