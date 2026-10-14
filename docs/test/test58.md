# test58 — Read-only AWS account and local scale smoke

Date: 2026-10-14

PR: [#58 — local load smoke and read-only AWS evidence](https://github.com/Bepoadewale/AgentConstruct/pull/58)

Execution type: local bounded load smoke plus authenticated read-only AWS inventory and Cost Explorer query.

Customer repository: `Bepoadewale/AgentConstruct` (control-plane repository; no customer workload deployed).

Commit: `982191f`

AWS account: `654654474502`

AWS region: `us-east-1` and read-only regional check in `eu-west-1`.

## Resources created

None. No Terraform apply, CloudFormation apply, workload deployment, or resource mutation occurred.

## Commands executed

```bash
make local-load-smoke
AWS_PROFILE=ai-platform-pilot-key AWS_REGION=us-east-1 aws sts get-caller-identity
AWS_PROFILE=ai-platform-pilot-key AWS_REGION=us-east-1 aws ce get-cost-and-usage \
  --time-period Start=2026-10-01,End=2026-10-15 \
  --granularity MONTHLY --metrics UnblendedCost --group-by Type=DIMENSION,Key=SERVICE
AWS_PROFILE=ai-platform-pilot-key AWS_REGION=eu-west-1 aws apprunner list-services
AWS_PROFILE=ai-platform-pilot-key AWS_REGION=eu-west-1 aws rds describe-db-instances
AWS_PROFILE=ai-platform-pilot-key AWS_REGION=eu-west-1 aws eks list-clusters
```

## Observed result

- Account identity was `654654474502`.
- `us-east-1` had no active App Runner service, RDS instance, EKS cluster or AgentConstruct-tagged VPC/EC2 instance.
- `eu-west-1` had no App Runner service, RDS instance, EKS cluster, ECR repository or AgentConstruct-tagged VPC/EC2 instance.
- October 1–15 Cost Explorer unblended spend returned approximately `$11.35`, including `$0.79` tax; billing data can lag and is not attributed entirely to AgentConstruct.
- AgentConstruct foundation support resources remain in `us-east-1` (state bucket, lock table and IAM roles).

## Teardown

Not applicable. No resources were created.

## Final boundary

The load result is a local smoke signal, not a production capacity claim. AWS evidence is read-only and does not prove hosted runtime, customer workload execution or production observability.
