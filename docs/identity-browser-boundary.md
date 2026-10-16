# Identity and browser boundary

Local V1 uses a signed development token. Production uses the `JwksIdentityVerifier` interface with a trusted issuer, exact issuer/audience checks and JWKS signature verification.

The static browser client is owned by the private
`Bepoadewale/agentconstruct-frontend` repository. Its OIDC client must list only
exact redirect and logout URLs for the deployed `pages.dev` origin and any
later custom domain. `AGENTCONSTRUCT_ALLOWED_FRONTEND_ORIGINS` must contain the
same exact HTTPS origins. Wildcards, URL paths and public HTTP origins fail
closed; localhost HTTP is accepted only for development.

The API uses bearer authorization and does not enable cross-origin credential
cookies. Preview origins are not automatically trusted; each must be explicitly
approved or it cannot read authenticated API responses.

The browser receives an identity token/session only. It does not receive AWS credentials, Kubernetes credentials, Terraform state, GitHub App credentials or secret values.
