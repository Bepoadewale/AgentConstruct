# test1 — Customer workload App Runner pilot, cycle 1

Date: 2026-10-14

Execution type: real AWS customer workload create → validate → destroy.

Customer repository: `https://github.com/Bepoadewale/ai-platform-control-plane`

Commit: `de60dfe2e24930d76e6be8a5fb2c428e35f483c6`

AWS account: `654654474502`

AWS region: `us-east-1`

Selected runtime profile: AWS App Runner.

Why App Runner: the customer repository exposes a single containerized FastAPI service with `/healthz`; this test did not require EKS, Kubernetes scheduling, GPUs, a database, or multi-service orchestration.

## Resources created

Terraform created the pilot workload resources:

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

## Observed result

App Runner service ARN:

```text
arn:aws:apprunner:us-east-1:654654474502:service/agentconstruct-customer-control-plane/5d378e5d076f4f8f977d0483fafc0c51
```

Temporary App Runner URL:

```text
https://ksp93iumxq.us-east-1.awsapprunner.com
```

Observed App Runner status:

```text
RUNNING
```

Smoke result:

```text
https://ksp93iumxq.us-east-1.awsapprunner.com/healthz returned {"status":"ok"}
```

## Teardown

```bash
AGENTCONSTRUCT_ENABLE_CUSTOMER_SERVICE=true \
AGENTCONSTRUCT_CUSTOMER_IMAGE_IDENTIFIER=654654474502.dkr.ecr.us-east-1.amazonaws.com/agentconstruct-customer-ai-platform-control-plane:cycle1-de60dfe2e249 \
CONFIRM_CUSTOMER_WORKLOAD_DESTROY=DESTROY_CUSTOMER_WORKLOAD \
./scripts/customer-workload-app-runner-pilot.sh destroy

./scripts/customer-workload-app-runner-pilot.sh verify-absent
```

Destroy result:

```text
Destroy complete. Resources: 7 destroyed.
Customer workload AWS resources absent: service=true, ecr_repository=deleted
```

## Final boundary

This test created and destroyed a real AWS App Runner customer workload.

It did not create:

- RDS or another durable customer-data database
- VPC or private networking
- Prometheus or Grafana runtime
- GitHub pull request
- GitOps sync
- Argo CD deployment
- EKS workload

The customer app’s protected JWT/OPA write paths were not validated in this run; only App Runner service creation, container start, `RUNNING` state, `/healthz`, and teardown were validated.
