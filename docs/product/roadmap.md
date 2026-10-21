# Product Roadmap

1. **V1 foundation:** local intent → plan → policy → approval → bounded execution → observation → destruction.
2. **BYOC execution:** scoped AWS role assumption, live inventory and pricing, profile-specific Terraform rendering, GitHub App, desired-state publication and GitOps observation.
3. **AI runtime controls:** metering, release governance, model quality evidence and cost intelligence.
4. **Business controls:** enterprise identity, policy packs, support and commercial packaging.

The local V1, cloud-pilot contracts and future cloud operator workflow are now implemented and statically validated. The next phase is a separately authorised cloud pilot; it must preserve the same evidence boundary.

Not V1: multi-cloud, physical GPU fleets, edge fleets, model training, Kafka platform, SCIM or full autonomous remediation.

## When the production domain exists

Complete the transactional-email activation as one reviewed change:

1. Verify the production domain as an Amazon SES identity in `us-east-1` and publish the SES DKIM records in the authoritative DNS zone.
2. Enable the SES account-level suppression list for both bounces and complaints.
3. Request SES transactional production access in `us-east-1`; do not enable customer delivery while the account remains limited to sandbox recipients.
4. Select a domain-covered From address and add `SES_IDENTITY_ARN` and `SES_FROM_ADDRESS` to the `terraform-plan` GitHub environment secrets.
5. Run and review the manual Terraform plan, then run the separate manual apply only after confirming that its changes are limited to the approved email configuration and identity-scoped `ses:SendEmail` permission.
6. Validate signup OTP and workspace invitation delivery to an external address, including acceptance, resend, cancellation, expiry, bounce suppression, audit evidence, and the absence of sender credentials in the browser bundle.

Until this checklist is complete, automatic workspace invitation delivery must remain disabled and must fail truthfully rather than expose an invitation token or claim that email was sent.
