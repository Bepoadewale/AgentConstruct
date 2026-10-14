# MVP scope

## Recommended MVP

AgentConstruct should first serve one narrow job: **choose and explain a safe, low-complexity AWS architecture for a small GitHub-hosted web/API workload, before anyone deploys it.**

### Supported workload envelope

- One AWS account and one region per plan.
- Python FastAPI or Node HTTP API, optionally containerized.
- Stateless or PostgreSQL-backed application.
- Low-to-moderate traffic with explicit average/peak requests.
- Public HTTPS entry point or private service boundary.
- One staging or production environment initially.
- Metrics-only monitoring contract; logs/traces are explicitly separate.

Candidate families: Lambda/API Gateway, App Runner, ECS/Fargate, EC2, and EKS only when a tested Kubernetes-specific requirement exists. Managed model API, CPU inference and GPU inference remain explicit profiles, not defaults.

## MVP user journey and acceptance criteria

1. **Sign in:** local fixture for development; hosted OIDC required before external customers. Acceptance: server-side subject maps to workspace membership; claimed role/org cannot elevate.
2. **Connect evidence:** GitHub repository and optional read-only AWS account. Acceptance: no long-lived keys; repository/account scope is visible; revoked access fails closed.
3. **Describe:** natural-language outcome plus budget, region, traffic, availability and data class. Acceptance: missing material values produce targeted questions.
4. **Analyze:** repository evidence + typed WorkloadSpec. Acceptance: every material inferred field has provenance/confidence.
5. **Recommend:** exactly one primary architecture with alternatives/rejections available. Acceptance: simple workload is not EKS; hard constraints are enforced; no unsupported claim is hidden.
6. **Review:** resources, security, monitoring, cost range, assumptions, risks, rollback and upgrade triggers. Acceptance: estimate says catalog/timestamp/assumptions and is not called a bill.
7. **Submit/approve:** immutable digest and workspace approval. Acceptance: submitted content cannot mutate; decision is server-side and audited.
8. **Optional later execution:** plan-only renderer first; live apply only after separate pilot. Acceptance: approval alone cannot deploy.

## Postpone

- Foundation-model training and broad autonomous agents.
- Multi-cloud execution.
- EKS/GPU as a default or broad catalog claims.
- Real-time automated remediation.
- Full billing/subscription platform.
- Enterprise SCIM/air-gapped deployment.
- General arbitrary Terraform generation.

## Business MVP boundary

The first paid pilot should be a guided architecture and approval workflow, not “press a button and we own your cloud.” A customer can receive high-value recommendations before granting deployment permission; that reduces trust friction and makes evidence collection safer.

