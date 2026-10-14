# Model strategy

## Recommendation

Do not train a foundation model. Start with an existing commercial or open-weight model behind the existing provider interface, combined with repository evidence, live AWS read-only tools, structured output validation, deterministic planner/policy code, and an expert-reviewed evaluation suite. Consider fine-tuning a small model only after repeated production traces show a stable, legally usable task distribution and a measured quality/cost benefit.

## Options

| Approach | Feasibility | Data/licensing | Reliability/economics | Decision |
|---|---|---|---|---|
| Train foundation model | Extremely expensive and slow for a small team; requires broad code/cloud corpora and model infrastructure | Requires licensed data, filtering, provenance and safety work | No reason to expect better AWS architecture decisions than a tool-grounded model; high inference/training burden | Reject |
| Fine-tune open-weight model | Technically feasible later; requires curated examples and evaluation | Need rights to prompts, repository-derived data, incident data and human labels; customer data must be opt-in and isolated | Can reduce latency/cost for extraction/classification, but may encode stale service assumptions | Defer; test on narrow tasks first |
| Commercial model + tools/RAG | Fastest path; matches existing `IntentProvider` seam | Provider terms, retention, regional processing and customer-data controls must be reviewed | Strong reasoning plus current tools; variable API cost and provider dependency | Use for first model-backed release |
| Hybrid | Use a strong model for ambiguous interpretation and small deterministic/specialized models for classification/routing | Same consent/provenance requirements for training traces | Best long-term cost/latency path if benchmark evidence supports it | Target architecture |

## Proprietary data worth collecting legally

- User requirements and clarification outcomes, with explicit consent.
- Repository metadata/manifests, not source contents by default; source use must be scoped and opt-in.
- Approved/rejected plan revisions and rejection reasons.
- Expert labels for service suitability, cost assumptions, security findings, and operational complexity.
- Observed plan outcomes, failures, rollback and destroy evidence from customer accounts, under contract.
- Anonymized telemetry and billing deltas only where customers opt in.

Do not train on private repositories, secrets, raw logs, customer identifiers, or cloud data by default. Build a deletion, retention, tenant isolation, provenance and licensing policy before any fine-tuning.

## Model boundary

The model may extract requirements, summarize repository evidence, ask clarification questions, explain trade-offs, and propose candidate preferences. Deterministic code must validate schemas, capabilities, pricing timestamps, region/quotas, IAM, policy, hashes, approvals, execution commands, and observed state. The model must never be an authority for privileged mutation.

