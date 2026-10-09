# Agent Guide

## Mission

Build and maintain **AgentConstruct**, the private commercial product. Use plain English first. Explain technical terms when they matter to a customer, operator or reviewer.

## Product rules

- AI proposes; typed validation, policy and approved deterministic systems authorize and execute.
- Start every recommendation with the cheapest, simplest option that meets hard requirements. EKS, GPUs, containers and multi-cloud are never defaults.
- Mark fixture inventory and fixture pricing as simulated. Never call an estimate an AWS bill.
- Never give an LLM, customer browser, developer, or agent unrestricted shell, Terraform, Kubernetes, cloud-admin or secret access.
- Keep customer workloads, cloud accounts and data in the customer cloud where possible.
- Preserve public repositories as technical evidence; do not copy private strategy, pricing, buyer research or proprietary ranking logic into them.
- Never commit secrets, private keys, customer data or long-lived cloud credentials.
- Every privileged change needs an attributable actor, immutable plan hash, policy result and audit event.
- Claims must say whether they are executed locally, simulated, planned or roadmap-only.

## Development rules

- Prefer a modular monolith until a real execution need justifies more services.
- Use deterministic fixtures when credentials are unavailable. Label them clearly.
- Keep interfaces provider-neutral, but implement AWS first.
- Use bounded readiness checks, useful failures and project-scoped cleanup.
- Do not push directly to `main`; use a focused branch and reviewable PR.

## Clean-room gate

Before calling a runnable change review-ready, execute and record:

```text
clean → bootstrap → smoke → simple demo → complex demo → degraded/Day-2 demos → policy failure → readiness failure → trace check → verify → clean
→ second bootstrap → second smoke → second simple, complex, degraded and Day-2 demos → second policy and readiness failures → trace check → verify → clean
```

Do not infer reproducibility from an existing environment.
