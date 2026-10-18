# test92

Date: 2026-10-18
Execution type: Real AWS prerequisite migration, static workflow validation, and post-merge manual
Terraform plan
Customer repository: No customer workload repository; control-plane repository
`Bepoadewale/davdeploy`
Commit: `373e3dc` plus the implementation changes recorded by this evidence file
AWS account: `654654474502`
AWS region: `us-east-1`

## Resources created

- Private, versioned state bucket `davdeploy-tfstate-654654474502`.
- DynamoDB lock table `davdeploy-terraform-locks` in on-demand mode.
- Private, versioned saved-plan and release buckets.
- Two KMS keys with DavDeploy aliases for saved plans and release packages.
- Least-privilege GitHub OIDC plan and apply roles scoped to the renamed repository and respective
  GitHub environments.

Terraform reported 30 resources added across the two prerequisite roots, with zero changed and zero
destroyed. The old prerequisite resources were retained for recovery and were not modified by these
applies.

## Commands executed

```text
make install
make verify
make terraform-validate
GITHUB_PR_NUMBER=92 .venv/bin/python scripts/check_doc_conventions.py
PyYAML safe-load of every .github/workflows/*.yml file
git diff --check
```

## Observed result

- Ruff passed.
- All 226 Pytest tests passed with one upstream Starlette deprecation warning.
- The OpenAPI v1 snapshot matched the FastAPI application.
- Docker Compose configuration validated.
- Every Terraform root initialized without its remote backend and validated successfully.
- PR ticket and evidence conventions passed.
- Every workflow file parsed as valid YAML and the diff passed whitespace validation.
- The manual Terraform plan remains a post-merge validation item. Terraform apply will not be
  dispatched.

## Teardown

No teardown was performed. The new prerequisites are the active production workflow foundation.
The old prerequisites are retained, isolated from the active GitHub environments, and recoverable.

## Final boundary

- The prerequisite applies did not create the serverless control plane.
- A Terraform plan may upload one versioned Lambda release package and one encrypted saved plan.
- No customer workload, API, database, Cognito pool, queue, or production runtime is created until
  a separately authorized Terraform apply.
