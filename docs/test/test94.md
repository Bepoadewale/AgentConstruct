# test94

Date: 2026-10-19
Execution type: Real AWS failed-apply diagnosis, remote-state inspection, and local/static
reconciliation validation
Customer repository: No customer workload repository; DavDeploy production control plane only
Commit: PR #94 review branch
AWS account: `654654474502`
AWS region: `us-east-1`

## Resources created

Apply run `39269651252` created 25 managed resources before stopping. Terraform recorded them in
the production remote state. They include the database VPC and subnets, Cognito user pool/client and
domain, budget, SQS queues and policy, EventBridge schedule, runtime IAM roles and policies, and the
policy and Cognito-link Lambda functions.

The run did not create Aurora, its instance, API Gateway, the API/migration/worker Lambda functions,
or their dependent integrations.

## Commands executed

```text
gh run view 39269651252 --repo Bepoadewale/davdeploy --log-failed
aws rds describe-db-engine-versions --engine aurora-postgresql
aws rds describe-orderable-db-instance-options \
  --engine aurora-postgresql --db-instance-class db.serverless
terraform state list against the production serverless-control-plane state
.venv/bin/python -m pytest -q \
  tests/test_terraform_operations_bootstrap.py tests/test_serverless_runtime.py
make terraform-validate
make verify
terraform plan against the production remote state with the reviewed PR changes
```

## Observed result

- The apply failed because Aurora PostgreSQL `16.6` was unavailable in `us-east-1` and the apply
  role lacked permission for API Gateway's separate tag endpoint.
- Live AWS discovery confirmed `16.15` is available and orderable for `db.serverless`.
- The remote state contains every resource that completed before the failure.
- The focused regression suite passed 15 tests.
- Every Terraform root validated.
- Ruff passed, 227 Pytest tests passed, the OpenAPI snapshot matched, and Compose configuration
  validated.
- The real reconciliation plan refreshed all 25 completed resources and proposed 14 additions, zero
  changes, and zero deletions.

## Teardown

No teardown or manual state change was performed. Successful resources remain managed by the
production Terraform state so a fresh plan can reconcile them safely.

## Final boundary

This proves the failure diagnosis, current AWS engine availability, permission correction, state
integrity, and static reconciliation configuration. A successful post-merge plan and apply are still
required before the control plane is operational.
