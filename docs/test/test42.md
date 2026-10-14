# test42 — Customer workload App Runner pilot for PR #42

Date: 2026-10-14

PR: [#42 — feat: deploy hosted AWS discovery runtime](https://github.com/Bepoadewale/AgentConstruct/pull/42)

Execution type: real AWS customer workload create → validate → destroy, repeated twice.

Customer repository: `https://github.com/Bepoadewale/ai-platform-control-plane`

Commit: `de60dfe2e24930d76e6be8a5fb2c428e35f483c6`

AWS account: `654654474502`

AWS region: `us-east-1`

Selected runtime profile: AWS App Runner.

Why App Runner: the customer repository exposes a single containerized FastAPI service with `/healthz`; this test did not require EKS, Kubernetes scheduling, GPUs, a database, or multi-service orchestration.

## Resources created

Each cycle created these pilot workload resources:

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

Cycle 1:

```bash
AWS_PROFILE=ai-platform-pilot-key AWS_REGION=us-east-1 \
EXPECTED_AWS_ACCOUNT_ID=654654474502 \
TF_STATE_BUCKET=agentconstruct-tfstate-654654474502 \
TF_LOCK_TABLE=agentconstruct-terraform-locks \
AGENTCONSTRUCT_CUSTOMER_SOURCE_COMMIT=de60dfe2e24930d76e6be8a5fb2c428e35f483c6 \
AGENTCONSTRUCT_CUSTOMER_PLAN_DIGEST=pilot-cycle-1 \
./scripts/customer-workload-app-runner-pilot.sh plan

CONFIRM_CUSTOMER_WORKLOAD_FOUNDATION_APPLY=APPLY_CUSTOMER_WORKLOAD_FOUNDATION \
./scripts/customer-workload-app-runner-pilot.sh apply-foundation

AGENTCONSTRUCT_CUSTOMER_SOURCE_DIR=/tmp/.../ai-platform-control-plane \
AGENTCONSTRUCT_CUSTOMER_ECR_REPOSITORY_URL=654654474502.dkr.ecr.us-east-1.amazonaws.com/agentconstruct-customer-ai-platform-control-plane \
AGENTCONSTRUCT_CUSTOMER_IMAGE_TAG=cycle1-de60dfe2e249 \
./scripts/customer-workload-app-runner-pilot.sh build-push-image

AGENTCONSTRUCT_ENABLE_CUSTOMER_SERVICE=true \
AGENTCONSTRUCT_CUSTOMER_IMAGE_IDENTIFIER=654654474502.dkr.ecr.us-east-1.amazonaws.com/agentconstruct-customer-ai-platform-control-plane:cycle1-de60dfe2e249 \
CONFIRM_CUSTOMER_WORKLOAD_SERVICE_APPLY=APPLY_CUSTOMER_WORKLOAD_SERVICE \
./scripts/customer-workload-app-runner-pilot.sh apply-service

AGENTCONSTRUCT_ENABLE_CUSTOMER_SERVICE=true \
AGENTCONSTRUCT_CUSTOMER_IMAGE_IDENTIFIER=654654474502.dkr.ecr.us-east-1.amazonaws.com/agentconstruct-customer-ai-platform-control-plane:cycle1-de60dfe2e249 \
./scripts/customer-workload-app-runner-pilot.sh wait-ready

AGENTCONSTRUCT_ENABLE_CUSTOMER_SERVICE=true \
AGENTCONSTRUCT_CUSTOMER_IMAGE_IDENTIFIER=654654474502.dkr.ecr.us-east-1.amazonaws.com/agentconstruct-customer-ai-platform-control-plane:cycle1-de60dfe2e249 \
./scripts/customer-workload-app-runner-pilot.sh smoke
```

Cycle 2:

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

Cycle 1 App Runner service ARN:

```text
arn:aws:apprunner:us-east-1:654654474502:service/agentconstruct-customer-control-plane/5d378e5d076f4f8f977d0483fafc0c51
```

Cycle 1 temporary App Runner URL:

```text
https://ksp93iumxq.us-east-1.awsapprunner.com
```

Cycle 1 observed App Runner status:

```text
RUNNING
```

Cycle 1 smoke result:

```text
https://ksp93iumxq.us-east-1.awsapprunner.com/healthz returned {"status":"ok"}
```

Cycle 2 App Runner service ARN:

```text
arn:aws:apprunner:us-east-1:654654474502:service/agentconstruct-customer-control-plane/99b6286c6e37463c91921b6ca0282c13
```

Cycle 2 temporary App Runner URL:

```text
https://tpayu7abh2.us-east-1.awsapprunner.com
```

Cycle 2 observed App Runner status:

```text
RUNNING
```

Cycle 2 smoke result:

```text
https://tpayu7abh2.us-east-1.awsapprunner.com/healthz returned {"status":"ok"}
```

## Teardown

Cycle 1:

```bash
AGENTCONSTRUCT_ENABLE_CUSTOMER_SERVICE=true \
AGENTCONSTRUCT_CUSTOMER_IMAGE_IDENTIFIER=654654474502.dkr.ecr.us-east-1.amazonaws.com/agentconstruct-customer-ai-platform-control-plane:cycle1-de60dfe2e249 \
CONFIRM_CUSTOMER_WORKLOAD_DESTROY=DESTROY_CUSTOMER_WORKLOAD \
./scripts/customer-workload-app-runner-pilot.sh destroy

./scripts/customer-workload-app-runner-pilot.sh verify-absent
```

Cycle 1 destroy result:

```text
Destroy complete. Resources: 7 destroyed.
Customer workload AWS resources absent: service=true, ecr_repository=deleted
```

Cycle 2:

```bash
AGENTCONSTRUCT_ENABLE_CUSTOMER_SERVICE=true \
AGENTCONSTRUCT_CUSTOMER_IMAGE_IDENTIFIER=654654474502.dkr.ecr.us-east-1.amazonaws.com/agentconstruct-customer-ai-platform-control-plane:cycle2-de60dfe2e249 \
CONFIRM_CUSTOMER_WORKLOAD_DESTROY=DESTROY_CUSTOMER_WORKLOAD \
./scripts/customer-workload-app-runner-pilot.sh destroy

./scripts/customer-workload-app-runner-pilot.sh verify-absent
```

Cycle 2 destroy result:

```text
Destroy complete. Resources: 7 destroyed.
Customer workload AWS resources absent: service=true, ecr_repository=deleted
```

## Final cleanup verification

After cycle 2:

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

This PR test created and destroyed a real AWS App Runner customer workload twice.

It did not create:

- RDS or another durable customer-data database
- VPC or private networking
- Prometheus or Grafana runtime
- GitHub pull request
- GitOps sync
- Argo CD deployment
- EKS workload

The customer app’s protected JWT/OPA write paths were not validated in this run; only App Runner service creation, container start, `RUNNING` state, `/healthz`, and teardown were validated.
