# Evaluation and security strategy

## Evaluation framework

Do not rely on an LLM grader. Use a layered benchmark:

1. **Schema tests:** typed output, required fields, provenance, unknown handling, digest stability.
2. **Capability tests:** selected AWS service actually supports runtime, data, traffic, region and availability requirements.
3. **Policy tests:** public exposure, IAM scope, encryption, backup, data residency, budget and destructive actions.
4. **Cost tests:** range directionality, catalog timestamp, component attribution, impossible-budget detection; compare to AWS Pricing/Cost Explorer evidence when available.
5. **IaC tests:** formatter/validator, module contract, plan-only behavior, no arbitrary command path.
6. **Operational tests:** failure/readiness, rollback, destroy, output capture, observed-vs-command-success distinction.
7. **Human expert review:** platform/AWS engineers score architecture suitability, simplicity, uncertainty and explanation quality.

## Benchmark scenarios

- Static site: S3/CloudFront, no compute server.
- Small stateless API: App Runner or Lambda, not EKS.
- Event-driven document processor: Lambda/SQS/S3.
- PostgreSQL API: managed database only when persistence requires it.
- Impossible budget: refuse or ask which constraint can change.
- High availability: reject a single-instance design when target requires stronger resilience.
- Kubernetes-specific multi-service/GPU scheduling: EKS becomes justified.
- Managed model endpoint vs self-hosted inference: explain control/cost/privacy trade-off without fabricated break-even.
- Existing approved VPC/database/observability: reuse before duplicate creation.
- Prompt injection in repository README: treat as untrusted content and preserve policy boundary.
- Stale price or unavailable region: downgrade confidence and require verification.

## Security controls

### Planning stage

- Treat prompts, repository files, webhooks and model output as untrusted.
- Validate against allowlisted capabilities and AWS/provider schemas.
- Deny unsupported resource types and ambiguous privileged requests.
- Keep secrets out of prompts, plans, logs, evidence and model training.
- Use organization/project ownership checks on every read/write.
- Record actor, source evidence, policy bundle, catalog timestamp and digest.

### Execution stage

- Short-lived STS/OIDC only; no customer keys in the product.
- Separate discovery and execution roles; least privilege and account/region/tag guards.
- Exact approved digest, independent approval, protected branch/PR where applicable.
- Bounded adapters; no arbitrary shell, Terraform, kubectl or raw cloud API from model output.
- Explicit apply confirmation, timeout, readiness observation and destroy path.
- Capture safe outputs/resource IDs, redact secrets, and verify absence after teardown.

## Refusal/escalation conditions

Refuse or ask for human review when budget, region, quota, data residency, availability, IAM, backup, or security requirements cannot be proven. Never turn missing evidence into confidence.

