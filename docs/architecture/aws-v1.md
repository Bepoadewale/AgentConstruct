# AWS V1 Architecture Families

AWS is the only provider in the V1 planner. The planner does not make EKS the default.

| Family | Typical use | Why it may be rejected |
| --- | --- | --- |
| S3 + CloudFront | Static content | A runtime or private application workflow is needed. |
| Lambda + API Gateway | Short stateless or event-driven work | A long-running container, GPU, or complex service runtime is needed. |
| App Runner | One small containerised API | Higher traffic, multiple services, or special runtime control is needed. |
| ECS Fargate | Container services without Kubernetes | Kubernetes-only control or GPU support is required. |
| EC2 | Long-lived or host-controlled work | Managed options meet the need with less operational work. |
| EKS | Kubernetes-specific scheduling, isolation, or policy | The workload does not need Kubernetes. |
| Managed AI endpoint | An approved managed model is acceptable | Data, model-control, or GPU requirements rule it out. |
| CPU or GPU inference | Self-hosted model serving | Managed AI or simpler compute meets the request. |

All current monthly amounts are fixture estimates in USD. They include stated assumptions and are not actual billing evidence. A future selected profile will render only the resources it needs; Terraform must not create the full EKS reference stack for a simple App Runner plan.
