# Self-hosted administrator runbook

## Install and validate

```bash
make bootstrap-local
make smoke
make validate-environment
make admin-diagnostics
```

For hosted mode, set a PostgreSQL URL and a trusted `AGENTCONSTRUCT_JWKS_URL`.
The validator rejects SQLite and the local fixture-signing key in hosted mode.

## Upgrade and rollback

1. Take a database backup using the operator-approved PostgreSQL mechanism.
2. Deploy the new image or checkout; run `make validate-environment`.
3. Start the API once so its versioned migrations run, then run `make smoke`.
4. If validation fails, restore the verified backup and redeploy the preceding
   immutable image/commit. Do not manually edit production tables.

## Incident and privacy operations

- Use the audit-evidence API to collect tenant-scoped review evidence.
- Create export/deletion requests through the data-lifecycle API; execution is
  intentionally an operator-approved workflow until a retention provider is
  configured.
- Support tickets and API-credential revocations are tenant-scoped and audited.

## Security posture

The API uses bearer tokens, not browser cookies; CSRF tokens are therefore not
applicable. CSP, anti-framing, referrer and permissions headers are applied at
the API boundary. Enable `AGENTCONSTRUCT_RATE_LIMIT_PER_MINUTE` at the local
edge seam or replace it with a shared production limiter.
