# ticket79: Add governed Amazon Nova 2 Lite model gateway

- PR: #79
- Branch: `feat/nova-2-lite-gateway`
- Status: complete

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

- Amazon Nova 2 Lite model card and supported geographic inference profile IDs.
- Amazon Bedrock Converse and geographic cross-Region IAM documentation.
- Repository ADR-005 and queue/model-gateway architecture guidance.

The official model card currently marks Bedrock native structured outputs as
unsupported for Nova 2 Lite. The implementation therefore uses JSON-only prompt
guidance followed by strict local Pydantic validation and one bounded repair
attempt; it does not claim provider-enforced schema compliance.

## Work planned for the PR

- Add a Bedrock-backed Nova 2 Lite adapter using JSON-only responses and strict
  local schema validation.
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

- [x] Nova 2 Lite JSON responses are strictly schema validated locally.
- [x] Authority boundaries remain intact.
- [x] Admission and data-policy limits are enforced.
- [x] Safe audit metadata and usage metering are produced.
- [x] Explicit deterministic fallback is covered and labelled as a fixture.
- [x] Tests remain credential-free and offline.
- [x] Required validation passes.

## Tests / validation performed

Validated on 2026-10-15 with:

- `make lint`;
- `make test` — 187 passed, with one upstream Starlette/httpx deprecation
  warning;
- `python3 scripts/check_doc_conventions.py`;
- `git diff --check`;
- `make terraform-validate`;
- two complete clean-room cycles recorded in `docs/test/test79.md`.

Both cycles additionally passed smoke, browser/interaction/responsive/
accessibility contracts, a bounded local load smoke, customer-plan E2E,
simple/complex/degraded/Day-2 demonstrations, policy and readiness failures,
Tempo trace verification, OPA 3/3, Terraform validation, Kubernetes rendering,
and final cleanup.

## Evidence files produced

- `docs/test/test79.md` records two local fixture customer-workload cycles.

## Boundaries

- No AWS resource, Bedrock invocation, customer workload, or Terraform apply is
  performed by this PR's local validation.
- Nova proposes typed data only. Policy, approval, plan hashing, and bounded
  execution remain independent.
- No AWS access keys or other long-lived credentials are added.
- Nova 2 Lite native structured output is not supported at the time of this PR;
  JSON is validated locally and failures are bounded.

## Follow-up work

- Enable Bedrock model access in the production AWS account and run an explicitly
  authorized, budget-capped live evaluation before tenant rollout.
- Verify the chosen inference profile's destination Regions and account SCPs at
  activation time rather than relying on the profile prefix alone.
