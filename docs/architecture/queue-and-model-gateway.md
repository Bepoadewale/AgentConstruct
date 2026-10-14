# Queue and model gateway

## Queue boundary

`apps/api/src/agentconstruct/queue.py` defines `JobQueue`. The local adapter stores typed jobs in PostgreSQL, enforces organization/idempotency uniqueness, claims jobs, tracks attempts, retries failures and dead-letters exhausted jobs. `InMemoryJobQueue` makes the semantics deterministic in tests.

The current worker is not replaced by this PR. Future adapters can use SQS/EventBridge or a workflow service while preserving tenant scope, idempotency, retry, timeout, trace and dead-letter semantics.

## Model boundary

`apps/api/src/agentconstruct/model_gateway.py` defines `ModelGateway`. The fixture returns a typed `ModelResponse` with provider/model/prompt metadata, evidence and usage. The disabled adapter fails closed. Neither adapter can execute shell, Terraform, Kubernetes, cloud APIs or approvals.

An actual model provider must be added behind this interface and must preserve data-policy, timeout, usage, schema validation and provenance requirements.

## Scale evolution

At early scale, PostgreSQL remains a durable source of job state. When queue pressure, isolation or regional requirements justify it, the transport can move to SQS/EventBridge and workers can be split by job kind or cell. The API and business contracts should not change.

