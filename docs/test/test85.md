# test85: Serverless control plane and authentication

Date: 2026-10-18

Execution type: Local clean-room, simulated customer workflow, static Terraform validation, and
offline release-package validation.

Customer repository: Local AgentConstruct fixtures only.

Commit: Branch `feat/serverless-control-plane`; final commit recorded by PR #85.

AWS account: Not contacted.

AWS region: Static default `us-east-1`; no regional API call was made.

## Resources created

Ephemeral local Docker containers, networks, volumes, PostgreSQL data, and temporary build files.
No AWS, GitHub, Google, SES, Cognito, Cloudflare, or customer resource was created.

## Commands executed

```text
make clean-local
make bootstrap-local
make smoke
make demo
make demo-simple
make demo-complex
make demo-degraded
make demo-day2
make demo-failure
make demo-readiness-failure
make customer-plan-e2e
make seed-demo-data
make trace-check
make verify
make clean-local
make terraform-validate
scripts/build_lambda_packages.sh <temporary-output-directory>
unzip -t <temporary-output-directory>/agentconstruct-control-plane.zip
```

The complete clean cycle was run twice before the repository requirement was reduced to one. Both
cycles used fresh dependencies and local state.

## Observed result

- Both clean cycles passed.
- Each test suite completed with 216 passed and one upstream deprecation warning.
- All demos, customer-plan workflow, trace check, lint, OpenAPI snapshot, and Compose validation
  passed.
- All Terraform roots initialized without backends and validated successfully.
- No readiness state was inferred: the readiness-failure scenario recorded failure as expected.
- Policy denial prevented execution in the policy-failure scenario.

## Teardown

`make clean-local` removed the local Compose stack, volumes, virtual environment, and generated
local runtime data after each cycle. Temporary Lambda packaging directories use a cleanup trap.

## Final boundary

This is local, simulated, and static evidence. It does not prove AWS IAM, API Gateway, Lambda,
Aurora Data API, Cognito, Google federation, SES delivery, Bedrock inference, Terraform plan, or
Terraform apply in a live account. No cloud apply or deployment occurred.
