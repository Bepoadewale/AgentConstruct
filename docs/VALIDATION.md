# Validation

## Local V1 evidence template

Record only commands actually executed.

| Field | Result |
| --- | --- |
| Date / commit | 2026-10-08, working tree before first implementation PR |
| Environment | macOS, Docker Desktop, Python 3.12 |
| Starting state | Project-specific containers, volume and `.local` data were absent before each cycle |
| Commands | Cycle 1: `make bootstrap-local`, `make smoke`, `make demo`, `make demo-failure`, `make verify`, `make opa-test`, `make clean-local`. Cycle 2: `make install`, `docker compose up -d --no-build`, then the same smoke/demo/verify/policy/cleanup commands. |
| Success demo | Intent → plan → approval → observed READY → audit → governed destroy |
| Failure demo | Over-budget request is denied by policy before execution |
| Cleanup | `make clean-local` removes only AgentConstruct Compose resources and `.local` data |
| Second run | Passed. The second run used already-built local images; image rebuilding is part of `make bootstrap-local` and was also exercised earlier in this validation session. |

### Results

- Both smoke checks found API, fixture executor, Prometheus, Grafana and OPA ready.
- Both success demos created staging and production fixture environments, observed two READY results, performed protected production approval, destroyed the production environment, and recorded audit events.
- Both failure demos were denied by policy before execution.
- `ruff`: passed; `pytest`: **7 passed**; `opa test`: **3 passed**; Compose configuration validation passed.
- Both cleanups removed the AgentConstruct Compose network, project volume, containers and `.local` state. No broad Docker cleanup command was used.

No AWS, customer GitHub, or enterprise identity execution is claimed in this document.
