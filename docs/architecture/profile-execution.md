# Profile-aware execution

AgentConstruct does not send every approved plan to Kubernetes.

The planner selects an architecture profile. The executor then selects the matching, bounded delivery contract. A static site uses a static-hosting contract; a Lambda API uses a serverless contract; App Runner and ECS use their own managed-container contracts. GitOps and Kubernetes are required only for the `aws-eks-governed` profile.

| Selected profile | Delivery contract | GitOps / Kubernetes |
| --- | --- | --- |
| Static, Lambda, App Runner, EC2, or managed AI | The matching Terraform contract | Not used |
| ECS, CPU inference, or GPU inference | The matching Terraform contract | A reviewed desired-state change can be used when it helps; Kubernetes is not required |
| EKS | The EKS Terraform contract | A reviewed GitOps pull request and Argo observation; Kubernetes is required |

This prevents a request that needs a simple managed application from accidentally becoming an EKS deployment.

## Current evidence

**Executed locally:** the planner stores the selected profile in the immutable plan; the local worker passes that profile to the bounded executor; tests prove that an App Runner recommendation has no Kubernetes contract and an EKS recommendation does.

**Implemented / unexecuted:** approved `aws-app-runner` customer-plan revisions can now render a plan-only Terraform contract. The rendered contract includes module inputs for the service, repository/branch, ECR/source boundary, IAM boundary, secret references, HTTPS assumptions, Prometheus/Grafana monitoring contract, required tags, selected account/region, revision ID and exact approved digest. The renderer persists the preview and exposes only offline validation commands. It does not expose `terraform apply`.

**Simulated:** the executor reports a deterministic local result. Fixture desired-state PR publication records a reviewed-PR contract without writing GitHub.

**Planned cloud pilot:** actual GitHub PR writes, authenticated AWS Terraform plan, apply, independent cloud observation and destroy remain separate, explicit future work.
