# Backlog

## Three-PR delivery plan

### PR 1 — Complete the local commercial V1

- [ ] Add provider-agnostic intent adapter, deterministic fixture, material-question handling, richer typed inputs, and source provenance.
- [ ] Add repository/cloud connection records and local fixtures.
- [ ] Add stale-plan/replay/idempotency/restart-recovery and readiness-failure coverage.
- [ ] Complete visible UI constraints, environment health and audit views.
- [ ] Add local OTel/Tempo traces and outcome metrics.
- [ ] Repeat a fully cold `make bootstrap-local` clean-room run twice.

### PR 2 — Cloud-pilot architecture and safe runtime contracts

- [ ] Add AWS icon architecture, Terraform foundation, private EKS runtime contracts, IRSA, secrets, GitOps, observability and recovery designs. No apply.

### PR 3 — Cloud-pilot operator workflow and final evidence

- [ ] Add GitHub OIDC plan/apply/destroy workflows, cloud operator commands, static contract CI and final plain-English evidence review. No apply.

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

## P2 — Product depth

- [ ] Live pricing catalogue provider and actual billing evidence.
- [ ] Model release, inference controls and AI telemetry as separately approved slices.
- [ ] Commercial packaging, billing and support workflows after market validation.
