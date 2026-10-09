# Connect an AWS account

AgentConstruct starts with a read-only connection. It does not ask for AWS access keys or administrator access.

## What the customer does

1. In AgentConstruct, select **Connect AWS** and enter the 12-digit AWS account ID.
2. Select **Open AWS setup**.
3. In the AWS Console, review one CloudFormation stack, acknowledge IAM resource creation, and choose **Create stack**.
4. Return to AgentConstruct and select **Verify connection**.

The customer does not create an IAM user, write a policy, install Terraform, run a command, or copy a secret.

## What AWS creates

The template creates one `AgentConstructDiscovery-*` IAM role. It is allowed to read infrastructure metadata and Cost Explorer data only. It cannot create, update, delete, pass roles, read S3 objects, read database contents, or retrieve secret values.

The trust policy requires AgentConstruct's control-plane role and one unique external ID. Sessions are short-lived. The role can be removed to disconnect the account.

## Product boundary

The Quick Create endpoint only generates an AWS Console link. The customer creates the stack in their own account. A separately approved execution role is required before AgentConstruct can provision a workload.

For local development, set `AGENTCONSTRUCT_CONTROL_PLANE_ROLE_ARN` and the hosted template URL only outside Git. The template URL must be publicly reachable by the AWS Console; a private repository raw URL is not suitable.
