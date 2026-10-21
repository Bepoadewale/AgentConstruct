# test107

Date: 2026-10-21
Execution type: Local clean-room and direct public GitHub read-only validation
Customer repository: `https://github.com/Bepoadewale/ai-platform-control-plane`
Commit: `4dc113a`
AWS account: Not used
AWS region: Not used

## Resources created

- Temporary local containers, PostgreSQL volume, test records, and Terraform validation directories.
- Read-only public GitHub API requests for metadata and a fixed manifest allowlist.
- Zero customer cloud resources.

## Commands executed

- Targeted Ruff and pytest checks.
- Direct bounded read-only analysis of `Bepoadewale/ai-platform-control-plane`.
- One complete local clean-room validation cycle.

## Observed result

Targeted checks passed 18 tests. Direct public analysis confirmed the real repository, `main`
default branch, `docker-compose.yml`, `pyproject.toml`, and `.github/workflows` manifests, Python and
FastAPI hints, and 0.82 evidence confidence.

The clean-room cycle passed smoke, API contract, all demo variants, customer-plan E2E, seeded data,
persistence, trace, Python verification, OPA, and every Terraform root. The fixture regression test
also confirms generated `example/*` demo repositories stay on the deterministic adapter.

## Teardown

The clean-room cycle ended with `make clean-local`, removing its containers, network, volume,
virtual environment, and generated local state. Public GitHub reads create no remote resources.

## Final boundary

The validation reads public repository evidence and exercises only local control-plane fixtures. It
does not call customer approval, execution, deployment, or teardown APIs. Private repositories still
require an authorized GitHub App installation.
