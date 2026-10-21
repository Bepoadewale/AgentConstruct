# test115

Date: 2026-10-21
Execution type: Local migration validation followed by a pending real control-plane migration retry
Customer repository: `https://github.com/Bepoadewale/ai-platform-control-plane`
Commit: `b17f3e1`
AWS account: Existing DavDeploy control-plane account
AWS region: `us-east-1`

## Resources created

The clean-room cycle created temporary Compose containers, a PostgreSQL volume, and Terraform
validation directories. Final cleanup removed them. No customer resources were created.

## Commands executed

- `.venv/bin/ruff check apps/api/src/davdeploy/db.py tests/test_invitation_email.py`
- `.venv/bin/python -m pytest tests/test_invitation_email.py tests/test_db_config.py -q`
- One complete cycle: clean, bootstrap, smoke, API contract, customer-plan E2E, API restart,
  persistence check, simple/complex/degraded/Day-2 demos, policy failure, readiness failure,
  traces, verify, OPA, Terraform validation, Kubernetes rendering, MCP catalogue, clean.
- GitHub CI run `39688775591`.

## Observed result

Production apply run `39654840212` applied the exact saved plan and successfully invoked the
migration Lambda using refreshed credentials. The Lambda failed closed with
`UnsupportedResultException` because SQLAlchemy PostgreSQL reflection requested an unsupported
`CHAR` result through Aurora Data API.

The replacement uses PostgreSQL's idempotent `ADD COLUMN IF NOT EXISTS`, so it does not read the
system catalogue through Data API. SQLite retains a reflected-column fallback. Focused validation
passed 7 tests, including repeat migration idempotency. The clean-room cycle passed 255 tests,
Ruff, OpenAPI parity, exact-origin CORS, customer-plan persistence after API restart, all planning
and failure journeys, Tempo traces, OPA 3/3, every Terraform root, Kubernetes rendering, and the
MCP authority boundary. Final cleanup completed.
All seven required jobs in GitHub CI run `39688775591` passed, including independent local E2E,
cloud-contract, policy, supply-chain, Python, documentation, and secret-scanning gates.

## Teardown

The clean-room cycle removed all temporary containers, networks, volumes, `.venv`, and `.local`
state. The durable control-plane migration is not torn down.

## Final boundary

The live customer journey stops after a review-only plan and never submits, approves, executes,
deploys, changes, or destroys customer infrastructure.
