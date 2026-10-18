# Serverless control plane

This root defines the early hosted AgentConstruct control plane:

- API Gateway HTTP API and Python Lambda for FastAPI
- Aurora PostgreSQL Serverless v2 through RDS Data API
- Cognito with Google federation and email OTP
- isolated policy Lambda
- SQS-triggered worker with a dead-letter queue
- Nova 2 Lite permissions

The two Aurora subnets are database-only. The stack intentionally contains no NAT Gateway, Internet Gateway, VPC endpoint, or Lambda VPC attachment. Lambda calls Data API, Cognito, Bedrock, Secrets Manager, and external HTTPS services through AWS service endpoints or its default public networking.

Terraform does not store the Google client secret. Configure the Google identity provider after the user pool exists, using the operator procedure in `docs/SERVERLESS_DEPLOYMENT.md`, then set `google_identity_provider_enabled = true`.

This directory is plan-only until an operator supplies an existing artifact bucket, exact frontend origin, unique Cognito domain prefix, remote Terraform state, and a reviewed production variable file.
