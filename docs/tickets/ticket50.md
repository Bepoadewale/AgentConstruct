# ticket50 — Product strategy, architecture and scale review

PR: [#50 — docs: add product strategy and architecture review](https://github.com/Bepoadewale/AgentConstruct/pull/50)

Branch: `strategy/product-architecture-review`

Status: draft review.

## Problem / goal

Create an evidence-backed strategic review of AgentConstruct and document the goal of eventually supporting millions of customers without prematurely overbuilding the platform.

## Current repo state

- AgentConstruct has a local modular-monolith V1 with typed planning, policy, approvals, audit, read-only GitHub/AWS adapters and bounded execution contracts.
- The planner and pricing model are deterministic fixtures rather than live intelligence.
- Hosted durable persistence and production identity are contracts/follow-up work.

## Research / references used

- AWS SaaS Lens: https://docs.aws.amazon.com/wellarchitected/latest/saas-lens/saas-lens.html
- AWS SaaS isolation: https://docs.aws.amazon.com/wellarchitected/latest/saas-lens/full-stack-isolation.html
- Pulumi Cloud capabilities: https://www.pulumi.com/docs/iac/concepts/pulumi-cloud/
- HCP Terraform agents: https://developer.hashicorp.com/terraform/cloud-docs/agents
- Spacelift drift detection and worker limits: https://docs.spacelift.io/concepts/stack/drift-detection
- Repository source paths and tests cited directly in `docs/strategy/01-current-state-audit.md`.

## Work planned for the PR

- Audit the current repository and classify capabilities by evidence level.
- Assess the proposed AWS-specialized AI product direction and model options.
- Research adjacent infrastructure AI and SaaS control-plane products.
- Define an incremental architecture, MVP, evaluation/security strategy and roadmap.
- Document the long-term millions-customer scalability goal without claiming current scale.

## Work completed

- Added current-state audit.
- Added product-direction, competitive, model, architecture, MVP, evaluation/security, roadmap and decision-memo documents.
- Added `10-scale-and-multi-tenancy.md` with the millions-customer goal, scale dimensions, invariants, target control-plane shape and staged evolution.

## Acceptance criteria

- [x] Review distinguishes implemented, simulated, unexecuted and roadmap capabilities.
- [x] Product direction is challenged rather than accepted without evidence.
- [x] Model-training options are compared and a recommendation is made.
- [x] Competitor claims use official documentation or are marked as research limits.
- [x] MVP scope and measurable acceptance criteria are defined.
- [x] Security/evaluation strategy is defined.
- [x] Millions-customer scalability goal is documented without claiming current scale.
- [x] No application code or AWS resources are changed.

## Acceptance status

Met for the documentation-only review. No application behavior or cloud state was changed.

## Validation

- `python3 scripts/check_doc_conventions.py` — passed.
- `git diff --check` — passed.
- Documentation-only change; application test suite was not changed.

## Evidence files produced

- `docs/strategy/01-current-state-audit.md` through `docs/strategy/10-scale-and-multi-tenancy.md`.

## Boundaries

This PR is analysis and documentation only. It does not add a model provider, change planner behavior, deploy infrastructure, or claim production scale.

## Follow-up work

Implement the versioned tenant/evidence/model/job contracts and queue abstraction in a separate code PR after this review is accepted.
