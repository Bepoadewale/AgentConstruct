# Planner evaluation and regression benchmark

`davdeploy.evaluation` provides a deterministic benchmark for architecture decisions.
It currently includes two deliberately different cases:

- a tiny stateless API, which must not select EKS/Kubernetes;
- a GPU, multi-service inference workload, which must select EKS with a GPU node group.

The benchmark checks coarse safety properties and profile direction. It does not claim
that a fixture price is a real AWS bill or that two cases are a complete quality measure.
Future scenarios should add expert-reviewed requirements, region/capacity evidence,
security checks, Terraform validation, cost-error ranges and observed outcomes.

For the millions-customer goal, this gives us a reproducible regression gate before
changing the planner, provider catalog or model gateway. The benchmark is intentionally
small and local now; a hosted evaluation service can run the same scenario contracts later.
