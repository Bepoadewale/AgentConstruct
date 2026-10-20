# test99

Date: 2026-10-20
Execution type: Controlled live production customer journey
Customer repository: No customer repository write; DavDeploy production control plane only
AWS account: 654654474502
AWS region: us-east-1

## Scope

This run is limited to authentication, planning, governance, bounded fixture execution,
observation, audit, and teardown through the deployed API. The initial production pass exercised
authentication, organization onboarding, invitation acceptance, tenant isolation, project
creation, and Nova intent interpretation. It exposed a model-repair defect before any plan or
execution job was created.

## Resources created

- Two temporary Cognito QA users, one administrator and one developer.
- One production workspace created through first-user onboarding.
- One accepted workspace invitation.
- One production project for `Bepoadewale/davdeploy-frontend`.
- No customer AWS workload resources.

## Commands executed

- Cognito administrative user creation with email delivery suppressed.
- Cognito `USER_AUTH` password challenges for both temporary QA users.
- Authenticated `/api/v1/me`, onboarding, invitation, acceptance, project, and intent API calls.
- Focused model-gateway and Nova intent tests: 17 passed.
- One clean-room repository validation cycle:
  `make clean-local`, `make bootstrap-local`, all canonical demos, API contract, customer-plan
  E2E, trace check, Terraform validation, `make verify`, and final `make clean-local`.

## Observed result

- Unonboarded authentication was rejected with HTTP 403.
- The first user became an administrator and created the workspace.
- The invited user accepted membership and resolved as a developer in the same workspace.
- The developer created project `9f3167c8-0239-4e44-8743-701e29222eaf`.
- Nova was invoked, but both its original and repair responses violated the typed intent schema.
  The API correctly returned HTTP 503 and persisted no false plan.
- Root cause: the repair request did not include the rejected response or bounded Pydantic
  validation diagnostics.
- The repair request now carries the rejected response plus field locations and error types. A
  regression test proves the context is bounded and excludes rejected input values.
- The clean-room cycle passed all demonstrations, contract checks, Terraform validation, lint,
  OpenAPI drift checking, and 234 tests. One upstream Starlette deprecation warning remains.

## Teardown

The local validation stack and volumes were removed by `make clean-local`. Temporary Cognito users
remain only until the repaired production release is deployed and the journey resumes. Production
workspace, project, and audit records are intentionally retained as immutable evidence.

## Final boundary

This run did not create or delete customer AWS workload resources. The remaining lifecycle stages
will resume after this fix is merged and released through the manual Terraform plan and apply
gates.
