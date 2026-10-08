# Backlog

## Three-PR delivery plan

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

## P1 — Customer-cloud execution

- [ ] AWS STS/OIDC role-assumption adapter with least privilege.
- [ ] GitHub App installation, repository discovery and scoped desired-state publication.
- [ ] Real GitOps/Argo observer and customer-cloud workload agent.
- [ ] Enterprise OIDC/JWKS adapter and organisation lifecycle.

## P1 — First cloud pilot prerequisites

- [ ] Replace the local fixture issuer with a real trusted OIDC issuer and test the existing JWKS adapter.
- [ ] Configure and test the planned GitHub App desired-state publisher and Argo observer.
- [ ] Configure and test the planned AWS Load Balancer Controller, External Secrets Operator and exact browser redirect/CORS origins.
- [ ] Run an explicitly authorised AWS create → validate → destroy pilot, including the failure, recovery, load and cost-evidence drills.

## P2 — Product depth

- [ ] Live pricing catalogue provider and actual billing evidence.
- [ ] Model release, inference controls and AI telemetry as separately approved slices.
- [ ] Commercial packaging, billing and support workflows after market validation.
