# ticket83 — Separate the static frontend from the control plane

- PR: #83
- Branch: `feat/frontend-separation`
- Status: complete

## Problem / goal

Move the verified browser application to the private
`Bepoadewale/agentconstruct-frontend` repository and leave this repository as
the authoritative AWS-hosted control plane. The browser must communicate over
the versioned HTTPS API without weakening tenant, identity, policy, approval or
execution enforcement.

## Current repo state

- FastAPI serves a legacy HTML/CSS/JavaScript application from `apps/web`.
- The API has no browser CORS middleware because the UI shares its origin.
- Browser contract scripts inspect the legacy static files.
- The independently verified React/Vite extraction is in frontend PR #1.

## Research / references used

- Existing FastAPI routes, Pydantic schemas and generated OpenAPI document.
- Existing hosted identity and browser-boundary documentation.
- Cloudflare Pages static-site and SPA behavior documented in the frontend
  repository handoff; no Cloudflare runtime product is used here.
- Starlette/FastAPI exact-origin CORS behavior and the repository's existing
  hosted-runtime activation guards.

## Work planned for the PR

- Publish and regression-check the versioned OpenAPI contract.
- Add strict, exact-origin bearer-token CORS configuration.
- remove the verified legacy UI and its image/runtime packaging.
- Replace legacy browser checks with API-boundary checks.
- Update backend architecture, identity, deployment and migration guidance.
- Verify the backend independently, including two clean-room local cycles.

## Acceptance criteria

- This repository builds and tests without frontend source files.
- The API serves JSON rather than an embedded web application at `/`.
- Credentialed wildcard CORS is impossible; configured origins are exact.
- The frontend builds independently from its committed API contract.
- Security, tenancy, planning, policy, approvals and execution stay server-side.
- No AWS or Cloudflare resource is created by the migration.
- Two clean-room backend cycles and required CI checks pass.

## Acceptance status

- [x] Versioned OpenAPI snapshot and compatibility check are present.
- [x] Exact-origin CORS and negative tests pass.
- [x] Legacy UI and obsolete browser checks are removed.
- [x] Backend documentation reflects repository ownership.
- [x] Independent backend and frontend validation passes.
- [x] Two clean-room cycles pass; required PR CI is pending remote completion.

## Tests / validation performed

- Ruff and 204 pytest tests passed; the only warning is an upstream
  Starlette/httpx deprecation.
- Documentation conventions, diff checks, OpenAPI snapshot comparison and
  API/CORS positive/negative boundary checks passed.
- The backend-only Docker image built; Compose smoke, load and customer-plan
  workflows passed.
- OPA passed 3/3; every Terraform root validated; Kubernetes rendered; MCP
  catalogue discovery passed.
- Two clean-room local cycles passed and each ended with full project cleanup.
- The synchronized frontend passed its complete verification gate again.

## Evidence files produced

- `docs/test/test83.md` will record the local backend migration validation. No
  AWS or customer cloud resource is created.

## Boundaries

- No frontend role or tenant value is treated as authorization.
- No OAuth secret, AWS credential, GitHub App secret or execution authority is
  moved into the browser.
- No Cloudflare Function, Worker, storage or paid service is introduced.
- No AWS apply or workload deployment is performed.

## Follow-up work

- After Cloudflare assigns the production `pages.dev` hostname, configure that
  exact origin in the hosted backend and the same callback origin in the IdP.
- Validate the live browser-to-AWS API path after production identity and the
  durable hosted backend are activated.
