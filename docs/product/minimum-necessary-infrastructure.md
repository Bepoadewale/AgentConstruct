# Minimum Necessary Infrastructure

AgentConstruct starts with the smallest, simplest AWS design that can safely meet the request. It does not start with Kubernetes, GPUs, or a large cloud bill.

The planner first reads hard requirements: region, data sensitivity, traffic, budget, availability, workload shape, runtime needs, and whether GPU or Kubernetes-specific features are truly required. It then checks the approved-resource inventory fixture for reusable services.

It evaluates these AWS families in a fixed, reviewable catalogue:

1. Static hosting: S3 and CloudFront.
2. Serverless API or event processing: Lambda and API Gateway.
3. Managed application: App Runner.
4. Managed containers: ECS Fargate.
5. Managed virtual machines: EC2.
6. Managed Kubernetes: EKS.
7. Managed AI endpoint.
8. CPU self-hosted inference.
9. GPU inference.

A candidate is rejected when it breaks a hard requirement. The planner estimates a cost range and an operational-complexity score for the candidates that remain. Candidates in the configurable cheapest-cost band are treated as cost-equivalent; AgentConstruct then chooses the least complex one.

The recommendation tells the user what it selected, what it will create or reuse, why simpler choices failed, and what would justify an upgrade.

## Current evidence

**Executed locally:** deterministic candidate generation, hard-constraint rejection, fixture inventory reuse, cost-range components, complexity scoring, and recommendation explanations.

**Simulated:** AWS inventory and pricing. They use checked-in fixtures, make no network call, and never report an estimate as an AWS bill.

**Not yet executed:** AWS discovery, live pricing, customer-specific discounts or commitments, and deployment of any selected architecture.
