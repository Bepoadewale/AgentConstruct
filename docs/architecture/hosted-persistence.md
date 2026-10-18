# Hosted control-plane persistence

Status: serverless contract implemented and statically validated; not yet applied in AWS.

The historical App Runner runtime proved customer-AWS discovery with ephemeral SQLite. A commercial control plane requires durable PostgreSQL. The selected early hosted design is Aurora PostgreSQL Serverless v2 through RDS Data API.

## Runtime rule

Hosted mode requires both:

- `AGENTCONSTRUCT_AURORA_CLUSTER_ARN`
- `AGENTCONSTRUCT_DATABASE_SECRET_ARN`

`AGENTCONSTRUCT_DATABASE_NAME` selects the database. AgentConstruct uses the pinned `sqlalchemy-aurora-data-api` dialect, IAM-signed Data API calls, and the AWS-managed Aurora credential secret. It does not retrieve a raw password or open a PostgreSQL socket from Lambda.

Local development retains SQLite and ordinary PostgreSQL. Hosted mode rejects SQLite.

## Terraform contract

`infrastructure/terraform/serverless-control-plane` creates:

- isolated database subnets across two availability zones;
- Aurora PostgreSQL Serverless v2 with Data API enabled;
- AWS-managed master credentials in Secrets Manager;
- encrypted storage, backups, log export, final snapshot and deletion protection;
- Lambda IAM access scoped to the cluster and its credential secret.

The application Lambdas have no VPC attachment. The database VPC has no NAT Gateway or Internet Gateway. The database security group has no application ingress because Data API is the only application path.

## Migration behavior

API cold starts do not run schema migrations. An explicit migration Lambda runs the versioned migration sequence during a release. Traffic should not move to a new release until this function succeeds.

## Boundaries

- This is control-plane persistence, not customer workload persistence.
- Applying the contract creates billable AWS resources.
- Aurora Serverless v2 auto-pauses at zero capacity after an idle interval; resume latency and active/storage costs remain explicit tradeoffs.
- Data API response, row-size, transaction-duration and statement limits must be included in live load tests.
- The third-party SQLAlchemy dialect is pinned and covered by adapter tests, but a deployed compatibility test remains required.

## Validation

Unit tests verify Data API configuration and engine arguments. Terraform init and validate verify the serverless infrastructure shape. These checks do not prove live Aurora connectivity, schema migration, backup restore, concurrency or production latency.
