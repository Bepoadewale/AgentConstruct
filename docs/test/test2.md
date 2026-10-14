# test2 — Customer workload App Runner pilot, cycle 2

Date: 2026-10-14

Execution type: real AWS customer workload create → validate → destroy.

Customer repository: `https://github.com/Bepoadewale/ai-platform-control-plane`

Commit: `de60dfe2e24930d76e6be8a5fb2c428e35f483c6`

AWS account: `654654474502`

AWS region: `us-east-1`

Selected runtime profile: AWS App Runner.

Why App Runner: this repeat run verified that the customer workload could be recreated from a clean destroyed pilot state using the same repository and same App Runner profile.

## Resources created

Terraform recreated the pilot workload resources:

- ECR repository: `agentconstruct-customer-ai-platform-control-plane`
- IAM role: `agentconstruct-customer-apprunner-ecr`
- IAM role: `agentconstruct-customer-apprunner-runtime`
- CloudWatch log group: `/aws/apprunner/agentconstruct-customer-control-plane`
- App Runner service: `agentconstruct-customer-control-plane`

The Terraform state key was:

```text
agentconstruct/customer-workload-app-runner-pilot.tfstate
```

## Commands executed

```bash
AWS_PROFILE=ai-platform-pilot-key AWS_REGION=us-east-1 \
EXPECTED_AWS_ACCOUNT_ID=654654474502 \
TF_STATE_BUCKET=agentconstruct-tfstate-654654474502 \
TF_LOCK_TABLE=agentconstruct-terraform-locks \
AGENTCONSTRUCT_CUSTOMER_SOURCE_COMMIT=de60dfe2e24930d76e6be8a5fb2c428e35f483c6 \
AGENTCONSTRUCT_CUSTOMER_PLAN_DIGEST=pilot-cycle-2 \
CONFIRM_CUSTOMER_WORKLOAD_FOUNDATION_APPLY=APPLY_CUSTOMER_WORKLOAD_FOUNDATION \
./scripts/customer-workload-app-runner-pilot.sh apply-foundation

AGENTCONSTRUCT_CUSTOMER_SOURCE_DIR=/tmp/.../ai-platform-control-plane \
AGENTCONSTRUCT_CUSTOMER_ECR_REPOSITORY_URL=654654474502.dkr.ecr.us-east-1.amazonaws.com/agentconstruct-customer-ai-platform-control-plane \
AGENTCONSTRUCT_CUSTOMER_IMAGE_TAG=cycle2-de60dfe2e249 \
./scripts/customer-workload-app-runner-pilot.sh build-push-image

AGENTCONSTRUCT_ENABLE_CUSTOMER_SERVICE=true \
AGENTCONSTRUCT_CUSTOMER_IMAGE_IDENTIFIER=654654474502.dkr.ecr.us-east-1.amazonaws.com/agentconstruct-customer-ai-platform-control-plane:cycle2-de60dfe2e249 \
CONFIRM_CUSTOMER_WORKLOAD_SERVICE_APPLY=APPLY_CUSTOMER_WORKLOAD_SERVICE \
./scripts/customer-workload-app-runner-pilot.sh apply-service

AGENTCONSTRUCT_ENABLE_CUSTOMER_SERVICE=true \
AGENTCONSTRUCT_CUSTOMER_IMAGE_IDENTIFIER=654654474502.dkr.ecr.us-east-1.amazonaws.com/agentconstruct-customer-ai-platform-control-plane:cycle2-de60dfe2e249 \
./scripts/customer-workload-app-runner-pilot.sh wait-ready

AGENTCONSTRUCT_ENABLE_CUSTOMER_SERVICE=true \
AGENTCONSTRUCT_CUSTOMER_IMAGE_IDENTIFIER=654654474502.dkr.ecr.us-east-1.amazonaws.com/agentconstruct-customer-ai-platform-control-plane:cycle2-de60dfe2e249 \
./scripts/customer-workload-app-runner-pilot.sh smoke
```

## Observed result

App Runner service ARN:

```text
arn:aws:apprunner:us-east-1:654654474502:service/agentconstruct-customer-control-plane/99b6286c6e37463c91921b6ca0282c13
```

Temporary App Runner URL:

```text
https://tpayu7abh2.us-east-1.awsapprunner.com
```

Observed App Runner status:

```text
RUNNING
```

Smoke result:

```text
https://tpayu7abh2.us-east-1.awsapprunner.com/healthz returned {"status":"ok"}
```

## Teardown

```bash
AGENTCONSTRUCT_ENABLE_CUSTOMER_SERVICE=true \
AGENTCONSTRUCT_CUSTOMER_IMAGE_IDENTIFIER=654654474502.dkr.ecr.us-east-1.amazonaws.com/agentconstruct-customer-ai-platform-control-plane:cycle2-de60dfe2e249 \
CONFIRM_CUSTOMER_WORKLOAD_DESTROY=DESTROY_CUSTOMER_WORKLOAD \
./scripts/customer-workload-app-runner-pilot.sh destroy

./scripts/customer-workload-app-runner-pilot.sh verify-absent
```

Destroy result:

```text
Destroy complete. Resources: 7 destroyed.
Customer workload AWS resources absent: service=true, ecr_repository=deleted
```

## Final cleanup verification

After this second run:

- No AgentConstruct App Runner services remained.
- No AgentConstruct ECR repositories remained.
- App Runner-created CloudWatch log groups for both customer workload cycles and old AgentConstruct runtime checks were deleted.
- Customer workload Terraform output was `{}`, confirming empty state outputs after destroy.

Retained support resources:

- `arn:aws:s3:::agentconstruct-tfstate-654654474502`
- `arn:aws:dynamodb:us-east-1:654654474502:table/agentconstruct-terraform-locks`
- `arn:aws:iam::654654474502:oidc-provider/token.actions.githubusercontent.com`
- `agentconstruct-control-plane-github`
- `agentconstruct-adewale-primary-aws-discovery`
- `agentconstruct-adewale-primary-aws-execution`

## Final boundary

This test recreated and destroyed a real AWS App Runner customer workload.

It did not create:

- RDS or another durable customer-data database
- VPC or private networking
- Prometheus or Grafana runtime
- GitHub pull request
- GitOps sync
- Argo CD deployment
- EKS workload

The customer app’s protected JWT/OPA write paths were not validated in this run; only App Runner service creation, container start, `RUNNING` state, `/healthz`, and teardown were validated.
