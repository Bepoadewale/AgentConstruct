# test83 — Frontend separation backend evidence

Date: 2026-10-16.

Execution type: local and static migration validation. No AWS or Cloudflare
deployment, Terraform apply or customer workload execution occurred.

Customer repository: `Bepoadewale/AgentConstruct`; separated browser repository:
`Bepoadewale/agentconstruct-frontend`.

Commit: backend PR #83 branch plus frontend commit `8e1264d`.

AWS account: not accessed.

AWS region: not accessed.

## Resources created

No AWS, Cloudflare or customer resource was created. Local verification created
only disposable Docker images, containers and a project-scoped PostgreSQL
volume used by the clean-room tests.

## Commands executed

```bash
make install
make lint
make test
make openapi-check
python3 scripts/check_doc_conventions.py
terraform fmt -check -recursive infrastructure/terraform
docker build -f apps/api/Dockerfile .

# In the independent frontend repository
npm run verify
```

The completed clean-room section will run the local API, worker, PostgreSQL,
OPA, Prometheus, Grafana, Tempo and fixture executor twice from clean state. It
will exercise API/CORS, customer-plan, simple, complex, degraded, Day-2,
failure, readiness, trace, OPA, Terraform, Kubernetes and MCP checks.

## Observed result

- Ruff passed.
- Pytest passed 204 tests with one upstream Starlette/httpx deprecation warning.
- The generated OpenAPI document exactly matched `contracts/openapi-v1.json`.
- Documentation, diff and Terraform formatting checks passed.
- The backend-only Docker image built without `apps/web`.
- The synchronized frontend passed formatting, lint, strict TypeScript, 16
  deterministic tests, 34-operation API compatibility, static production
  build, Cloudflare-limit inspection, nested-route refresh and npm audit with
  zero vulnerabilities.
- Clean-room cycle results are pending.

## Teardown

No cloud teardown is required. The final clean-room command will be `make
clean-local`, which removes only this project's containers, volume, virtual
environment and `.local` runtime state.

## Final boundary

Current evidence proves local/static separation and independent builds. It does
not prove Cloudflare deployment, live cross-origin login, production OIDC,
hosted durable PostgreSQL, or any AWS customer workload. Those require their
own explicit configuration and live-environment evidence.

