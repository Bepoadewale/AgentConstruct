# Decision memo

## My recommendation for davdeploy is...

Pursue the direction, but define davdeploy as an **AWS-first, outcome-to-architecture and governed-delivery platform**. Use AI as the interpretation and explanation layer; make the durable product the customer-specific infrastructure system of record, deterministic architecture evaluator, policy/approval boundary, and evidence-backed execution/operations loop.

## Answers to the ten decisions

1. **Should we pursue it?** Yes, if the first release stays narrow and proves fewer wrong/unsafe/expensive decisions, not merely faster Terraform generation.
2. **Why?** Small teams need platform judgment before they can afford platform staff. The current repository already has unusually strong governance foundations.
3. **What should it be?** AI-assisted infrastructure planning and governed AWS delivery, later expanding to observed optimization.
4. **Train or fine-tune?** Neither now. Use an existing model plus tools, schemas, deterministic planning and evaluation. Fine-tune only after consented traces prove a narrow cost/quality benefit.
5. **Strongest differentiation?** Persistent customer context + minimum-necessary architecture selection + policy/approval/audit + observed outcomes. Not model branding.
6. **Existing advantage?** Typed plans, non-EKS-first planner tests, tenant/RBAC, immutable approvals, AWS discovery, GitHub boundary, local evidence, and a real execution safety model.
7. **MVP?** One AWS architecture for a small GitHub-hosted API/web workload, with cost assumptions, security/operations trade-offs, one selected plan, approval, and plan-only delivery.
8. **Postpone?** Foundation-model training, broad multi-cloud, autonomous remediation, EKS/GPU expansion, production billing, and enterprise deployment variants.
9. **Biggest risks?** Incorrect recommendations, stale pricing, weak differentiation against AWS Q/Pulumi/coding agents, hosted persistence/auth gaps, and overclaiming cloud execution.
10. **First ten engineering tasks?**
   1. Freeze supported workload envelope and claims.
   2. Add benchmark schema and first 12 expert-reviewed scenarios.
   3. Expand repository evidence extraction.
   4. Add AWS pricing/catalog snapshot adapter.
   5. Add AWS region/quota/availability evidence adapter.
   6. Add model-backed intent adapter behind typed validation.
   7. Add prompt-injection and provider-failure regression tests.
   8. Operate hosted Postgres/RDS and real OIDC before external customer data.
   9. Complete one product-driven App Runner plan/apply/observe/destroy evidence run.
   10. Add real App Runner metrics/Cost Explorer evidence before Day-2 automation.

## Commercial view

Start with guided paid design partners, then offer team subscriptions for planning/governance and an optional deployment/operations tier. Usage-based model costs should be a pass-through or bounded product cost, not the sole value metric. Pricing, market size, conversion and willingness-to-pay remain hypotheses requiring interviews; this repository contains no validated market evidence.

## Three decisions needed before implementation

1. **Initial customer/workload boundary:** approve the small API/web workload envelope and the first five design-partner profile.
2. **Model/data policy:** choose the initial model provider and whether repository content may be sent to it, with explicit retention and opt-in rules.
3. **Execution posture:** decide whether the next release is plan-only for external users or includes one tightly controlled App Runner pilot with real apply/destroy evidence.

