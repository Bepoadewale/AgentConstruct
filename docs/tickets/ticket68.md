# ticket68: Prevent stale local UI assets

- PR: #68
- Branch: `main`
- Status: complete

## Problem / goal

The local browser could retain an older HTML/CSS/JS build after a container rebuild, making the current UI changes appear absent.

## Current repo state

The product serves the web app through FastAPI `StaticFiles`, while local development uses a rebuilt Docker image.

## Research / references used

- Browser cache-control guidance: https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Cache-Control

## Work planned for the PR

- Mark local UI entrypoint and static assets as non-cacheable.
- Add an explicit asset version query to the HTML references.
- Rebuild and verify the served assets.

## Acceptance criteria

- The root page, stylesheet, and application script return `Cache-Control: no-store`.
- The HTML references versioned CSS and JavaScript assets.
- Existing lint, tests, smoke, browser-contract, and customer-plan E2E checks remain green.

## Acceptance status

- [x] No-store response headers added.
- [x] Versioned asset references added.
- [x] Local verification completed.

## Tests / validation performed

- `make lint`
- `make test`
- `make smoke`
- `make browser-contract`
- `make customer-plan-e2e`
- `python3 scripts/check_doc_conventions.py`

## Evidence files produced

- None. This is a local UI cache-control fix and does not execute a customer workload or AWS deployment.

## Boundaries

- No AWS resources or cloud credentials are touched.
- Local fixture mode remains bounded and non-production.

## Follow-up work

- If hosted deployments add a CDN, configure equivalent cache invalidation there.
