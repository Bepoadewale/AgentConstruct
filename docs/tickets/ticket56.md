# ticket56 — Planner evaluation and regression benchmark

PR: planner evaluation and regression benchmark

Branch: `feature/planner-evaluations`

Status: ready for review

## Problem / goal

The planner has unit tests but no compact regression suite proving that simple workloads
avoid unnecessary Kubernetes and GPU workloads receive an appropriate profile. Add a
deterministic benchmark boundary without using an LLM or live AWS.

## Current repo state

- `AwsV1Planner` is deterministic and fixture-priced.
- Evidence, queue, model, usage and execution contracts now provide scale-ready seams.
- Planner quality is not yet measured against an explicit scenario catalog.

## Research / references used

- `apps/api/src/agentconstruct/planner.py`
- `apps/api/src/agentconstruct/domain.py`
- `docs/strategy/07-evaluation-and-security.md`
- AWS Well-Architected Framework: https://docs.aws.amazon.com/wellarchitected/latest/framework/the-pillars-of-the-framework.html

## Work planned for the PR

- Add typed scenario/result benchmark contracts.
- Add simple and GPU inference regression fixtures.
- Add tests and evaluation documentation.

## Acceptance criteria

- [x] Tiny API scenario rejects EKS/Kubernetes as the selected profile.
- [x] GPU inference scenario selects EKS with a GPU node group.
- [x] Benchmark is deterministic and local-only.
- [x] Documentation distinguishes regression evidence from production quality evidence.

## Acceptance status

Met for the initial deterministic benchmark. Expert-reviewed scenarios, live pricing and observed production outcomes remain follow-up work.

## Tests / validation performed

```bash
make lint
make test
python3 scripts/check_doc_conventions.py
git diff --check
```

Results: expected 145 tests; lint and documentation checks must pass.

## Evidence files produced

No customer workload or AWS execution occurs; no `docs/test/test56.md` is produced.

## Boundaries

This PR does not claim planner correctness for all AWS services, live capacity, or production scale.

## Follow-up work

Expand scenarios with expert reference architectures, cost accuracy and security/Terraform validators.
