# test87: Immutable GitHub OIDC trust and plan retry

Date: 2026-10-18

Execution type: Real AWS prerequisite bootstrap, GitHub environment configuration, failed-closed
OIDC attempt, and pending plan-only retry.

Customer repository: AgentConstruct repository and local deterministic fixtures only.

Commit: Branch `fix/immutable-github-oidc-subject`; final commit recorded by PR #87.

AWS account: `654654474502`.

AWS region: `us-east-1`.

## Resources created

PR #86 bootstrap created the two private artifact buckets, two rotating KMS keys and aliases, and
two GitHub OIDC roles. Existing state, lock, and OIDC resources were adopted. No serverless control
plane or customer workload was created.

## Commands executed

```text
terraform apply /tmp/agentconstruct-tfops-bootstrap-main.tfplan
terraform plan -detailed-exitcode
gh workflow run terraform-plan.yml --ref main -f environment=staging
```

The post-merge plan retry is pending.

## Observed result

- Bootstrap apply completed and the post-apply plan reported no changes.
- GitHub environments restrict deployment to `main`; apply requires founder review.
- Initial plan run `39140035466` failed before AWS access because its customized immutable OIDC
  subject did not match the name-only trust policy.
- CloudTrail showed the exact denied subject with owner and repository IDs.
- One clean-room validation cycle passed with 224 tests and all 12 Terraform roots valid.
- The corrective Terraform plan contains only two in-place IAM trust updates, with no additions or
  destroys.

## Teardown

No teardown was appropriate because the prerequisite resources are the intended retained workflow
support layer. Artifact lifecycle policies automatically expire saved plans and old releases.

## Final boundary

No serverless control-plane apply was run. The initial plan attempt did not upload artifacts. The
plan retry and final absence checks remain pending.
