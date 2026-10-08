# Product vision

> **Historical strategy note.** Superseded on 2026-10-08 by [AgentConstruct V1 product vision](product/vision.md). Preserved for decision history only.

## Positioning

**Governed AI Operations Platform**

Give enterprises a single control plane for operating AI workloads across teams, models, agents, clusters, and edge devices without giving every developer, service, or agent broad cloud or Kubernetes administrator access.

## The problem

As organisations move from AI experiments to production, they accumulate:

- multiple model providers and runtime stacks;
- shared GPU/CPU capacity and unpredictable costs;
- developers and agents requesting infrastructure actions;
- model releases that need safe rollout and rollback;
- fragmented audit, policy, reliability, and cost evidence;
- sensitive data constraints and tenant boundaries.

Cloud AI platforms solve portions of this. Enterprises still assemble policy, tenancy, workflow, cost, agent, infrastructure, and operational controls around them.

## Value proposition

> Enable teams and AI agents to consume approved AI capabilities quickly, while centrally enforcing the controls needed for security, reliability, compliance, and cost management.

## What it does

1. Authenticates human, service, and agent requests.
2. Enforces tenant, quota, policy, and approval rules.
3. Routes requests to approved model/runtime capacity.
4. Governs model registration, evaluation, rollout, and rollback.
5. Records operational telemetry, usage, cost allocation, and audit evidence.
6. Helps operators detect and safely remediate bounded failures.
7. Extends the same principles to distributed edge devices where required.

## What it does not do

- Replace a cloud provider, model provider, or Kubernetes distribution.
- Promise universal model quality or eliminate human accountability.
- Grant autonomous agents unrestricted production authority.
- Treat a public demo as production validation.

## One-sentence explanations

Technical: a vendor-neutral, governed AI operations control plane for multi-tenant model, agent, and infrastructure workloads.

Executive: a control centre that lets a company scale AI safely without making every team an AI-infrastructure operator.
