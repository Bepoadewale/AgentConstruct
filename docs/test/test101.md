# test101

Date: 2026-10-20
Execution type: Controlled live production customer journey
Customer repository: No customer repository write; DavDeploy production control plane only
Commit: `test/live-customer-journey-evidence` worktree before final evidence commit
AWS account: 654654474502
AWS region: us-east-1

## Scope

Complete the authenticated developer and administrator workflow through Nova planning, immutable
review, independent approval, bounded fixture execution, observation, audit, usage, and governed
fixture teardown.

## Preliminary live results

The authenticated developer created a tenant-scoped project, Nova-derived intent, architecture
plan, immutable customer review, and approval submission. The production API rejected developer
access to the administrator queue, developer approval, and an administrator approval with a stale
digest. A different administrator approved the exact digest. The approved dry run created only two
fixture environment records and SQS jobs.

The environments remained `QUEUED`. SQS reported four in-flight messages and the Lambda event
source mapping was enabled. CloudWatch showed the worker attempting to call the Docker-only
hostname `fixture-executor` and failing with `httpx.ConnectError`. No customer cloud workload was
created.

## Correction and local validation

PR #101 now selects a stateless embedded fixture adapter for hosted Lambda while retaining the
HTTP fixture adapter for local Compose. The embedded adapter has no network, shell, Terraform, or
cloud authority. Teardown also marks all durable observed outputs and resources as destroyed.

One clean-room cycle passed on 2026-10-20:

- smoke and versioned API contract;
- customer-plan E2E;
- simple, complex, degraded, Day-2, canonical, policy-failure, and readiness-failure demos;
- Tempo trace check;
- Ruff;
- 236 tests with one upstream Starlette deprecation warning;
- OpenAPI drift and Compose configuration;
- OPA 3/3;
- all Terraform roots validated;
- final project-scoped cleanup.

## Resources created

- Durable control-plane records for one project, intent, plan, revision, approval, and two fixture
  environments.
- SQS messages for bounded fixture execution.
- No customer AWS workload resources.

## Commands executed

Production API requests used short-lived Cognito ID tokens for separate developer and administrator
identities. AWS diagnostics used read-only SQS event-source and CloudWatch Logs commands. The
repository validation command followed the single clean-room sequence required by `AGENTS.md`.

## Observed result

Pending deployment of the reviewed correction and completion of the queued fixture execution,
governed destroy, audit check, usage check, and temporary-identity removal.

## Teardown

Local Compose state and volumes were removed by the final `make clean-local`. Production fixture
teardown remains pending until the correction is deployed.

## Final boundary

This run will not create or delete customer AWS workload resources.
