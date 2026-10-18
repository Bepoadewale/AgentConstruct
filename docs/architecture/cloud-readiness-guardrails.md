# Cloud-readiness guardrails

davdeploy now has a local preflight that answers:

> If a future cloud operator workflow existed, would this approved plan be safe to take to the next review step?

It does not run Terraform, call AWS, write GitHub, merge a pull request, sync Argo CD, or deploy anything.

## Required checks

The preflight records a checklist for:

- exact approved customer-plan digest;
- policy result;
- generated plan-only Terraform contract;
- no exposed apply command;
- expected AWS account;
- allowed AWS region;
- required ownership tags;
- budget ceiling;
- reviewed desired-state PR/check state;
- davdeploy runtime identity availability;
- dry-run/plan-only execution mode.

## States

- `BLOCKED_GUARDRAIL_FAILURE`: one or more guardrails failed.
- `BLOCKED_CLOUD_RUNTIME_NOT_CONFIGURED`: every other guard is satisfied, but the product runtime identity is not configured.
- `READY_FOR_AUTHORIZED_CLOUD_PLAN`: all local preflight checks passed. This is still not deployment approval or execution.

## Evidence boundary

This is implemented and tested locally. It is a guardrail and operator UX layer before any real cloud action is introduced.

Future work must still add a separately approved authenticated Terraform plan path, followed by an explicitly gated apply path only after operator confirmation and cloud-pilot authorization.
