# GitOps delivery contract

**State: planned cloud contract. No GitHub App, pull request or Argo deployment has been executed.**

The product API owns intent, policy, approvals and audit. It does not run `kubectl`, Helm or Terraform against a customer cluster.

When a protected plan is approved, the future GitOps worker will:

1. Read the immutable plan and exact approved hash.
2. Render a limited desired-state overlay with the approved ECR digest, secret references and tenant namespace.
3. Use a GitHub App installation token limited to that customer repository.
4. Create a pull request containing only that desired-state change.
5. Wait for repository protection and merge evidence.
6. Let Argo CD reconcile the committed change.
7. Observe Kubernetes readiness independently and store `READY` or `FAILED` with the plan hash.

The GitHub App must use installation-scoped permissions. A customer browser, AI model and normal developer never receive the App private key, AWS role credentials or cluster credentials.

## Delivery format decision

davdeploy uses Kustomize for the initial generated customer overlay. This keeps the first product workflow small and reviewable. Helm is deliberately not added as a second templating layer in V1. A future customer-provided Helm chart adapter may be added only when it has typed values, schema validation and the same plan/approval/audit boundary.
