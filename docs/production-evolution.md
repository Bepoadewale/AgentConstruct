# Production evolution

The local V1 is executable. The cloud-pilot design is now concrete and statically validated. Neither fact is an AWS execution claim.

## Next: cloud-pilot execution

Run one bounded, customer-account-style AWS pilot using Terraform, a scoped role and the prepared GitHub OIDC workflow. Prove create, signed request, policy denial, approval, GitOps reconciliation, observed failure/recovery, private telemetry, cost query, destroy and absence.

## Later: commercial hardening

- Customer AWS role assumption using STS rather than long-lived keys.
- GitHub App installation and scoped PR/webhook workflow.
- Enterprise OIDC/JWKS adapters.
- Real price/billing adapters and subscription controls.
- Model release/quality controls and AI-runtime telemetry as separate reviewed slices.

## Explicitly not V1

Multi-cloud, physical GPU fleets, edge fleets, model training, Kafka, SCIM, a service mesh and autonomous remediation. These add complexity before the core customer outcome is proven.
