# ADR-010: Permit auditable workspace-administrator self-approval

## Context

The customer product workflow requires an administrator to be able to create, submit and approve their own infrastructure plan. Earlier execution-plan controls required a distinct operator.

## Decision

Customer-facing infrastructure-plan revisions use a separate approval model. A workspace administrator may approve their own submitted revision. The decision records the creator, approver, exact digest, revision, timestamp, authorizing policy and `is_self_approval=true`.

## Alternatives

Keep an unconditional self-approval prohibition, or allow unchecked self-approval for every role.

## Consequences

Small teams can complete the planning workflow without inventing a second approver. Developers still cannot approve or reject. This exception does not apply to the existing bounded execution-plan workflow and does not grant cloud permissions or trigger deployment.

## Security and operations

The API checks tenant scope, administrator role, submitted state and exact digest. PostgreSQL locks the revision during a decision and permits one decision record per revision.
