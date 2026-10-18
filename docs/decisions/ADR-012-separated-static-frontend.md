# ADR-012: Separate the static frontend from the control plane

## Status

Accepted. Supersedes ADR-009 for current implementation.

## Context

The product now has multiple authenticated routes, shared client state, role
specific views and enough interaction complexity to justify a typed frontend.
Serving it from the API couples releases and prevents zero-cost static hosting.

## Decision

Maintain the React/TypeScript/Vite client in the private
`Bepoadewale/davdeploy-frontend` repository and host its static output on
Cloudflare Pages Free. This repository owns the AWS-hosted API and all
authoritative logic. The boundary is authenticated HTTPS using the committed
OpenAPI v1 contract and explicit exact-origin CORS.

Cloudflare Functions, Workers, KV, D1, R2 and other runtime products are not
part of the design. A custom domain is optional.

## Consequences

- Frontend and backend build and release independently.
- The browser needs a configured public API URL and OIDC settings.
- API contract drift and CORS configuration are tested.
- Backend authorization cannot depend on route guards or browser state.

