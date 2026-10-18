# Day-2 operations

**Status: executed locally with deterministic fixtures.** This is not cloud telemetry or autonomous remediation evidence.

davdeploy treats a running environment as something it must explain and improve safely, not merely create.

```text
bounded telemetry evidence → diagnosis → recommendation → immutable change plan
→ policy → independent approval for production → durable worker → observed result → audit
```

The local Day-2 fixture supplies a high-latency snapshot: 2,800 ms p95 latency, 1,200 ms queue time, and 92% utilization with one minimum replica. It recommends increasing the minimum replica count from one to two. The recommendation includes its evidence, assumptions, low risk, rollback path, and a $25–$40/month **estimate**. That range is not actual AWS billing.

The diagnostic is persisted as an open incident and a proposed recommendation. A deliberately degraded fixture environment also opens an incident. For a production environment, the recommendation becomes a protected `CHANGE` plan and the environment enters `CHANGE_PROPOSED`. The requesting founder cannot approve it. A separate operator must approve the exact hash before the existing durable worker can call its fixed local endpoint. The observer records the resulting 1,500 ms p95 fixture outcome, marks the recommendation applied and resolves its incident.

The local executor has no AWS, Kubernetes, Terraform, shell, Docker, or secret authority. A future cloud implementation will replace the fixture telemetry and fixed endpoint with tenant-authorised telemetry, a policy-bounded executor, and independent resource observation.

Run `make demo-day2` for the full governed change loop and `make demo-degraded` to show a durable degraded state and open incident. Both are local fixture evidence only.
