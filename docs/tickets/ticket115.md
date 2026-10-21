# ticket115

PR: #115
Branch: `fix/114-data-api-migration-introspection`

## Problem / goal

Production apply run `39654840212` successfully refreshed the least-privilege OIDC session and
invoked the migration Lambda. The migration then failed closed because SQLAlchemy PostgreSQL
reflection returned an unsupported `CHAR` result through Aurora RDS Data API. Replace that
reflection path with a deterministic, Data API-compatible migration check.

## Current repo state

Terraform applied the reviewed 0-add, 5-update, 0-destroy saved plan. Migration v20 remains
unconfirmed, so the invitation endpoint still fails safely.

## Research / references used

- Production apply run `39654840212` and its `UnsupportedResultException` stack trace.
- Existing `run_migrations()` implementation and migration tests.
- Aurora Data API SQL execution behavior already used by the production adapter.

## Work planned for the PR

- Remove unsupported SQLAlchemy column reflection from the invitation migration.
- Preserve idempotent upgrade behavior on PostgreSQL and SQLite.
- Add a regression test that exercises the Data API-compatible path.
- Run focused validation and one complete clean-room cycle.
- Repeat the reviewed production plan/apply and authenticated live checks after merge.

## Acceptance criteria

- Migration v20 can determine whether invitation lifecycle columns exist without PostgreSQL
  reflection through Data API.
- Repeated migration runs are safe.
- Existing PostgreSQL and local SQLite behavior remains covered.
- Production invitation listing succeeds after the reviewed release.
- No customer infrastructure is deployed or executed.

## Acceptance status

Implementation and local validation are complete. Required GitHub CI and the reviewed production
retry remain pending.

## Tests / validation performed

Focused migration tests passed 7 tests. One complete clean-room cycle passed 255 tests, all local
customer journeys, failure paths, policy tests, contract checks, Terraform validations,
Kubernetes rendering, MCP catalogue validation, and final cleanup. See `docs/test/test115.md`.

## Evidence files produced

- `docs/test/test115.md`

## Boundaries

This PR changes only control-plane migration introspection and its tests. It does not provision or
operate customer infrastructure.

## Follow-up work

Complete the reviewed production plan/apply and authenticated live checks after merge.
