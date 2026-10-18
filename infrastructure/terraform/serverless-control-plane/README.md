# Serverless control plane

This root defines the early hosted davdeploy control plane:

- API Gateway HTTP API and Python Lambda for FastAPI
- Aurora PostgreSQL Serverless v2 through RDS Data API
- Cognito with Google federation and email OTP
- isolated policy Lambda
- SQS-triggered worker with a dead-letter queue
- Nova 2 Lite permissions

The two Aurora subnets are database-only. The stack intentionally contains no NAT Gateway, Internet Gateway, VPC endpoint, or Lambda VPC attachment. Lambda calls Data API, Cognito, Bedrock, Secrets Manager, and external HTTPS services through AWS service endpoints or its default public networking.

Terraform does not store the Google client secret. Configure the Google identity provider after the user pool exists, using the operator procedure in `docs/SERVERLESS_DEPLOYMENT.md`, then set `google_identity_provider_enabled = true`.

This directory defines one production control plane. The GitHub workflow uses the fixed
`serverless-control-plane/terraform.tfstate` state object, the canonical `davdeploy` resource
namespace, and one unique Cognito domain prefix. Development and staging environments are not
operator-selectable and require a future reviewed design change.
