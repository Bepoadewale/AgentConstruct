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

**Simulated:** the executor reports a deterministic local result. It does not run Terraform, create cloud resources, open a pull request, call Argo, or call Kubernetes.

**Planned cloud pilot:** profile-specific Terraform rendering, reviewed desired-state publication, and independent cloud observation.
