# ticket42 — Hosted AWS discovery runtime and customer workload App Runner pilot

PR: [#42 — feat: deploy hosted AWS discovery runtime](https://github.com/Bepoadewale/AgentConstruct/pull/42)

Branch: `feature/aws-hosted-runtime-verification`

Status: in review.

## Problem / goal

AgentConstruct needed evidence beyond local fixtures:

1. Host the AgentConstruct control-plane runtime in AWS for read-only customer AWS discovery verification.
2. Prove that the hosted runtime can guide a customer account connection without access keys.
3. Prove a real customer workload can be created, observed, destroyed, recreated, observed again, and destroyed again.
4. Preserve foundation/support resources but remove workload/runtime resources after validation.

## Current repo state before this PR

- Local AgentConstruct V1 already supported role-aware login, GitHub/AWS connection fixtures, one AWS plan, review/submission/approval, local dry-run execution and destroy.
- Terraform roots existed for bootstrap, customer connection, template host, runtime identity and plan-only App Runner rendering.
- App Runner renderer existed as a plan-only contract, not an apply path.
- Customer AWS discovery had been designed and partially verified, but AgentConstruct did not yet have a hosted runtime that could perform the read-only verification path.
- Customer workload cloud execution had not been run before this PR.

## Research / references used

Local repository references:

- `apps/api/`
- `infrastructure/terraform/app-runner-runtime/`
- `infrastructure/terraform/customer-connection/`
- `infrastructure/terraform/connection-template-host/`
- `infrastructure/terraform/renderers/app-runner-plan/`
- `scripts/customer-aws-connection.sh`
- `scripts/customer-aws-template-host.sh`
- `docs/customer-aws-connection.md`
- `docs/VALIDATION.md`

Customer workload repository:

- `https://github.com/Bepoadewale/ai-platform-control-plane`
- Commit: `de60dfe2e24930d76e6be8a5fb2c428e35f483c6`
- Relevant runtime file: `control-plane/Dockerfile`
- Health endpoint: `/healthz`

AWS account evidence:

- AWS account: `654654474502`
- Region: `us-east-1`
- AWS CLI profile: `ai-platform-pilot-key`

## Work planned for the PR

- Add App Runner runtime Terraform for hosted AgentConstruct discovery verification.
- Add runtime image build/push script.
- Add guarded runtime apply/destroy script.
- Add hosted runtime support for Secrets Manager-backed fixture signing key lookup.
- Add hosted inline AWS discovery verification mode.
- Add fixture-policy switch for hosted validation mode until production OPA is deployed.
- Record live hosted runtime and read-only customer discovery evidence.
- Add customer workload App Runner pilot Terraform root.
- Add guarded customer workload pilot script.
- Run customer workload create → validate → destroy twice.
- Store numbered per-run evidence under `docs/test/`.
- Keep foundation/support resources after teardown.

## Acceptance criteria

- [x] Hosted AgentConstruct runtime can be deployed to AWS App Runner.
- [x] Hosted runtime reaches `RUNNING`.
- [x] Hosted runtime health endpoint responds successfully.
- [x] Hosted runtime generates a customer AWS Quick Create flow.
- [x] Temporary customer CloudFormation stack creates a read-only discovery role.
- [x] Hosted runtime assumes the read-only discovery role with STS.
- [x] Hosted runtime records a credential-free inventory snapshot.
- [x] Temporary customer discovery stack, role and ExternalId secret are deleted after verification.
- [x] Customer workload repository can be built from its own Dockerfile.
- [x] Customer workload image is pushed to ECR.
- [x] Customer workload App Runner service reaches `RUNNING`.
- [x] Customer workload `/healthz` responds successfully.
- [x] Customer workload resources are destroyed and absence is verified.
- [x] Customer workload create → validate → destroy succeeds twice.
- [x] Foundation/support resources are retained.
- [x] Numbered customer workload evidence files exist.
- [x] Repo instructions require future PR-numbered customer workload evidence files.

## Acceptance status

Met.

## Tests / validation performed

Local/static validation:

```bash
git diff --check
make terraform-validate
```

Results:

- `git diff --check` passed.
- `make terraform-validate` passed across Terraform roots, including:
  - `infrastructure/terraform/app-runner-runtime`
  - `infrastructure/terraform/customer-workload-app-runner-pilot`

Hosted runtime validation:

- Terraform applied AWS App Runner runtime.
- Runtime reached `RUNNING`.
- Health endpoint returned `{"status":"ok","product":"AgentConstruct"}`.
- Hosted runtime completed read-only customer discovery verification.
- Temporary customer discovery stack/role/secret were deleted.

Customer workload validation:

- Cycle 1:
  - App Runner ARN: `arn:aws:apprunner:us-east-1:654654474502:service/agentconstruct-customer-control-plane/5d378e5d076f4f8f977d0483fafc0c51`
  - URL: `https://ksp93iumxq.us-east-1.awsapprunner.com`
  - `/healthz` returned `{"status":"ok"}`
  - Destroy removed 7 resources.
  - Absence check passed.
- Cycle 2:
  - App Runner ARN: `arn:aws:apprunner:us-east-1:654654474502:service/agentconstruct-customer-control-plane/99b6286c6e37463c91921b6ca0282c13`
  - URL: `https://tpayu7abh2.us-east-1.awsapprunner.com`
  - `/healthz` returned `{"status":"ok"}`
  - Destroy removed 7 resources.
  - Absence check passed.

## Evidence files produced

- `docs/VALIDATION.md`
- `docs/test/test42.md`

## Retained resources

The following foundation/support resources were intentionally retained:

- `agentconstruct-tfstate-654654474502`
- `agentconstruct-terraform-locks`
- GitHub OIDC provider: `token.actions.githubusercontent.com`
- `agentconstruct-control-plane-github`
- `agentconstruct-adewale-primary-aws-discovery`
- `agentconstruct-adewale-primary-aws-execution`

## Boundaries

- The hosted AgentConstruct runtime still uses fixture sign-in, fixture policy and SQLite in `/tmp`; it is validation/demo infrastructure, not production SaaS persistence.
- Customer discovery is read-only; no customer access keys are stored.
- Customer workload validation covered App Runner service creation, container start, `RUNNING`, `/healthz`, and teardown.
- Customer workload validation did not create RDS, durable customer-data storage, VPC, Prometheus/Grafana runtime, GitHub PRs, GitOps sync, Argo CD or EKS.
- Customer app protected JWT/OPA write paths were not validated in the App Runner workload pilot.

## Follow-up work

- Wire the App Runner workload execution path into the AgentConstruct UI/API after approval.
- Add durable data profile: App Runner + RDS PostgreSQL.
- Add real monitoring runtime with Prometheus-compatible metrics and Grafana.
- Replace hosted fixture sign-in/policy/SQLite with production OIDC/JWKS, OPA and durable persistence.
