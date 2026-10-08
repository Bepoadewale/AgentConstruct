# Cloud reliability contract

**State: planned pilot drills. They have not run in AWS.**

## What will be monitored

- API request, plan-policy and execution-result metrics.
- OpenTelemetry traces from intent through observation.
- Workload readiness, restart count and reconciliation failure.
- Audit records retained with plan hash, actor, approval and result.

Prometheus, OpenTelemetry Collector, Tempo and Grafana remain private. Future alert rules must page only on actionable conditions: unavailable API replicas, failed reconciliations, failed deployment readiness and budget guardrail breach.

## Planned drills

| Drill | Expected result |
| --- | --- |
| Bad image or failed readiness | Workload becomes `FAILED`; it is never reported ready |
| Restore known-good desired state | Reviewed GitOps revert is reconciled and observed |
| Delete one API Pod | The second replica continues serving; Kubernetes restores the missing Pod |
| Bounded load | Fixed-duration, capped requests measure availability and latency without claiming a benchmark |
| Cost query | Cost Explorer is queried after 24–48 hours because AWS billing can be delayed |

The pilot runbook must record actual thresholds, alert evidence, duration, results and cost. These are not measured values today.
