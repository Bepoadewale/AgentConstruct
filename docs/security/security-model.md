# Security Model

## The rule

**AI proposes. Policy and approved deterministic systems authorize and execute.**

The browser holds only a short-lived local fixture token in this demo. It does not receive cloud, Kubernetes, Terraform or secret credentials. The executor can call a fixed local fixture API only.

| Threat | V1 control |
| --- | --- |
| Caller selects a different tenant | All reads/writes are filtered by organisation in the signed principal |
| Caller selects a privileged role | Role comes from the signed local fixture identity, not request headers |
| LLM suggests unsafe execution | Typed schema, small planner catalogue, policy and approval happen before execution |
| Requester self-approves production | Distinct operator is required |
| Approved plan changes | Approval stores and verifies the exact plan hash |
| Cross-tenant project access | Service checks organisation ownership |
| Executor becomes a cloud backdoor | Local executor has no shell or cloud capability and only fixed endpoints |

## Planned cloud boundary

The static AWS contract uses private EKS and RDS, ECR immutable images, Secrets Manager references, IRSA, non-root/read-only containers, probes, a PDB and a default-deny NetworkPolicy. An optional future browser route exposes only Console/API/identity paths; Grafana, Tempo, Prometheus, Argo, Kubernetes, databases and secrets remain private.

Trusted OIDC/JWKS identity, customer-cloud STS role assumption, External Secrets delivery and network enforcement are roadmap execution work. The contracts do not prove those controls in AWS.
