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

## Customer workload evidence

- Every PR that performs a customer workload test run must have a PR-numbered evidence file under `docs/test/`.
- Use the GitHub PR number as the filename: PR #42 uses `test42.md`, PR #43 uses `test43.md`, and so on.
- If one PR performs multiple customer workload cycles, record all cycles in that one PR-numbered file.
- Do not overwrite, rename, or renumber older test evidence.
- Each file must state whether the run was local, simulated, statically validated, or real AWS execution.
- For real AWS workload runs, record the exact repository, commit, account, region, commands, resources created, observed readiness result, teardown command, absence check, retained resources, and limitations.
- `docs/VALIDATION.md` may summarize multiple runs, but `docs/test/test<PR_NUMBER>.md` is the per-PR customer workload evidence source of truth.

## PR tickets

- Every PR must have a PR-numbered ticket file under `docs/tickets/`.
- Use the GitHub PR number as the filename: PR #42 uses `ticket42.md`, PR #43 uses `ticket43.md`, and so on.
- Create the ticket file before implementation work starts whenever the PR number is already known. If the PR does not exist yet, create the branch, open a draft PR early to get the number, then add the matching ticket before substantive implementation.
- Do not overwrite, rename, or renumber older tickets.
- Each ticket must include the PR goal, current repo state relevant to the PR, research/references, work to be done, acceptance criteria, whether each criterion was met, validation performed, evidence files, boundaries, and follow-up work.
- Keep the ticket updated as implementation changes. Before marking the PR review-ready, update the acceptance status truthfully.

## Clean-room gate

Before calling a runnable change review-ready, execute and record:

```text
clean → bootstrap → smoke → simple demo → complex demo → degraded/Day-2 demos → policy failure → readiness failure → trace check → verify → clean
→ second bootstrap → second smoke → second simple, complex, degraded and Day-2 demos → second policy and readiness failures → trace check → verify → clean
```

Do not infer reproducibility from an existing environment.
