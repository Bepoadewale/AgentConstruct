# Current State Audit

Audit date: 2026-10-13. Branch reviewed: `main` after the local V1 hardening and administrator-gated readiness work.

## What works today

- A local FastAPI, PostgreSQL, OPA, worker, Prometheus, Grafana and Tempo stack runs with Docker Compose.
- Signed local fixture users are tenant-bound. A JWT/JWKS verifier interface exists but is not connected to a real identity provider.
- The planner turns a request into typed AWS-oriented candidates, cost ranges, complexity scores and a selected recommendation. It does not default to EKS.
- The product stores projects, intents, cloud connections, plans, approvals, audit events and local execution results.
- A GitHub App has read repository metadata through a short-lived installation token. The live adapter refuses writes.
- A customer AWS discovery role has been proven with short-lived STS access. It is read-only and has not deployed a workload.
- The AgentConstruct API is deployed to AWS App Runner for hosted read-only customer-account connection verification. The static UI is maintained separately in `agentconstruct-frontend`. The hosted API uses a separate runtime IAM role and Secrets Manager-backed ExternalId storage, but still uses fixture sign-in/policy and ephemeral SQLite.
- The customer-facing plan flow supports draft, submitted, approved and rejected revisions; administrator rejection reasons; administrator self-approval; editable draft/rejected constraints; review diffs; and a clear approved-not-deployed boundary.
- The local UI has separate developer and administrator fixture sessions, role-aware dashboards, integration selectors, one-plan review, approval queues, audit evidence, local dry-run execution, governed destroy, fixture desired-state PR state, App Runner Terraform contract preview, cloud-readiness preflight and plan-only review records.
- Every customer AWS plan includes mandatory Prometheus-compatible metrics and Amazon Managed Grafana review components with cost assumptions and coverage limitations.

## What is simulated or partial

- Natural-language understanding, pricing and normal inventory are deterministic fixtures.
- Browser login is a local signed fixture; it is not customer sign-in.
- Fixture desired-state PR/check state does not write GitHub, publish checks, or merge code.
- App Runner Terraform rendering and plan-only review records are local governance evidence; they do not run authenticated Terraform or create AWS resources.
- Cloud-readiness preflight is administrator-only local guardrail evidence. The hosted runtime identity is proven for read-only discovery only; it does not prove live reviewed PR/checks, Terraform workload plan/apply, GitOps sync or workload readiness.

## Missing for the developer and administrator journey

1. Enterprise/customer identity is not connected; local login remains a signed fixture.
2. Live GitHub public OAuth/install callback and public webhook delivery are not executed; fixture webhooks and read-only installation-token discovery are implemented.
3. Live GitHub desired-state PR writes/checks are not enabled; publication remains fixture-only.
4. The public CloudFormation template host and hosted App Runner runtime are deployed and verified for read-only customer-account discovery. Production identity, production policy and durable hosted persistence are still missing.
5. Authenticated Terraform plan-only review has not been executed; apply remains out of scope until separately authorized.
6. Real workload monitoring, actual AWS cost evidence for deployed workloads, GitOps/Argo reconciliation and customer-cloud destroy evidence are not implemented.

## Reuse plan

Reuse the existing organisation checks, signed principal boundary, OPA client, canonical SHA-256 hashing, audit event store, PostgreSQL Compose service, GitHub read-only adapter, AWS STS discovery adapter and planner. Do not reuse the legacy execution-plan self-approval prohibition for customer plan decisions.

## Risks and shortest credible path

Real GitHub writes and real AWS workload execution need customer-controlled external setup plus hosted-runtime hardening. The local product is stable enough to demonstrate the intended plan/review/approval/dry-run lifecycle without cloud spend, and the hosted App Runner runtime can verify read-only customer discovery. The shortest next path is production identity/policy/persistence hardening, then authenticated Terraform plan-only mode for the App Runner contract, then a separately authorized create → validate → destroy cloud pilot. Approval remains separate from deployment throughout.
