# Ticket 131: Wake the worker after cloud-execution confirmation

## Goal

Close the event-driven handoff gap between final administrator confirmation and a durable `QUEUED` cloud-execution run.

## Current state

The worker is intentionally not a polling heartbeat. A run was woken at creation while it was still awaiting confirmation; after confirmation it became queued without a new wake-up. No customer apply was started.

## Work

- Send a minimal SQS wake-up after the post-confirmation durable commit.
- Add a regression test asserting the queue transition emits exactly one cloud-execution wake-up.

## Acceptance criteria

- [x] A ready run remains unable to execute before explicit confirmation.
- [x] Confirming the exact apply phrase commits `QUEUED` and emits a non-sensitive wake-up.
- [ ] Focused tests and required CI pass.
- [ ] The real queued pilot run is claimed only after the correction is deployed.

## Boundaries

The message carries only the event kind and durable run ID. Terraform commands, tenant data, plan material, and credentials remain in the database and trusted runner boundary.

## Validation

`pytest -q tests/test_cloud_execution.py` and repository linting will be recorded before merge. The live customer-pilot proof remains in PR #130.
