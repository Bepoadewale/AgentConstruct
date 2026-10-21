# test113

Date: 2026-10-21
Execution type: Local workflow validation followed by a real control-plane migration retry
Customer repository: `https://github.com/Bepoadewale/ai-platform-control-plane`
Commit: `e650bd7`
AWS account: Existing DavDeploy control-plane account
AWS region: `us-east-1`

## Resources created

The local cycle created temporary Compose containers, one PostgreSQL volume, and Terraform
validation directories. Final cleanup removed them. No customer resources are in scope.

## Commands executed

- `GITHUB_PR_NUMBER=113 python3.12 scripts/check_doc_conventions.py`
- `terraform fmt -check -recursive infrastructure/terraform`
- `.venv/bin/python -m pytest tests/test_terraform_workflows.py -q`
- One complete cycle: clean, bootstrap, smoke, API contract, customer-plan E2E, API restart,
  persistence check, simple/complex/degraded/Day-2 demos, policy failure, readiness failure,
  traces, verify, OPA, Terraform validation, Kubernetes rendering, MCP catalogue, clean.
- GitHub CI run `39653642990`.
- Manual Terraform plan/apply and authenticated production API checks remain pending until the
  corrected workflow is merged to `main`.

## Observed result

Apply run `39652878720` proved the safety gate: Terraform applied 1 addition and 5 in-place changes
with 0 destroys, then migration invocation failed closed because the original OIDC session did not
inherit the policy created during that same apply. Focused workflow tests passed 6 tests. The
clean-room cycle passed 254 tests, Ruff, OpenAPI parity, exact-origin CORS, customer-plan
persistence after API restart, all planning and failure journeys, Tempo traces, OPA 3/3, every
Terraform root, Kubernetes rendering, and the MCP authority boundary. Final cleanup completed.
All seven required jobs in GitHub CI run `39653642990` passed, including the independent local E2E,
cloud-contract, policy, supply-chain, Python, documentation, and secret-scanning gates.

## Teardown

Local resources will be removed by the clean-room cycle. The durable control-plane migration is not
torn down.

## Final boundary

The live customer journey stops after a review-only plan and never submits, approves, executes,
deploys, changes, or destroys customer infrastructure.
