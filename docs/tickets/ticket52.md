# ticket52 — Queue and model gateway boundaries

PR: [#52 — feat: add queue and model gateway boundaries](https://github.com/Bepoadewale/AgentConstruct/pull/52)

Branch: `feature/queue-model-gateway`

Status: draft.

## Problem / goal

The current worker and intent provider are useful local implementations but are not explicit replacement points for future SQS/EventBridge transport or multiple model providers. Add those boundaries without changing the existing customer workflow.

## Current repo state

- `agentconstruct.worker` polls PostgreSQL and processes discovery/cloud/local execution paths.
- `IntentProvider` has a deterministic implementation, but no model-call metadata or provider gateway.
- PR #51 added typed `JobEnvelope`, `ModelRequest`, `ModelResponse` and usage contracts.

## Research / references used

- `apps/api/src/agentconstruct/worker.py`
- `apps/api/src/agentconstruct/intent.py`
- `apps/api/src/agentconstruct/contracts.py`
- HCP Terraform agents: https://developer.hashicorp.com/terraform/cloud-docs/agents
- AWS SaaS Lens: https://docs.aws.amazon.com/wellarchitected/latest/saas-lens/saas-lens.html

## Work planned for the PR

- Add a transport-neutral `JobQueue` protocol with a PostgreSQL adapter and in-memory test adapter.
- Persist generic jobs with tenant scope, idempotency, attempts, timeout, retry and dead-letter state.
- Add a provider-neutral `ModelGateway` with deterministic fixture and disabled/fail-closed adapter.
- Record model/provider/prompt/version/usage metadata without secrets.
- Add tests and documentation; preserve current worker and intent behavior.

## Acceptance criteria

- [x] Duplicate tenant/idempotency submissions return one durable job.
- [x] Queue claims are tenant-scoped and transition through retry/dead-letter states.
- [x] Job timeout, attempt and trace metadata are persisted.
- [x] Model gateway returns typed validated responses and usage metadata.
- [x] Disabled model mode fails closed without execution authority.
- [x] Existing local workflow and tests remain green.
- [x] No AWS resources or external model calls occur in CI.

## Acceptance status

Met for the PostgreSQL and in-memory queue adapters plus deterministic/disabled model gateway. Existing worker wiring and a real external model provider remain follow-up work.

## Tests / validation performed

Validation performed:

```bash
make lint
make test
python3 scripts/check_doc_conventions.py
git diff --check
```

Results: lint passed; 133 tests passed; documentation conventions passed; diff check passed.

## Evidence files produced

No customer workload or AWS execution is planned. No `docs/test/test52.md` is required unless a live customer workload is deliberately run.

## Boundaries

This PR does not replace the existing worker loop, add SQS/EventBridge, call a paid model API, or change authorization/execution policy.

## Follow-up work

Wire the queue into the worker, add an actual model provider behind customer data controls, and add evidence-backed planning in separate PRs.
