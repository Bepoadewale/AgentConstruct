# Frontend separation migration audit

Date: 2026-10-16. Source baseline: `7dc5c33`. Backend PR: #83. Frontend PR:
[`Bepoadewale/agentconstruct-frontend#1`](https://github.com/Bepoadewale/agentconstruct-frontend/pull/1).

## Inspected system

The source was inspected before extraction: repository manifests, FastAPI
routes, the plain browser client, domain/service/policy code, PostgreSQL models
and migrations, identity and tenant checks, GitHub and AWS adapters, planning,
cost, approval and execution workflows, Terraform/Kubernetes contracts,
observability, tests, fixtures, CI, documentation and repository instructions.

The source is a Python 3.12/FastAPI modular monolith. Its legacy client was
three server-mounted files: `apps/web/index.html`, `app.js` and `styles.css`.
It called `/api/v1` directly. FastAPI, PostgreSQL, OPA, background workers,
provider adapters and infrastructure code are the authoritative control plane.

## Ownership inventory

| Classification | Source material | Migration result |
| --- | --- | --- |
| Frontend-only | `apps/web`, browser state, layouts, pages, forms, styles and accessibility behavior | Reimplemented as typed React/Vite modules and tests in the frontend repository; removed here after independent verification |
| Frontend-specific rules | UI design system and browser portions of ADR-009/identity guidance | Adapted into frontend `AGENTS.md` and architecture/security documentation |
| Backend-only | `apps/api`, database, workers, OPA, provider adapters, CLI/MCP, Terraform/Kubernetes, observability | Retained here |
| Shared contract | FastAPI `/api/v1` request/response schemas | Published as `contracts/openapi-v1.json`; the frontend carries a reproducible snapshot and checks required operations |
| Backend-authoritative | Tenant membership, roles, policy, approvals, pricing/planning decisions, secrets, execution and audit integrity | Retained and tested here; no browser override exists |
| Cross-cutting tooling | CI, local Compose and contract checks | Split into frontend static CI and backend API/Compose CI |
| Obsolete | FastAPI static mount and legacy browser grep scripts | Removed after the extracted frontend passed two clean cycles and a separate-clone build |
| Historical | Prior tickets, evidence and ADR-009 | Retained as historical evidence; ADR-009 is superseded by ADR-012 |

No backend source, credentials, `.env` file, Terraform state or original Git
history was copied into the frontend repository. The frontend can be cloned and
built without this repository.

## Coupling and security findings

- Same-origin hosting had hidden the need for explicit CORS. The separated API
  now accepts only configured exact origins, rejects wildcards/paths/public
  HTTP, and does not enable browser credential cookies.
- Browser authorization remains advisory. Every tenant, role, approval and
  execution decision is repeated by the API and policy boundary.
- Bearer credentials are kept in memory by the client; OAuth client secrets,
  AWS credentials, GitHub App secrets and infrastructure authority stay here.
- Mutating frontend requests are not retried automatically. The API retains
  idempotency and digest checks where implemented.
- Cloudflare hosts static assets only. It does not host the backend or provide
  application compute, storage, identity, AI or security enforcement.

## Removal gate

Before the legacy client was removed, the extracted repository passed lint,
type checking, 16 deterministic tests, accessibility checks, contract checks,
production build/static inspection, nested-route refresh, dependency audit,
two clean validation cycles and a fresh private-repository clone build.

