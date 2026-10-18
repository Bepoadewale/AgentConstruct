# Portfolio-to-flagship architecture

> **Historical strategy note.** Superseded on 2026-10-08. davdeploy is now the private commercial flagship; public repositories remain independent references.

The public portfolio projects are independent reference implementations. The flagship will consume validated concepts, not blindly merge ten codebases.

| Public project | Flagship contribution |
| --- | --- |
| ai-platform-control-plane | identity, policy, approvals, reconciliation, audit |
| ai-developer-platform | self-service and golden paths |
| multi-tenant-ai-inference-platform | gateway, quotas, routing, metering |
| secure-agent-runtime | bounded agent execution and capabilities |
| model-deployment-control-plane | evaluation, release gates, canary, rollback |
| ai-observability-finops-platform | traces, metrics, cost, SLO evidence |
| ai-infrastructure-auto-remediation-agent | guarded remediation and verification |
| gpu-scheduler-lab | capacity and workload-scheduling patterns |
| secure-mcp-infrastructure-gateway | governed tool access and delegated authority |
| hybrid-ai-edge-platform | fleet model operations and local/cloud routing |

## Long-term conceptual flow

```text
Users, applications, and agents
  -> authenticated multi-tenant gateway
  -> policy, quota, routing, and control plane
  -> model release / serving / compute layers
  -> observability, cost, audit, and bounded remediation
  -> optional edge fleet extension
```

## Integration principles

- Start with one end-to-end vertical slice.
- Prefer stable API/event contracts over shared internal libraries.
- Keep customer data and production configuration isolated.
- Treat every expansion as a separately validated product decision.
