# ticket79: Add governed Amazon Nova 2 Lite model gateway

- PR: #79
- Branch: `feat/nova-2-lite-gateway`
- Status: in progress

## Problem / goal

AgentConstruct currently exposes a provider-neutral model boundary but only ships
with deterministic and disabled adapters. Add Amazon Nova 2 Lite through Amazon
Bedrock so real language interpretation can be introduced without granting the
model approval, policy, execution, or cloud authority.

## Current repo state

- `ModelGateway` already defines structured completion, validation, and cost
  estimation boundaries.
- Admission policy constrains provider, output-token budget, and timeout.
- The deterministic fixture remains the only configured implementation.
- Planning, policy, approval, and execution remain separate deterministic
  systems.

## Research / references used

- Amazon Nova 2 documentation and model identifiers.
- Amazon Bedrock Converse and structured-output API documentation.
- Repository ADR-005 and queue/model-gateway architecture guidance.

## Work planned for the PR

- Add a Bedrock-backed Nova 2 Lite adapter using strict structured output.
- Add configuration, bounded retries/timeouts, usage metadata, safe errors, and
  deterministic fallback behavior.
- Keep credentials outside configuration and use the AWS SDK credential chain.
- Add unit and contract tests for success, refusal, malformed output, budgets,
  tenant data policy, fallback, and telemetry.
- Document local setup, runtime boundaries, and rollout controls.

## Acceptance criteria

- Nova 2 Lite can return schema-valid structured proposals through
  `ModelGateway`.
- The adapter cannot approve plans or invoke execution capabilities.
- Requests enforce configured token, timeout, provider, and tenant-data limits.
- Model/provider/prompt/usage/latency/request metadata is auditable without
  retaining secrets or raw prompts by default.
- Failures are bounded and can fall back to the deterministic fixture when that
  behavior is explicitly enabled.
- Local and CI tests require no AWS credentials or network access.
- Relevant lint, tests, documentation checks, and clean-room validation pass.

## Acceptance status

- [ ] Structured Nova 2 Lite responses are schema validated.
- [ ] Authority boundaries remain intact.
- [ ] Admission and data-policy limits are enforced.
- [ ] Safe audit metadata is produced.
- [ ] Explicit deterministic fallback is covered.
- [ ] Tests remain credential-free and offline.
- [ ] Required validation passes.

## Tests / validation performed

Pending implementation.

## Evidence files produced

No customer workload execution is planned. If the validation process performs a
customer workload cycle, `docs/test/test79.md` will record it.

## Boundaries

- No AWS resource, Bedrock invocation, customer workload, or Terraform apply is
  performed by this PR's local validation.
- Nova proposes typed data only. Policy, approval, plan hashing, and bounded
  execution remain independent.
- No AWS access keys or other long-lived credentials are added.

## Follow-up work

- Enable Bedrock model access in the production AWS account and run an explicitly
  authorized, budget-capped live evaluation before tenant rollout.
