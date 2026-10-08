# V1 Architecture

AgentConstruct begins as one modular product API, not a fleet of microservices.

```text
Browser UI
   │ natural-language goal
   ▼
FastAPI product API ──► Intent fixture ──► typed WorkloadSpec
   │                                      │
   │                                      ▼
   │                              AWS V1 planner + cost catalogue
   │                                      │
   ▼                                      ▼
PostgreSQL ◄── audit / plans / approvals ◄── OPA policy
   │
   ▼
bounded fixture executor ──► observed READY / FAILED / DESTROYED

Prometheus scrapes the API; Grafana reads Prometheus.
```

The product boundary is deliberate: natural language can propose a typed specification, but it cannot call a shell, Terraform, Kubernetes or cloud APIs. A future AWS adapter will assume a customer-scoped role using short-lived credentials after policy and approval.

The local cloud connection record stores only tenant-scoped connection metadata and the intended `byoc_role_contract` mode. It stores no access key or cloud credential.

See [security](../security/security-model.md) and [product vision](../product/vision.md).
