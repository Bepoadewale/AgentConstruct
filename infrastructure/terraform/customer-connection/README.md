# Customer AWS connection: identity only

This Terraform root creates no application, network, database, cluster, registry, workload, or customer deployment resource.

It defines two IAM roles in a customer AWS account:

- **Discovery role:** short-lived, read-only inventory and Cost Explorer access. It cannot create, update, delete, read secrets, read object contents, pull images, or obtain registry credentials.
- **Execution role contract:** a separate role with **no permissions**. A later approved architecture profile must attach a narrowly scoped policy before it can do anything.

Both roles trust one future AgentConstruct control-plane IAM role and require a unique external ID. This is a cross-account STS design, not a browser credential design. No AWS access key is created or stored.

## Plan only

Use the script below with values supplied outside Git. It checks the AWS account before planning. Do not put a real external ID in a `.tfvars` file or commit it.

Before an authenticated plan, AgentConstruct needs a real control-plane IAM role in its own management account. This repository does not create that platform role yet, and a made-up ARN must never be applied. Until that prerequisite exists, only static validation is possible.

```bash
AWS_PROFILE=<customer-profile> \
EXPECTED_AWS_ACCOUNT_ID=<customer-account-id> \
AWS_REGION=us-east-1 \
TF_STATE_BUCKET=<agentconstruct-state-bucket> \
TF_LOCK_TABLE=<agentconstruct-lock-table> \
CUSTOMER_CONNECTION_ID=<connection-id> \
AGENTCONSTRUCT_CONTROL_PLANE_ROLE_ARN=<future-control-plane-role-arn> \
AGENTCONSTRUCT_EXTERNAL_ID=<generated-secret> \
make customer-aws-connection-plan
```

`apply` is confirmation-gated and must not be used until the customer reviews the exact plan. The static CI check runs only `fmt`, `init -backend=false`, and `validate`.
