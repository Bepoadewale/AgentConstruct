# test111

Date: 2026-10-21
Execution type: Local workflow and Terraform validation, followed by a real control-plane migration
Customer repository: `https://github.com/Bepoadewale/ai-platform-control-plane`
Commit: Pending reviewed PR commit
AWS account: Existing DavDeploy control-plane account
AWS region: `us-east-1`

## Resources created

The local cycle created temporary Compose containers, one PostgreSQL volume, and Terraform
validation directories. All were removed by final cleanup. A reviewed Terraform plan has not yet
run. No customer cloud resources are in scope.

## Commands executed

- `terraform fmt -check -recursive infrastructure/terraform`
- `.venv/bin/python -m pytest tests/test_terraform_workflows.py tests/test_serverless_runtime.py tests/test_invitation_email.py -q`
- `make terraform-validate`
- One complete cycle: clean, bootstrap, smoke, API contract, customer-plan E2E, API restart,
  persistence check, simple/complex/degraded/Day-2 demos, policy failure, readiness failure,
  traces, verify, OPA, Terraform validation, Kubernetes rendering, MCP catalogue, clean.
- GitHub CI, manual Terraform plan, manual Terraform apply, and authenticated production API
  rechecks remain pending.

## Observed result

Focused validation passed 34 tests and every Terraform root. The clean-room cycle passed 254
tests, Ruff, OpenAPI parity, exact-origin CORS, customer-plan persistence after API restart, all
planning and failure journeys, Tempo traces, OPA 3/3, every Terraform root, Kubernetes rendering,
and the MCP authority boundary. Final cleanup removed all project containers, the database volume,
the virtual environment, and generated local state.

## Teardown

The control-plane schema upgrade is durable and is not torn down. Local validation resources are
removed by the clean-room cycle.

## Final boundary

The live journey stops after creating a review-only plan. It does not submit, approve, execute,
deploy, change, or destroy customer infrastructure.
