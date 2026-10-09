# Architecture Planner

The planner turns a typed workload request into an explainable AWS architecture recommendation. It is a deterministic, small decision catalogue—not a model that can invent arbitrary cloud resources.

```text
natural-language request
  → typed WorkloadSpec
  → approved cloud inventory fixture
  → architecture candidates
  → hard-constraint checks
  → cost + complexity comparison
  → selected ArchitecturePlan
  → policy, immutable plan, approval, bounded execution
```

## Decision order

1. Reject a request missing peak traffic or a monthly budget.
2. Check the requested region against approved regions.
3. Generate AWS candidates from lower to higher operational complexity.
4. Reject options that cannot meet GPU, Kubernetes, runtime, availability, privacy, model-control, or budget requirements.
5. Reuse an approved suitable service before proposing a duplicate.
6. Find the lowest estimated cost among viable candidates.
7. Consider candidates within the configured 10% cheapest viable band equivalent on cost.
8. Choose the lowest-complexity candidate in that band.
9. Store the selected option, rejected options, risks, cost assumptions, and upgrade triggers in the immutable plan payload.

EKS is selected only for explicit Kubernetes needs. A small FastAPI application therefore selects App Runner or ECS Fargate before EKS. A GPU requirement selects an accelerator profile only when the budget permits it; an explicit multi-service GPU/Kubernetes requirement selects the specialised EKS profile instead.

## Boundaries

The local planner uses fixture price ranges and a local inventory adapter. It does not call AWS, apply Terraform, or promise that the estimate will match a customer bill. Live discovery and pricing remain separate provider-adapter work.
