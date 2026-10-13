# Terraform plan-only review

AgentConstruct now has a governance record for the step between local cloud-readiness preflight and a future authenticated cloud plan.

The flow is:

1. A customer-plan revision is approved.
2. The selected profile must be `aws-app-runner`.
3. AgentConstruct renders the App Runner Terraform contract.
4. Cloud-readiness preflight must pass for the exact approved digest.
5. A workspace administrator requests a Terraform plan-only review.
6. AgentConstruct records the command shape, digest, target account/region evidence, preflight evidence and the fact that apply is unavailable.

Local mode is intentionally conservative. It records the only allowed `terraform init -backend=false` and `terraform plan -refresh=false` command shape, but it does not claim an authenticated AWS plan. Authenticated mode remains gated by both the request field `allow_cloud_plan=true` and the process environment variable `ALLOW_CLOUD_PLAN=true`.

This endpoint never exposes `terraform apply`, `terraform destroy`, arbitrary shell, Kubernetes access, cloud credentials or workload mutation.

Current status: implemented and locally tested as plan-review governance evidence. Authenticated AWS plan execution remains an operator action for a later phase.
