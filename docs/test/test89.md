# test89: Single production control-plane contract

Date: 2026-10-18

Execution type: Local clean-room validation, static workflow tests, and authenticated AWS
plan-only review. No AWS apply was run.

Customer repository: AgentConstruct repository and local deterministic fixtures only; no customer
repository or workload.

Commit: Implementation commit `eb199b4` on branch `feat/single-production-control-plane`.

AWS account: `654654474502`.

AWS region: `us-east-1`.

## Resources created

The clean-room cycle created ephemeral local Docker containers, a network, a PostgreSQL volume,
and a Python virtual environment. Final cleanup removed them.

No AWS resource was created or modified. The authenticated plan used the existing state bucket,
lock table, immutable Lambda release object, and local IAM profile. The fixed production state
object did not exist before or after the plan.

## Commands executed

```text
make clean-local
make bootstrap-local
make smoke
make demo-simple
make demo-complex
make demo-degraded
make demo-day2
make demo-failure
make demo-readiness-failure
make trace-check
make verify
make terraform-validate
make clean-local
terraform init -reconfigure with serverless-control-plane/terraform.tfstate
terraform plan with production inputs and an immutable release version
aws s3api list-objects-v2
aws lambda list-functions
aws rds describe-db-clusters
aws cognito-idp list-user-pools
aws apigatewayv2 get-apis
```

## Observed result

- The plan workflow no longer presents an environment selector.
- Both workflows use `serverless-control-plane/terraform.tfstate`.
- Terraform uses the canonical `agentconstruct` namespace and the fixed `production` tag.
- Saved-plan manifest version 2 identifies the deployment as `production`.
- Apply rejects older manifests, including the historical staging plan.
- The complete clean-room sequence passed.
- `make verify` passed 226 tests with one upstream dependency deprecation warning.
- All Terraform roots passed initialization without backends and static validation.
- The authenticated production plan reported 39 additions, no changes, and no destroys.
- The fixed production state object was absent after planning.
- No AgentConstruct Lambda function, Aurora cluster, Cognito pool, or API Gateway API exists.

## Teardown

`make clean-local` removed the local containers, network, volume, `.venv`, and `.local`. No cloud
teardown was required because Terraform apply was not run.

## Final boundary

This evidence proves the single-production workflow contract, local product correctness, static
Terraform validity, and an authenticated plan-only review. It does not prove a deployed control
plane, live authentication, migrations, customer traffic, or customer workload execution.
