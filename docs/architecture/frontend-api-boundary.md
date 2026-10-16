# Frontend/API boundary

The browser application is maintained in the private
[`Bepoadewale/agentconstruct-frontend`](https://github.com/Bepoadewale/agentconstruct-frontend)
repository. This repository owns the AWS-hosted control-plane API, persistence,
workers, policy, planning, provider integrations, audit and infrastructure.

## Contract

`contracts/openapi-v1.json` is the committed v1 API snapshot. `make
openapi-check` compares it with `FastAPI.openapi()` and fails on drift. An
intentional API change must update the backend implementation, tests and
snapshot, then update the frontend snapshot and contract expectations in its
own pull request.

The frontend never needs this source checkout to build. It commits the
portable contract artifact and typed client-owned models required by its
release.

## Browser configuration

Set `AGENTCONSTRUCT_ALLOWED_FRONTEND_ORIGINS` to a comma-separated list of
explicit origins. Hosted origins must use HTTPS and must not include paths,
queries, credentials or wildcards. Localhost HTTP is accepted for development.

The browser uses `Authorization: Bearer` and the API deliberately leaves
credential-cookie CORS disabled. The allowed methods are GET, POST, PUT, PATCH,
DELETE and OPTIONS; allowed request headers are Authorization, Content-Type and
Idempotency-Key. Preview deployments do not receive API access unless their
exact origin is deliberately configured.

## Authority

Route guards, hidden controls and client form validation improve usability but
confer no authority. The API independently validates the authenticated actor,
server-side membership, tenant, operation, plan digest, policy result, approval
and scope. The browser never receives AWS credentials, GitHub App secrets,
Terraform state, model-provider secrets or execution-runner authority.

## Deployment order

1. Deploy or identify the backend HTTPS API and production OIDC provider.
2. Configure the frontend build with the public API URL and browser-safe OIDC
   identifiers.
3. Let Cloudflare Pages assign the production `pages.dev` hostname.
4. Add that exact origin to backend CORS and exact callback/logout URLs to OIDC.
5. Smoke-test login, `/api/v1/me`, plan creation, review permissions and logout.

The circular origin dependency is handled by initially deploying the static
site without claiming live integration, then configuring the assigned origin
before authenticated smoke testing.
