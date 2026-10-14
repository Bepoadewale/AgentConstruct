# ticket51 — Scale-ready platform contracts

PR: [#51 — feat: add scale-ready platform contracts](https://github.com/Bepoadewale/AgentConstruct/pull/51)

Branch: `feature/scale-ready-contracts`

Status: draft.

## Problem / goal

Document and implement the first future-scale boundaries without changing the current local workflow: versioned tenant context, evidence provenance, model requests/responses, typed jobs, provider capabilities, and usage/entitlement events.

## Current repo state

- The product has tenant-scoped SQLAlchemy records, typed plans, a deterministic intent provider, a deterministic AWS planner, and a PostgreSQL-backed worker.
- These concepts are currently implicit or represented by unversioned dictionaries in several service paths.
- The long-term target is millions of customer identities and much lower execution coupling to the API process.

## Research / references used

- `docs/strategy/10-scale-and-multi-tenancy.md`
- `docs/strategy/05-proposed-architecture.md`
- AWS SaaS Lens: https://docs.aws.amazon.com/wellarchitected/latest/saas-lens/saas-lens.html
- Pulumi Cloud concepts: https://www.pulumi.com/docs/iac/concepts/pulumi-cloud/
- HCP Terraform agents: https://developer.hashicorp.com/terraform/cloud-docs/agents

## Work planned for the PR

- Add versioned Pydantic contracts for tenant scope, evidence, model calls, jobs, capabilities, costs and usage.
- Add contract tests for tenant scope, digest/provenance requirements, job idempotency metadata and usage events.
- Add documentation for the contract boundary and local-to-hosted evolution.
- Preserve existing behavior; no queue transport or model provider replacement in this PR.

## Acceptance criteria

- [x] Contracts are typed, versioned and importable by API, worker and future adapters.
- [x] Tenant scope is explicit and cannot be omitted from platform envelopes.
- [x] Evidence includes provenance and capture time.
- [x] Model calls include provider/model/prompt version and usage metadata without secrets.
- [x] Jobs include idempotency, retry, timeout and tenant scope metadata.
- [x] Capability and cost contracts are provider-neutral and AWS-compatible.
- [x] Usage events support future quotas and billing without implementing billing now.
- [x] Existing tests and local workflow remain unchanged.

## Acceptance status

Met for the additive contract layer. Queue transport, model provider, evidence ingestion and execution isolation remain follow-up PRs.

## Tests / validation performed

Validation performed:

```bash
make lint
make test
python3 scripts/check_doc_conventions.py
git diff --check
```

Results: lint passed; 128 tests passed; documentation conventions passed; diff check passed.

## Evidence files produced

No customer workload or AWS execution is planned for this PR. No `docs/test/test51.md` is required unless a live customer workload is deliberately run.

## Boundaries

This PR does not add a model provider, change authorization, execute Terraform, provision AWS resources, or introduce Kafka/Kubernetes/multi-region infrastructure.

## Follow-up work

Add queue adapters, model gateway implementations, evidence-backed planning, execution-runner isolation, usage metering, and cell-aware routing in separate PRs.
