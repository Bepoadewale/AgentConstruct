# Customer AWS connection

davdeploy connects to a customer AWS account in stages. The first stage is discovery only.

## What the first role can do

The Terraform contract creates a discovery role with short-lived STS access. It can list and describe approved AWS infrastructure and ask Cost Explorer for cost information. It can inspect services such as VPCs, App Runner, ECS, EKS, Lambda, RDS, ElastiCache, ECR and bucket metadata.

It cannot create, change or delete infrastructure. It cannot read Secrets Manager values, S3 object contents, container images, application logs or database data. It does not create an access key.

## What the second role can do

The separate execution role has no permissions at all. It exists only so a later, approved architecture profile can receive its own narrow policy. A simple App Runner plan must not receive EKS permissions; an EKS plan must not receive general AWS administrator access.

## Trust boundary

Both roles trust one future davdeploy control-plane IAM role and require a unique external ID. The external ID protects the cross-account trust relationship; it is not an AWS access key or reusable customer credential. The encrypted Terraform state that contains the trust policy must remain private.

An authenticated plan needs the real ARN of that control-plane role. davdeploy does not have a deployed management account or workload identity yet, so this PR does not invent one or run a customer-account plan with a fake principal.

The browser, CLI and MCP server never receive this role or any STS credential. Only the governed control plane can request a short-lived session after tenant, account and policy checks.

## Current state

**Statically validated:** Terraform format, offline initialisation and validation; read-only permission and confirmation-gate tests.

**Not executed:** an authenticated AWS plan, IAM role creation, STS assumption, inventory discovery, Cost Explorer query or any customer workload change.
