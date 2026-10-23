# ticket126: Use a valid immutable CloudFormation onboarding template URL

PR: #126
Branch: fix/customer-connection-template-url

## Problem / goal

The production control plane still defaulted to a raw GitHub template URL. CloudFormation rejects that URL type, so the customer Quick Create handoff could not create the constrained discovery role.

## Current repo state

The separate template-host Terraform root has created the public, versioned, encrypted S3 template bucket. The serverless control-plane root needs the reviewed object URL supplied explicitly from the protected Terraform-plan environment.

## Research / references used

- AWS CloudFormation `TemplateURL` requirements.
- Existing `connection-template-host` Terraform root and generated immutable object URL.
- Existing GitHub Actions variable classification guard.

## Work planned for the PR

- Remove the invalid raw-GitHub default from the serverless Terraform input.
- Require `AWS_CONNECTION_TEMPLATE_URL` in the protected Terraform-plan environment.
- Classify that public URL in the workflow configuration guard and document its purpose.

## Acceptance criteria

- [x] CloudFormation template URL is explicit and immutable-by-key.
- [x] The GitHub plan workflow fails safely when it is missing.
- [x] The URL is documented as public metadata, never a secret.

## Acceptance status

Implemented and focused validation passed. The protected environment variable and a manual Terraform plan/apply remain required before production uses the corrected URL.

## Tests / validation performed

See `docs/test/test126.md`.

## Evidence files produced

- `docs/tickets/ticket126.md`
- `docs/test/test126.md`

## Boundaries

This PR changes only the control-plane configuration boundary. It does not create a customer connection, role, workload, or customer Terraform state.

## Follow-up work

- Merge and deploy the control-plane environment update through the existing manual Terraform plan/apply workflows.
- Re-run the customer Quick Create handoff and verify the constrained role.
