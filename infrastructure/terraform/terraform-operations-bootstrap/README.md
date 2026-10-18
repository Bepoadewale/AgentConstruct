# Terraform operations bootstrap

This root creates only the low-cost prerequisites used by the manually dispatched Terraform plan
and apply workflows:

- encrypted saved-plan and immutable release buckets;
- dedicated KMS keys;
- separate GitHub OIDC roles for planning and applying.

It adopts the existing AgentConstruct state bucket, lock table, and GitHub OIDC provider as data
sources. It does not create or apply the serverless control plane.

Initialize this root against the existing remote backend:

```bash
terraform init -reconfigure \
  -backend-config="bucket=agentconstruct-tfstate-654654474502" \
  -backend-config="key=terraform-operations-bootstrap/terraform.tfstate" \
  -backend-config="region=us-east-1" \
  -backend-config="dynamodb_table=agentconstruct-terraform-locks" \
  -backend-config="encrypt=true"
```

Always review a saved plan before applying this bootstrap. Configure GitHub environments only from
the verified Terraform outputs.
