# Documentation map

Start with the [current-state audit](product/CURRENT_STATE_AUDIT.md), [product flow](product/PRODUCT_FLOW.md), [user stories](product/USER_STORIES.md), [plan approval architecture](architecture/PLAN_APPROVAL_ARCHITECTURE.md), [plan lifecycle](architecture/PLAN_LIFECYCLE.md), [approval RBAC](security/APPROVAL_RBAC.md), [minimum-necessary infrastructure](product/minimum-necessary-infrastructure.md), [the planner](architecture/planner.md), [AWS and observability](architecture/AWS_AND_OBSERVABILITY.md), [Day-2 operations](architecture/day2.md), [agent client strategy](product/agent-client-strategy.md), [customer AWS connection](architecture/customer-aws-connection.md), [cloud-pilot design](architecture/cloud-pilot.md), [validation evidence](VALIDATION.md), and numbered [customer workload test evidence](test/README.md).

- `product/`: current customer, product, packaging and roadmap material.
- `architecture/`, `security/`, cloud/reliability/GitOps pages: current technical contracts.
- `strategy/`: preserved historical strategy and commercial thinking. It is private and not public-repository material.
- `decisions/`: active architectural decisions.

Every document must clearly say whether a capability is executed locally, simulated, statically validated, planned for a cloud pilot or executed in cloud evidence.

Every customer workload test run must also create the next numbered `docs/test/testN.md` file. Do not store customer workload run evidence only in `docs/VALIDATION.md`.
