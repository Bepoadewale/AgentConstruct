# Current State Audit

Audit date: 2026-10-11. Branch reviewed: `main` at `865689b` before this change.

## What works today

- A local FastAPI, PostgreSQL, OPA, worker, Prometheus, Grafana and Tempo stack runs with Docker Compose.
- Signed local fixture users are tenant-bound. A JWT/JWKS verifier interface exists but is not connected to a real identity provider.
- The planner turns a request into typed AWS-oriented candidates, cost ranges, complexity scores and a selected recommendation. It does not default to EKS.
- The product stores projects, intents, cloud connections, plans, approvals, audit events and local execution results.
- A GitHub App has read repository metadata through a short-lived installation token. The live adapter refuses writes.
- A customer AWS discovery role has been proven with short-lived STS access. It is read-only and has not deployed a workload.

## What is simulated or partial

- Natural-language understanding, pricing and normal inventory are deterministic fixtures.
- Browser login is a local signed fixture; it is not customer sign-in.
- The current browser is one local demonstration page, not separate developer and administrator dashboards.
- The existing `DeploymentPlan` approval flow governs bounded local execution. It requires a distinct operator and has no customer-facing submitted/rejected revision lifecycle.
- The browser currently shows alternatives. The requested product flow must show one selected AWS plan.
- Prometheus and Grafana run locally, but are not yet mandatory typed resources in every customer plan.

## Missing for the developer and administrator journey

1. Customer-facing infrastructure plan/revision records with `DRAFT`, `SUBMITTED`, `APPROVED` and `REJECTED` states.
2. Administrator review, rejection reasons, decision history and explicit administrator self-approval.
3. Role-aware dashboards and real two-user local demonstration.
4. GitHub App installation/account/repository/branch selection and disconnect flows.
5. AWS account capability/region views and connected-account selection.
6. One-plan customer review with mandatory Prometheus/Grafana details and costs.
7. Browser/API end-to-end evidence for submission, approval, rejection, revision, persistence and decision races.

## Reuse plan

Reuse the existing organisation checks, signed principal boundary, OPA client, canonical SHA-256 hashing, audit event store, PostgreSQL Compose service, GitHub read-only adapter, AWS STS discovery adapter and planner. Do not reuse the legacy execution-plan self-approval prohibition for customer plan decisions.

## Risks and shortest credible path

Real GitHub installation and real AWS roles need customer-controlled external setup. Local fixtures will prove the user journey without creating cloud resources. The shortest path is: persist customer plan revisions first, then role-aware dashboards, integrations, one-plan review, submission/decision UI and end-to-end proof. Approval remains separate from deployment throughout.
