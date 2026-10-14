# Implementation roadmap

Effort is expressed as relative solo-team sizing, not a promise of calendar delivery.

## Phase 0 — Review and product contract (small)

- Adopt this decision memo and freeze the supported workload envelope.
- Correct stale docs that overstate hosted production readiness.
- Add a benchmark format and evidence taxonomy.

**Exit:** product claims, MVP boundaries and test conventions agree.

## Phase 1 — Evidence-backed planning (medium)

- Expand repository analyzer to build/runtime/port/secret/persistence/deployment evidence.
- Add read-only AWS inventory normalization and provider/account scope.
- Add current pricing/catalog snapshots with timestamps and source.
- Add region/service quota and availability checks where supported.

**Exit:** a plan can explain what it knows, inferred, cannot know, and when evidence was captured.

## Phase 2 — Model-backed intent (medium)

- Implement a commercial/open-weight provider adapter behind `IntentProvider`.
- Constrain model output to typed schemas and clarification questions.
- Add prompt-injection fixtures and provider failure handling.

**Exit:** model improves extraction without gaining execution authority; deterministic fixture remains available.

## Phase 3 — Benchmark and recommendation quality (medium)

- Add the scenario suite in `07-evaluation-and-security.md`.
- Store expert reference decisions and regression reports.
- Measure correctness, uncertainty, cost error, simplicity and stability.

**Exit:** every planner change has measurable quality impact.

## Phase 4 — Hosted product hardening (large)

- Apply and operate RDS-backed persistence only after a reviewed migration plan.
- Configure a real OIDC provider, session lifecycle and workspace invites.
- Add retention, backup/restore and operational alerts.

**Exit:** external customer data can be hosted without relying on fixture identity or ephemeral SQLite.

## Phase 5 — One real execution profile (large)

- Run authenticated Terraform plan-only for App Runner.
- Add product-driven apply behind explicit operator and account guards.
- Capture outputs/resources, independently observe readiness, run destroy and verify absence.

**Exit:** one real workload profile has complete evidence, not only a script-level pilot.

## Phase 6 — Day-2 evidence (large)

- Connect App Runner metrics and Cost Explorer evidence.
- Generate bounded recommendations with cost delta and rollback.
- Require the same immutable plan and approval loop.

**Exit:** optimization is evidence-backed and not autonomous guesswork.

## Main risks

- Scope expands faster than evidence quality.
- AWS pricing/service churn makes fixture assumptions stale.
- A model-backed UX creates confidence without correctness.
- Hosted identity/persistence is delayed while cloud execution receives attention.
- Customers may compare the product to free/embedded AWS assistants and coding agents.

