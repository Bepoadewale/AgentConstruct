# ticket47 — Production-grade hosted control-plane persistence

PR: [#47 — feat: add hosted RDS persistence contract](https://github.com/Bepoadewale/AgentConstruct/pull/47)

Branch: `feature/hosted-rds-persistence`

Status: ready for review.

## Problem / goal

The AWS-hosted AgentConstruct runtime proved App Runner viability and read-only customer AWS discovery, but it still uses ephemeral SQLite in `/tmp`. Production hosted mode needs durable PostgreSQL, managed secrets, backups, migrations and clear no-SQLite guardrails.

## Current repo state

- Local development uses PostgreSQL through Docker Compose and SQLite fallback for simple local execution.
- Hosted App Runner Terraform sets `AGENTCONSTRUCT_DATABASE_URL=sqlite+pysqlite:////tmp/agentconstruct.db`.
- A generic RDS module exists for pilot infrastructure, but the hosted App Runner runtime does not yet create or consume a control-plane RDS database.
- Runtime signing key and per-connection ExternalIds use Secrets Manager.

## Research / references used

Local repo references:

- `apps/api/src/agentconstruct/db.py`
- `infrastructure/terraform/app-runner-runtime/main.tf`
- `infrastructure/terraform/modules/rds/main.tf`
- `docs/product/CURRENT_STATE_AUDIT.md`
- `docs/IMPLEMENTATION_STATUS.md`
- `PROJECT_STATUS.md`

## Work planned for the PR

- Add a hosted-mode database guard so production/App Runner cannot silently use ephemeral SQLite.
- Extend the App Runner runtime Terraform with optional durable RDS PostgreSQL.
- Add networking required for private RDS access from App Runner via VPC connector.
- Store database credentials in AWS-managed RDS Secrets Manager and pass only secret references to App Runner.
- Add backup/deletion-protection settings and outputs.
- Document hosted persistence status and boundaries.
- Add tests/static checks proving hosted mode blocks SQLite and Terraform validates.

## Acceptance criteria

- [x] Hosted mode rejects SQLite database URLs.
- [x] Local mode can still use SQLite/PostgreSQL.
- [x] App Runner runtime contract can provision durable private RDS PostgreSQL when enabled.
- [x] App Runner runtime receives database secret references, not plaintext passwords.
- [x] Backups, encryption and deletion protection are represented.
- [x] Terraform validates offline.
- [x] Tests pass.

## Acceptance status

Met for implementation and static validation. The RDS-backed hosted runtime contract has not been applied in AWS in this PR.

## Tests / validation performed

```bash
make lint
make test
make terraform-validate
python3 scripts/check_doc_conventions.py
GITHUB_EVENT_NAME=pull_request GITHUB_PR_NUMBER=47 python3 scripts/check_doc_conventions.py
git diff --check
```

Results:

- `make lint` passed.
- `make test` passed: 115 tests.
- `make terraform-validate` passed for every Terraform root, including `app-runner-runtime`.
- Documentation convention checks passed, including PR #47 mode.
- `git diff --check` passed.

## Evidence files produced

No customer workload cloud test is planned for this PR. If RDS/App Runner is applied in AWS for validation, record evidence in `docs/test/test47.md`.

## Boundaries

- No customer workload deployment.
- No Terraform apply unless explicitly run and recorded.
- No plaintext database password in Git, UI, audit or plan JSON.
- Local fixture sign-in remains separate from production identity work.

## Follow-up work

- Apply hosted RDS in AWS and record evidence if requested.
- Move hosted identity/policy from fixtures to production OIDC/OPA.
- Add migration observability and restore drill evidence.
