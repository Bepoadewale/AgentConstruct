# ticket83 — Separate the static frontend from the control plane

- PR: #83
- Branch: `feat/frontend-separation`
- Status: in progress

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

- [ ] Versioned OpenAPI snapshot and compatibility check are present.
- [ ] Exact-origin CORS and negative tests pass.
- [ ] Legacy UI and obsolete browser checks are removed.
- [ ] Backend documentation reflects repository ownership.
- [ ] Independent backend and frontend validation passes.
- [ ] Two clean-room cycles and required PR CI pass.

## Tests / validation performed

- In progress: Ruff, pytest, documentation conventions and dependency audit.
- In progress: OpenAPI snapshot comparison and API/CORS boundary tests.
- Planned: Docker image build, Compose smoke and customer-plan workflows.
- Planned: OPA, Terraform validation, Kubernetes render and MCP catalogue checks.
- Planned: two clean-room local cycles with final cleanup.

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
