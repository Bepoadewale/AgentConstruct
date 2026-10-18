# Connect an AWS account

davdeploy starts with a read-only connection. It does not ask for AWS access keys or administrator access.

## What the customer does

1. In davdeploy, choose **Connect AWS account** and enter the 12-digit AWS account ID.
2. Select **Open AWS setup**.
3. In the AWS Console, review one CloudFormation stack, acknowledge IAM resource creation, and choose **Create stack**.
4. Return to davdeploy and select **Verify connection**. davdeploy queues a read-only check. Its runtime identity assumes the role for 15 minutes, reads infrastructure metadata, and stores a credential-free inventory snapshot.

The customer does not create an IAM user, write a policy, install Terraform, run a command, or copy a secret.

## What AWS creates

The template creates one `davdeployDiscovery-*` IAM role. It is allowed to read infrastructure metadata and Cost Explorer data only. It cannot create, update, delete, pass roles, read S3 objects, read database contents, or retrieve secret values.

The trust policy requires davdeploy's runtime role and one unique external ID. Sessions are short-lived. The external ID is held only in the control-plane secret store, never in the browser or a normal database field. The role can be removed to disconnect the account.

## Product boundary

The Quick Create endpoint only generates an AWS Console link. The customer creates the stack in their own account. The browser never receives AWS credentials. A separately approved execution role is required before davdeploy can provision a workload.

For local development, set `DAVDEPLOY_CONTROL_PLANE_ROLE_ARN`, `DAVDEPLOY_AWS_CONNECTION_TEMPLATE_URL`, and the explicit live-discovery flag only outside Git. Production uses a separate runtime role, not the GitHub Actions role. Use `DAVDEPLOY_CONNECTION_SECRET_BACKEND=aws_secrets_manager` in hosted environments; `local_encrypted` is only a local substitute. The template URL must be a public, versioned S3 object with no customer data or secrets; a private repository raw URL is not suitable. The Terraform template-host root is applied and verified. The App Runner runtime root is also applied for read-only discovery validation, with fixture sign-in/policy and ephemeral SQLite still clearly labeled non-production.

## Current hosted validation

On 2026-10-13, the AWS-hosted davdeploy runtime at `https://x75qgwappp.us-east-1.awsapprunner.com` created a Quick Create URL, assumed the resulting customer read-only discovery role with STS, and stored a credential-free inventory snapshot with `live-read-only-sts-discovery` provenance. The temporary customer CloudFormation stack, discovery role and per-connection ExternalId secret were deleted after verification. No customer workload resources were created.

Current hosted template URL:

```text
https://davdeploy-customer-templates-654654474502.s3.us-east-1.amazonaws.com/cloudformation/customer-discovery-role-0e3209bff02286acf582ec3ed73858266261b294ae0c7e0d30ae37550a8926b2.yaml
```
