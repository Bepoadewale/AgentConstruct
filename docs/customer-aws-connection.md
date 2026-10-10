# Connect an AWS account

AgentConstruct starts with a read-only connection. It does not ask for AWS access keys or administrator access.

## What the customer does

1. In AgentConstruct, choose **Connect AWS account** and enter the 12-digit AWS account ID.
2. Select **Open AWS setup**.
3. In the AWS Console, review one CloudFormation stack, acknowledge IAM resource creation, and choose **Create stack**.
4. Return to AgentConstruct and select **Verify connection**. AgentConstruct queues a read-only check. Its runtime identity assumes the role for 15 minutes, reads infrastructure metadata, and stores a credential-free inventory snapshot.

The customer does not create an IAM user, write a policy, install Terraform, run a command, or copy a secret.

## What AWS creates

The template creates one `AgentConstructDiscovery-*` IAM role. It is allowed to read infrastructure metadata and Cost Explorer data only. It cannot create, update, delete, pass roles, read S3 objects, read database contents, or retrieve secret values.

The trust policy requires AgentConstruct's runtime role and one unique external ID. Sessions are short-lived. The external ID is held only in the control-plane secret store, never in the browser or a normal database field. The role can be removed to disconnect the account.

## Product boundary

The Quick Create endpoint only generates an AWS Console link. The customer creates the stack in their own account. The browser never receives AWS credentials. A separately approved execution role is required before AgentConstruct can provision a workload.

For local development, set `AGENTCONSTRUCT_CONTROL_PLANE_ROLE_ARN`, `AGENTCONSTRUCT_AWS_CONNECTION_TEMPLATE_URL`, and the explicit live-discovery flag only outside Git. Production uses a separate workload/IRSA runtime role, not the GitHub Actions role. Use `AGENTCONSTRUCT_CONNECTION_SECRET_BACKEND=aws_secrets_manager` in production; `local_encrypted` is only a local substitute. The template URL must be a public, versioned S3 object with no customer data or secrets; a private repository raw URL is not suitable. The Terraform template-host and runtime-identity roots are confirmation-gated and have not been applied.
