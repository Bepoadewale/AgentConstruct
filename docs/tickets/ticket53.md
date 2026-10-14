# ticket53 — Evidence-backed planning boundary

PR: [#53 — feat: add evidence-backed planning boundary](https://github.com/Bepoadewale/AgentConstruct/pull/53)

Branch: `feature/evidence-backed-planning`

Status: draft.

## Problem / goal

The planner currently accepts inventory but does not expose a unified evidence bundle or pricing source in its output. Add typed provenance so a recommendation can explain what was known, when it was captured, and whether pricing is fixture or live.

## Current repo state

- `AwsV1Planner` uses a deterministic catalog and optional `CloudInventorySnapshot`.
- Repository analysis is persisted separately and can feed `WorkloadSpec.repository_analysis`.
- `ArchitecturePlan` includes assumptions but not typed evidence references.
- PR #51 added `EvidenceRef` and `CostEvidence` contracts.

## Research / references used

- `apps/api/src/agentconstruct/planner.py`
- `apps/api/src/agentconstruct/domain.py`
- `apps/api/src/agentconstruct/integrations.py`
- `apps/api/src/agentconstruct/contracts.py`
- AWS Cost Explorer API: https://docs.aws.amazon.com/cost-management/latest/userguide/ce-api.html
- AWS Well-Architected pillars: https://docs.aws.amazon.com/wellarchitected/latest/framework/the-pillars-of-the-framework.html

## Work planned for the PR

- Add a typed `PlanningEvidence` bundle and pricing-catalog protocol.
- Add a deterministic fixture pricing catalog adapter with explicit estimate status.
- Allow the planner to attach evidence references and limitations to the selected plan.
- Preserve fixture behavior when no evidence bundle is supplied.
- Add tests and documentation; do not call live AWS pricing APIs in CI.

## Acceptance criteria

- [x] Planning evidence includes repository, inventory, pricing and capability references.
- [x] Pricing identifies catalog version, timestamp, assumptions and actual-billing status.
- [x] Architecture plans expose evidence references and limitations.
- [x] Missing evidence is labeled fixture/unknown, not silently treated as live.
- [x] Existing planner decisions remain unchanged.
- [x] No AWS API or billing call occurs in CI.

## Acceptance status

Met for the typed evidence bundle and deterministic catalog boundary. Live AWS pricing, quotas and availability remain follow-up adapters.

## Tests / validation performed

Validation performed:

```bash
make lint
make test
python3 scripts/check_doc_conventions.py
git diff --check
```

Results: lint passed; 136 tests passed; documentation conventions passed; diff check passed.

## Evidence files produced

No customer workload or AWS execution is planned. No `docs/test/test53.md` is required unless a live customer workload is deliberately run.

## Boundaries

This PR does not claim live pricing, quota, service availability or AWS deployment evidence.

## Follow-up work

Add live read-only AWS pricing/catalog, quotas, regional availability and inventory adapters after the evidence contract is accepted.
