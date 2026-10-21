# Test 107: Public GitHub repository planning

## Commands executed

- Targeted Ruff and pytest checks.
- Direct bounded read-only analysis of `Bepoadewale/ai-platform-control-plane`.
- One complete `make clean-room` validation cycle.
- Controlled production customer journey after reviewed deployment.

## Result

Targeted checks passed 18 tests. Direct public analysis confirmed the real repository, `main`
default branch, `docker-compose.yml`, `pyproject.toml`, and `.github/workflows` manifests, Python and
FastAPI hints, and 0.82 evidence confidence. One complete clean-room cycle passed on 2026-10-21,
including smoke, API contract, all demo variants, customer-plan E2E, seeded data, persistence,
trace, Python verification, OPA, every Terraform root, and final cleanup. Production results require
the reviewed code to be merged and deployed and will be recorded separately.

## Execution boundary

The direct and live repository checks use unauthenticated, read-only GitHub REST requests. The live
customer journey creates only control-plane account, workspace, repository-evidence, intent, plan,
and draft-review records. It never calls customer infrastructure execution or deployment APIs.

## Known limitations

Unauthenticated GitHub API rate limits apply. Private repositories require the existing GitHub App
adapter and installation authorization.
