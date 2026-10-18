# test88: Terraform operations bootstrap and plan evidence

Date: 2026-10-18

Execution type: Real AWS prerequisite bootstrap and manual staging plan only.

Customer repository: AgentConstruct repository and local deterministic fixtures only; no customer
repository or workload.

Commit: `3f4fe983a1b34a91e42967c1057bb723c20bdad9` on `main`; plan run `39140954204`.

AWS account: `654654474502`.

AWS region: `us-east-1`.

## Resources created

The retained workflow prerequisite layer contains:

- Saved-plan bucket `agentconstruct-tfplans-654654474502`.
- Release bucket `agentconstruct-releases-654654474502`.
- Two customer-managed KMS keys and aliases for plan and release encryption.
- GitHub OIDC roles `agentconstruct-terraform-plan-github` and
  `agentconstruct-terraform-apply-github`.
- GitHub environments `terraform-plan` and `terraform-apply`, restricted to `main`; apply requires
  founder review.

The existing state bucket `agentconstruct-tfstate-654654474502`, DynamoDB lock table
`agentconstruct-terraform-locks`, and GitHub Actions OIDC provider were adopted rather than
recreated.

Plan run `39140954204` created only the following operational artifacts:

- Encrypted manifest and saved plan under
  `plans/serverless-control-plane/3f4fe983a1b34a91e42967c1057bb723c20bdad9/39140954204/1/`.
- Versioned release object
  `releases/serverless-control-plane/3f4fe983a1b34a91e42967c1057bb723c20bdad9/agentconstruct-control-plane.zip`
  with version ID `4oYIWZa3uqA_pOADjy7Ka0x7aHAgVUEI`.

## Commands executed

```text
terraform apply /tmp/agentconstruct-tfops-bootstrap-main.tfplan
terraform plan -detailed-exitcode
gh workflow run terraform-plan.yml --ref main -f environment=staging
aws s3api head-object
aws lambda list-functions
aws rds describe-db-clusters
aws cognito-idp list-user-pools
aws apigatewayv2 get-apis
```

## Observed result

- The exact reviewed bootstrap plan applied successfully.
- A follow-up bootstrap plan reported no changes.
- Initial plan run `39140035466` failed closed before AWS access because the immutable GitHub OIDC
  subject did not match the original trust policy.
- PR #87 corrected only the two IAM trust policies. The post-merge correction applied with no
  additions and no destroys, then reported no drift.
- Plan run `39140954204` succeeded and reported 39 additions, no changes, and no destroys.
- The manifest is 289 bytes, the saved plan is 17,424 bytes, and the release package is 44,974,801
  bytes.
- The staging Terraform state object is absent.
- No Lambda functions, Aurora clusters, Cognito user pools, or API Gateway v2 APIs with the
  `agentconstruct-staging` prefix exist.

## Teardown

No teardown was performed because the prerequisite resources are the intended retained workflow
support layer. Bucket lifecycle policies expire saved plans and old release versions automatically.
There was no deployed control plane to tear down.

## Final boundary

This execution stopped after a successful Terraform plan. No apply workflow ran, no serverless
control plane was created, and no customer cloud workload was deployed.
