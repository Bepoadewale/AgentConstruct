# test81 — Platform runtime readiness and live Nova evidence

Date: 2026-10-16.

Execution type: authenticated AWS plan-only validation and bounded live Amazon
Nova 2 Lite inference, plus local and static validation. No Terraform apply or
customer workload execution occurred.

Customer repository: `Bepoadewale/AgentConstruct`.

Commit: `ee852c1` plus the PR's final implementation and evidence commits.

AWS account: `654654474502`.

AWS region: `us-east-1`.

## Classification

This evidence includes real AWS identity, Terraform refresh/plan, Bedrock model
availability and Bedrock Converse API calls. The Terraform runs were plans only.
The two Nova inputs were fixed synthetic cases; no customer data was sent. Raw
prompts and model responses were not retained in the evidence artifact.

## Resources created

None. Terraform was not applied. The Bedrock calls were API inference requests,
not durable infrastructure. The existing remote-state bucket, lock table,
CloudFormation template and AWS Budget were inspected but not changed.

## Commands executed

With the existing `ai-platform-pilot-key` AWS CLI profile and reviewed remote
state settings, the following command classes were run:

```bash
aws sts get-caller-identity
aws bedrock get-inference-profile --inference-profile-identifier us.amazon.nova-2-lite-v1:0

AGENTCONSTRUCT_ENABLE_DURABLE_DATABASE=true \
AGENTCONSTRUCT_ENABLE_NOVA_MODEL=true \
AGENTCONSTRUCT_ENABLE_RUNTIME_SERVICE=false \
AGENTCONSTRUCT_PLATFORM_MONTHLY_BUDGET_USD=250 \
AGENTCONSTRUCT_ALERT_EMAIL='<redacted operator address>' \
./scripts/app-runner-runtime.sh plan

AGENTCONSTRUCT_ENABLE_DURABLE_DATABASE=true \
AGENTCONSTRUCT_ENABLE_NOVA_MODEL=true \
AGENTCONSTRUCT_ENABLE_RUNTIME_SERVICE=true \
./scripts/app-runner-runtime.sh plan

EXPECTED_AWS_ACCOUNT_ID=654654474502 AWS_REGION=us-east-1 \
  .venv/bin/python scripts/nova_live_evaluation.py \
  --output /tmp/agentconstruct-nova-live81.json
```

Repository validation also included Ruff, pytest, documentation conventions,
shell syntax checks, Terraform formatting and validation. Each completed
clean-room cycle ran:

```bash
make clean-local
make bootstrap-local
make smoke
make browser-contract
make frontend-contract
make frontend-responsive-contract
make frontend-accessibility-contract
make local-load-smoke
make customer-plan-e2e
make demo-simple
make demo-complex
make demo-degraded
make demo-day2
make demo-failure
make demo-readiness-failure
make trace-check
make verify
make opa-test
make terraform-validate
make kubernetes-render
make clean-local
```

## Observed result

- AWS identity resolved to the exact expected account and Region.
- The foundation plan completed with `20 to add, 0 to change, 0 to destroy`.
- The foundation plan contained no NAT gateway, Elastic IP, Internet gateway,
  App Runner service or local fixture signing key.
- A service-enabled plan without an immutable image, HTTPS JWKS/OIDC settings
  and HTTPS OPA endpoint failed the Terraform preconditions before apply.
- The Nova inference profile was active.
- Two fixed synthetic evaluations passed typed validation. Combined provider
  usage was 569 input tokens and 131 output tokens, or 700 billed tokens. The
  observed calls took 588 ms and 480 ms. These two calls are integration
  evidence, not a model-quality, throughput or production-latency claim.
- The first live attempt encountered a transient AWS account-verification
  response. A later bounded retry succeeded.
- Live output showed that Nova can return an exact `json` code fence. The
  gateway now accepts only a plain JSON object or one exact JSON fence, then
  applies the same strict typed validation. Surrounding prose remains rejected.
- Pricing was not calculated because no current versioned token-price catalog
  was configured.
- Two complete clean-room cycles passed. Each cold-built the stack, exercised
  readiness, browser/interaction/responsive/accessibility contracts, the
  50-request concurrency-5 load smoke, governed customer-plan E2E, simple,
  complex, degraded, Day-2, policy-denial and readiness-failure paths, trace
  collection, 196 tests, OPA 3/3, all Terraform roots and Kubernetes rendering.
  One observed local p95 was 22.5 ms; this is a smoke result, not a capacity
  claim. An intervening attempt stopped before final cleanup; its checks were
  reproduced and the whole cycle was repeated successfully from a clean state.

## Teardown

No AWS teardown was required because this PR created no durable AWS resource.
Each successful clean-room cycle ended with `make clean-local`, removing the
project containers, project volume, virtual environment and local runtime
state. Temporary Terraform plan and Nova evidence files were written under
`/tmp` and are not repository or customer data.

## Final boundary

This proves the reviewed foundation can be planned in the intended account and
that the governed Nova adapter can parse two live synthetic responses. It does
not prove an applied RDS foundation, snapshot restore, hosted Google Workspace
identity, hosted OPA, App Runner readiness, sustained model quality, customer
workload deployment or cross-account isolation. The platform and customer
sandbox remain separate VPC scopes in one AWS account; no AWS Organizations
member account is created or required.
