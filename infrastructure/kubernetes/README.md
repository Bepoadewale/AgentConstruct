# Kubernetes runtime contract

These are static cloud-pilot contracts. They are not applied by this repository.

The intended runtime has two API replicas, a disruption budget, non-root containers, a read-only filesystem, dropped Linux capabilities, bounded CPU/memory, probes, IRSA and a default-deny NetworkPolicy. The current NetworkPolicy is deliberately closed; a future rendered customer overlay must add only the reviewed DNS, database, OTel and GitOps paths it needs.

The internal ALB ingress routes only Console/API traffic. It is not a public endpoint and it does not expose observability, Argo, Kubernetes, databases or secrets. The AWS Load Balancer Controller and its own scoped role are future runtime-bootstrap work; see the [controller contract](../terraform/modules/alb-controller/README.md).

The placeholders are intentional. A future approved delivery workflow replaces them with an ECR image digest and Terraform outputs. It must not place a secret value in Git.
