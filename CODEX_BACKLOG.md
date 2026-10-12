# Backlog

## Three-PR delivery plan

### Developer and administrator workflow

- [x] Audit the current product and add the separate immutable customer-plan revision foundation.
- [x] Add role-aware local sign-in, tenant-scoped workspace dashboards and browser navigation.
- [x] Add GitHub installation/repository/branch and AWS connected-account selection experiences.
- [x] Add GitHub repository intelligence for safe manifest analysis, persisted runtime/framework/data/deployment hints, and planner/review binding.
- [x] Render one AWS plan with required Prometheus/Grafana details and cost estimate.
- [x] Add editable draft/rejected plan constraints, assumption decisions and revision diffs before approval submission.
- [x] Add submit, administrator approval/rejection, self-approval and revision UI/API flows.
- [x] Add administrator queue filters, richer review evidence, approved-not-deployed banners and export-ready audit evidence.
- [x] Add explicit approved-plan local dry-run execution, observed health/cost state, readiness-failure evidence and governed local destroy.
- [x] Add realistic local demo seeding and expanded product E2E coverage for approve/reject/self-approve/dry-run/destroy/persistence.
- [x] Prove the two-session developer/admin journey with browser controls, deterministic API E2E, restart persistence and security-boundary checks.

### Completed hardening — local commercial V1

- [x] Add provider-agnostic intent adapter, deterministic fixture, material-question handling, richer typed inputs, and source provenance.
- [x] Add repository/cloud connection records and local fixtures.
- [x] Add stale-plan/replay/idempotency/restart-recovery, prompt-injection and readiness-failure coverage.
- [x] Complete visible UI constraints, environment health, governed destroy and audit views.
- [x] Add durable worker jobs, local OTel/Tempo business spans and outcome metrics.
- [x] Add Compose-backed API/UI contract CI and repeat clean project-runtime bootstrap, success, failure, trace and cleanup evidence twice.

### PR 2 — Cloud-pilot architecture and safe runtime contracts

- [x] Add cloud topology, Terraform foundation, private EKS runtime contracts, IRSA, secrets, GitOps, observability and recovery designs. No apply.

### PR 3 — Cloud-pilot operator workflow and final evidence

- [x] Add GitHub OIDC plan/apply/destroy workflows, cloud operator commands, static contract CI and final plain-English evidence review. No apply.

## Existing product roadmap

### Completed foundation

- [x] Rename product internally to AgentConstruct.
- [x] Build typed intent, architecture, cost, policy, plan, approval, audit and bounded execution paths.
- [x] Build the local UI and Docker Compose stack.
- [x] Record two local validation cycles; repeat fully cold bootstrap in PR 1.
- [x] Expose the governed product API through a thin CLI and a stdio MCP server without granting agents approval, cloud, shell, Terraform, Kubernetes or secret authority.
- [x] Demonstrate a bounded Day-2 loop: evidence, recommendation, exact change plan, independent approval, observed local change and audit.
- [x] Show the customer why an architecture was selected and prove both simple non-EKS and complex specialised-EKS local scenarios.
- [x] Persist local incident and recommendation evidence for degraded health and governed Day-2 changes.

## P1 — Customer-cloud execution

- [x] Create the AgentConstruct control-plane GitHub OIDC identity and a real customer discovery connection. Terraform applied only state/lock and IAM resources; STS, inventory and Cost Explorer were verified without a workload.
- [ ] Dispatch the hosted GitHub OIDC workflow to prove the production trust route, then keep all deployment permissions profile-specific and separately approved.
- [ ] Implement the live AWS STS role-assumption adapter with least privilege after the discovery-role pilot.
- [x] GitHub App installation/repository/branch discovery and safe manifest intelligence.
- [x] Local GitHub webhook receiver contract with signature verification, delivery dedupe, replay protection, persisted installation states and UI visibility.
- [ ] Scoped GitHub desired-state publication through reviewed pull requests.
- [ ] Real GitOps/Argo observer and customer-cloud workload agent.
- [ ] Enterprise OIDC/JWKS adapter and organisation lifecycle.
- [ ] Replace the fixture inventory and pricing catalogue with customer-approved AWS discovery and timestamped pricing sources.
- [ ] Replace deterministic Day-2 telemetry and the fixed change endpoint with tenant-authorised telemetry, policy-bounded execution and independently observed customer-cloud changes.
- [ ] Render Terraform only for the selected architecture family; do not send every plan to the EKS reference stack.

## P1 — First cloud pilot prerequisites

- [ ] Replace the local fixture issuer with a real trusted OIDC issuer and test the existing JWKS adapter.
- [ ] Configure and test the planned GitHub App desired-state publisher and Argo observer.
- [ ] Configure and test the planned AWS Load Balancer Controller, External Secrets Operator and exact browser redirect/CORS origins.
- [ ] Run an explicitly authorised AWS create → validate → destroy pilot, including the failure, recovery, load and cost-evidence drills.

## P2 — Product depth

- [ ] Live pricing catalogue provider and actual billing evidence.
- [ ] Model release, inference controls and AI telemetry as separately approved slices.
- [ ] Commercial packaging, billing and support workflows after market validation.
