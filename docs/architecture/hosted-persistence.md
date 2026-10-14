# Hosted control-plane persistence

Status: implemented and statically validated; not yet applied in AWS.

The hosted App Runner runtime originally proved the customer-AWS connection flow with ephemeral SQLite. That was acceptable for validation, but not for a commercial control plane. Production hosted mode now requires durable PostgreSQL.

## Runtime rule

When `AGENTCONSTRUCT_HOSTED_MODE=true`, AgentConstruct refuses any SQLite database URL. Hosted runtime must use one of:

- `AGENTCONSTRUCT_DATABASE_SECRET_ARN` plus `AGENTCONSTRUCT_DATABASE_NAME`; or
- a non-SQLite `AGENTCONSTRUCT_DATABASE_URL`.

The Secrets Manager path is preferred. The API reads the AWS-managed RDS master-user secret at startup and builds the SQLAlchemy PostgreSQL URL in memory. The secret value is not stored in product records, plans, audit events or Git.

## Terraform contract

`infrastructure/terraform/app-runner-runtime` now has an optional `enable_durable_database` mode.

When enabled, it creates:

- private VPC networking for the hosted runtime;
- private subnets across two availability zones;
- NAT egress for App Runner runtime calls to AWS APIs and approved external integrations;
- App Runner VPC connector;
- private encrypted RDS PostgreSQL;
- AWS-managed RDS master credential secret;
- database security group allowing PostgreSQL only from the App Runner connector security group;
- automated backups;
- deletion protection by default;
- App Runner environment variables that reference the database secret ARN and database name.

The App Runner runtime role receives `secretsmanager:GetSecretValue` only for the runtime signing key, per-connection ExternalId prefix and the RDS credential secret when RDS is enabled.

## Boundaries

- This is control-plane persistence, not customer workload persistence.
- Applying the RDS contract creates billable AWS resources.
- This PR does not apply RDS in AWS.
- The currently hosted App Runner runtime may continue using the older ephemeral database until the new contract is deliberately planned and applied.
- Fixture sign-in and fixture policy remain separate production-readiness gaps.

## Validation

Local unit tests prove:

- hosted mode rejects SQLite;
- local mode still permits SQLite;
- database URLs can be built from a Secrets Manager RDS secret reference.

Terraform validation proves the App Runner runtime contract is syntactically valid with the optional durable database resources.
