# ticket48 — Production identity binding and hosted sign-in guardrails

PR: [#48 — feat: harden hosted identity binding](https://github.com/Bepoadewale/AgentConstruct/pull/48)

Branch: `feature/production-identity-binding`

Status: ready for review.

## Problem / goal

The local signed identity is useful for demos, and a JWT/JWKS verifier already exists, but hosted authentication must not trust caller-selected organization or role claims. A production identity must be mapped to a server-side workspace membership. Hosted mode must also reject the local fixture login endpoint.

## Current repo state

- Local login issues signed demo tokens for seeded identities.
- JWKS verification validates signature, issuer, audience and expiration.
- `principal_from_claims` currently uses `org` and `role` claims directly.
- Workspace membership is represented by the users table and existing tenant checks.
- Hosted App Runner mode can still fall back to local login if JWKS is not configured.

## Research / references used

Local repo references:

- `apps/api/src/agentconstruct/security.py`
- `apps/api/src/agentconstruct/main.py`
- `apps/api/src/agentconstruct/models.py`
- `docs/security/security-model.md`
- `docs/IMPLEMENTATION_STATUS.md`

## Work planned for the PR

- Bind verified external subject to the server-side `ProductUser` membership record.
- Ignore caller-provided `org`/`role` claims for authorization decisions.
- Require JWKS configuration when hosted mode is enabled.
- Reject local-login in hosted mode.
- Preserve local fixture behavior and tests.
- Add tests for forged org/role claims, missing membership, hosted login rejection and valid JWKS claim handling.
- Document the production identity boundary and remaining IdP/invite work.

## Acceptance criteria

- [x] Hosted mode cannot use local fixture login.
- [x] Hosted mode cannot start without JWKS issuer/audience configuration.
- [x] External subject is authorized only through server-side membership.
- [x] Forged organization/role claims cannot escalate access.
- [x] Local fixture demo remains reproducible.
- [x] Tests pass.

## Acceptance status

Met for server-side identity binding and hosted-mode guardrails. A real external IdP is still a deployment/configuration follow-up.

## Tests / validation performed

```bash
make lint
make test
python3 scripts/check_doc_conventions.py
GITHUB_EVENT_NAME=pull_request GITHUB_PR_NUMBER=48 python3 scripts/check_doc_conventions.py
git diff --check
```

Results:

- `make lint` passed.
- `make test` passed: 118 tests.
- Documentation convention checks passed, including PR #48 mode.
- `git diff --check` passed.

## Evidence files produced

No customer workload cloud test is planned for this PR.

## Boundaries

- This PR does not deploy or configure a hosted identity provider.
- Invite flows, passwordless login, SSO configuration and SCIM remain follow-up work.
- No secrets or identity-provider credentials are committed.

## Follow-up work

- Configure a real OIDC provider and hosted callback/session flow.
- Add workspace invitation and membership-management UI.
- Add production session revocation and refresh-token handling.
