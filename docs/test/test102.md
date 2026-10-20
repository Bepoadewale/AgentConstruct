# test102

Date: 2026-10-20
Execution type: Local clean-room validation with deterministic fixture execution
Customer repository: Local davdeploy fixture workflows
Commit: `fix/profile-aware-fixture-metadata` worktree before final evidence commit
AWS account: 654654474502
AWS region: us-east-1

## Scope

Verify that bounded fixture observations truthfully match the selected architecture profile before
the correction is released to the production control plane.

## Commands executed

One clean-room cycle ran on 2026-10-20 with the repository Make targets for cleanup, bootstrap,
smoke, API contract, all demos, customer-plan E2E, persistence, trace, verification, OPA, Terraform
validation, and final cleanup.

## Resources created

Ephemeral local Docker containers, network, PostgreSQL volume, and fixture records only. No AWS
resource or customer cloud workload was created.

## Observed result

One clean-room cycle passed:

- cold bootstrap and all service readiness checks;
- versioned API and exact-origin CORS contract;
- simple, complex, degraded, Day-2, canonical, policy-failure, and readiness-failure demos;
- customer-plan E2E and seeded-data persistence after API restart;
- Tempo trace verification;
- Ruff and 241 tests;
- OpenAPI snapshot and Compose configuration;
- OPA 3/3;
- all Terraform roots;
- final project-scoped cleanup.

Focused regression tests covered Lambda, App Runner, ECS, EKS, and unknown future profiles. The
Lambda fixture record contained `lambda_function_arn` and `lambda_function` and no App Runner
label. The only warning was the existing upstream Starlette `httpx` deprecation warning.

All checks passed. Both the embedded Lambda fixture adapter and local HTTP fixture executor use the
same profile-aware primary-resource mapping.

## Teardown

`make clean-local` removed all project containers, the network, PostgreSQL volume, virtual
environment, and generated local state. No cloud teardown was required.

## Final boundary

Durable control-plane audit records are retained. Fixture execution proves workflow and governance
only; it does not prove a real customer cloud deployment.
