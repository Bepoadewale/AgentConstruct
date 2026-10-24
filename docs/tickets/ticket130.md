# ticket130 — Live customer cloud pilot evidence

PR: [#130 — docs: record live customer cloud pilot evidence](https://github.com/Bepoadewale/davdeploy/pull/130)
Branch: `docs/live-customer-pilot-evidence`

## Problem / goal

Record one governed, customer-style AWS workload lifecycle using DavDeploy's public API contracts: cloud connection verification, plan review, approved apply, observation, governed destroy, and absence verification.

## Current repo state

The original customer workspace has a verified customer-cloud connection. Its bounded runner
created the customer-sandbox foundation from an approved, checksum-bound Terraform plan
(`9187d820-c769-40dd-93ff-01b90f804fd9`) and built an immutable customer image
(`70935f5c-1f71-43fc-9d1e-561c2b47f43d`). The VPC, subnets, security group, VPC connector,
log group, and ECR repository remain intentionally present. No App Runner service has been
created and no destroy plan or destroy has run.

On 2026-10-24, the founder account authenticated successfully, but has no customer plan or
cloud-connection records. Its GitHub connection reports `SIMULATED`: the production API has no
GitHub App configuration. The existing customer user's credential is not present in the local
Keychain, so its tenant-scoped approval and execution records cannot be safely continued.

## Research / references used

- Cloud execution results and saved-plan objects in the protected customer state bucket.
- AWS tagged-resource, ECR, App Runner, CodeBuild, Lambda, API Gateway, Aurora, Cognito and
  Cloudflare Pages read-only checks performed on 2026-10-24.
- Merged product controls through PR #151 and the public API contract.

## Work planned for the PR

- Reconcile the completed authenticated plan artifact through the event-driven worker.
- Configure and install a least-privilege GitHub App before claiming private repository onboarding.
- Restore authorised access to the existing customer workspace, or explicitly create a new
  customer workspace and connection for this pilot.
- Start the service-enabled apply only after a reviewed saved plan is recorded.
- Record actual service outputs and observed state.
- Produce, review, and execute a separately saved destroy plan.
- Verify workload-resource absence while retaining the customer connection.

## Acceptance criteria

- [x] Customer-sandbox foundation apply uses a saved, reviewed plan artifact.
- [x] Foundation outputs are ingested from the real run.
- [ ] Private GitHub onboarding uses an installed, non-fixture GitHub App.
- [ ] Customer tenant approval workflow is validated with authorised customer access.
- [ ] Service-enabled apply uses a saved, reviewed plan artifact.
- [ ] Service outputs and observed state are recorded from the real run.
- [ ] Destroy uses its own reviewed saved destroy plan.
- [ ] Absence verification succeeds.
- [ ] `docs/test/test130.md` contains the complete real-AWS evidence without secrets.

## Acceptance status

Partially complete. Foundation apply and immutable image delivery are evidenced, but the private
GitHub integration and authorised existing-customer session are prerequisites for the remaining
service apply, observation, and governed-destroy stages.

## Tests / validation performed

- Read-only AWS resource and execution-artifact inspection.
- Cognito founder authentication and authenticated `/api/v1/me` request.
- Authenticated founder GitHub, customer-plan and cloud-connection API checks.
- API health and Cloudflare Pages production health checks.
- Local documentation-convention and diff validation before review.

## Evidence files produced

- `docs/test/test130.md`

## Boundaries

No customer credentials, external IDs, access keys, or unreviewed Terraform applies are recorded
or used. Destruction of the retained customer-sandbox resources requires a separate explicit
owner approval after the service smoke test.

## Follow-up work

The API, worker, CodeBuild runner, and Terraform controls are defined by merged control-plane PRs
through #151. Live account, CodeBuild, S3 artifact, API, Cognito, GitHub and Cloudflare checks are
recorded in `docs/test/test130.md`. Configure and install the GitHub App, restore authorised
customer access or create an explicitly approved replacement customer workspace, then complete
the service and destruction stages with fresh evidence.

