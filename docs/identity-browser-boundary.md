# Identity and browser boundary

Local V1 uses a signed development token. Production uses the `JwksIdentityVerifier` interface with a trusted issuer, exact issuer/audience checks and JWKS signature verification.

For a future browser deployment, the OIDC client must list only exact redirect and logout URLs for the Console origin. CORS must allow only that same explicit Console origin and only the API methods/headers it needs. Wildcards are not allowed for authenticated browser access.

The browser receives an identity token/session only. It does not receive AWS credentials, Kubernetes credentials, Terraform state, GitHub App credentials or secret values.
