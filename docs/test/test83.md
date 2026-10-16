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

Two complete clean-room cycles ran the local API, worker, PostgreSQL, OPA,
Prometheus, Grafana, Tempo and fixture executor from clean state. Each cycle
executed:

```bash
make clean-local
make bootstrap-local
make smoke
make api-contract
make local-load-smoke
make customer-plan-e2e
make seed-demo-data
make demo-simple
make demo-complex
make demo-degraded
make demo-day2
make demo-failure
make demo-readiness-failure
make trace-check
make verify
make opa-test
make terraform-validate
make kubernetes-render
printf '<MCP tools/list request>' | AGENTCONSTRUCT_TOKEN=fixture-token \
  .venv/bin/agentconstruct-mcp
make clean-local
```

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
- Two clean-room cycles passed. Their 50-request, concurrency-5 load smokes
  recorded local p95 values of 22.2 ms and 29.0 ms; these are correctness
  smokes, not production capacity claims.
- Both cycles passed the developer/administrator flow, self-approval audit,
  governed dry run/destroy, simple App Runner, complex EKS, degraded ECS,
  Day-2 change, policy denial and readiness-failure cases.
- Both cycles passed Tempo trace search, 204 tests, OPA 3/3, all Terraform
  validations, Kubernetes rendering and MCP tool discovery.
- An earlier cycle stopped at the first API-contract check because the new
  script used a singular decision-path spelling. The script was corrected to
  the actual `/decisions` route and the full cycle was restarted from clean
  state; the incomplete run is not counted.

## Teardown

No cloud teardown was required. Both clean-room cycles ended with `make
clean-local`, which removed this project's containers, PostgreSQL volume,
network, virtual environment and `.local` runtime state. No project container
remains running.

## Final boundary

This evidence proves local/static separation and independent builds. It does
not prove Cloudflare deployment, live cross-origin login, production OIDC,
hosted durable PostgreSQL, or any AWS customer workload. Those require their
own explicit configuration and live-environment evidence.
