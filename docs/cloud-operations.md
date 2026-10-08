# Cloud operations

**State: future pilot runbook. Do not treat these contracts as an AWS deployment.**

Terraform is the only planned authority for creating and destroying AgentConstruct AWS foundation resources. A future pilot must use a dedicated state bucket, lock table, project tags and an account/region guardrail.

## Before a future apply

- Confirm the AWS account, region, budget and project tags.
- Review Terraform plan output. Reject unexpected public access, broad IAM, unencrypted state or untagged resources.
- Use short-lived role credentials. Never use a long-lived access key in GitHub, a script or a repository file.
- Confirm that database, observability, Kubernetes and secret endpoints remain private.

## Runtime checks

- Wait for EKS, External Secrets, the API, observer and telemetry components with bounded readiness checks.
- Send one signed tenant request and verify policy, approval, audit and observed state.
- Deliberately use a bad image or failed readiness response. The system must record `FAILED`, not `READY`.
- Delete one API Pod and confirm the second replica continues serving while the PDB protects availability.
- Record Prometheus/Tempo/Grafana evidence. Query Cost Explorer after 24–48 hours; billing data can be delayed.

## Destroy

Destroy is a governed operation. Review the exact target, use only project tags/state, destroy with Terraform and then query EKS, RDS, ECR, Secrets Manager, IAM and tagged network resources for absence. State/lock/budget guardrails may be intentionally retained only if the runbook says so.
