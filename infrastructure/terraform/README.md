# Terraform cloud-pilot contract

**State: statically validated design. Nothing here has been applied to AWS.**

`bootstrap/` describes a separate encrypted/versioned state bucket, DynamoDB lock and budget guardrail. `customer-connection/` describes customer-account IAM roles only: a discovery role and an empty future-execution role. `pilot/` describes the private VPC, EKS, ECR, RDS, Secrets Manager and workload-identity foundation. Every resource uses project tags.

The bootstrap root requires a state-bucket name, AWS region, monthly budget and budget-notification email as values supplied outside Git. Do not commit a real `.tfvars` file.

Run static checks only:

```bash
make terraform-validate
```

See [the customer AWS connection](customer-connection/README.md) before using its authenticated plan command. It must be reviewed before its separately confirmation-gated apply.

A future cloud operator supplies account-specific values outside Git, reviews an authenticated plan and uses Terraform for both creation and teardown. The product API never runs Terraform.
