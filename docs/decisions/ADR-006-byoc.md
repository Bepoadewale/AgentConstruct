# ADR-006: Prefer bring-your-own-cloud

## Context

Customers want their workload data, cloud account and bill under their own control.

## Decision

davdeploy will orchestrate through a scoped customer-cloud role while the customer owns resources and workload data.

## Alternatives

Host all customer workloads in an davdeploy cloud account.

## Consequences

Onboarding needs clear cloud connection controls, but customer ownership is clearer.

## Security and operations

Use STS/OIDC short-lived access, least privilege and auditable scope.
