# Project Status

## Current state

**AgentConstruct V1 foundation — implemented locally; hosted customer-AWS discovery runtime executed; real customer-workload App Runner create → validate → destroy pilot executed twice and torn down.**

The GitHub repository has been renamed from `ai-platform-product-strategy` to `AgentConstruct`. It is a private commercial product repository.

## What is implemented

- Multi-organisation product domain and PostgreSQL persistence.
- Signed local development identity fixture, tenant checks and a production-facing JWT/JWKS verifier interface.
- Natural-language intent fixture → typed `WorkloadSpec`.
- Small, auditable AWS V1 catalogue that considers static, serverless, managed application, managed containers, VM, Kubernetes, managed-AI, CPU and GPU options. It rejects hard-constraint failures, reuses fixture-approved resources, and selects the lowest-complexity option in the configurable cheapest viable cost band.
- OPA policy, immutable plan hashes, independent production approval and durable audit.
- Tenant-scoped GitHub repository and AWS BYOC connection metadata. No reusable cloud credentials are stored.
- Durable local execution jobs processed by a separate bounded worker, with observed READY, FAILED and DESTROYED states.
- Web UI with editable region, data, budget, environment, availability, workload, access and assumption controls; Prometheus metrics, OpenTelemetry business traces, Tempo and Grafana dashboard provisioning.
- One governed REST API shared by the browser, a thin CLI, and a stdio MCP server. Agent clients can analyse, plan, compare, estimate, inspect, request eligible execution, create fixture desired-state PR contracts, and create a destroy plan; they cannot self-approve, merge GitHub PRs, or receive cloud, shell, Terraform, Kubernetes, or secret access.
- GitHub App read-only discovery, repository intelligence and local webhook workflow contract. The selected `Bepoadewale/ai-platform-control-plane` repository was read through a short-lived installation token. The adapter can inspect safe repository metadata plus selected manifest files, persists credential-free runtime/framework/data/deployment hints, and refuses GitHub writes. Signed fixture webhooks now persist installation state and deduplicated deliveries; reviewed-PR publication remains simulated.
- Executed customer-AWS discovery connection: Terraform created an encrypted, versioned AgentConstruct state bucket, a DynamoDB lock table, GitHub OIDC control-plane identity, one read-only discovery role and one empty future-execution role. STS role chaining, real account inventory and Cost Explorer discovery were proved. No workload, network, database or compute resource was created.
- Customer AWS connection UI is implemented and live-verified through an AWS-hosted App Runner runtime: a user can choose an AWS target, enter an account ID, open a CloudFormation Quick Create review, and queue server-side STS verification. Connection external IDs are protected through a control-plane secret-store interface; the browser and normal connection record never hold them. A separate App Runner runtime IAM role prevents the GitHub Actions role from being the production runtime identity. The public CloudFormation template host is applied and verified as a versioned S3 object.
- A bounded Day-2 loop: deterministic latency evidence, a transparent replica recommendation, immutable `CHANGE` plan, independent production approval, durable worker, observed result and audit. It is local fixture evidence, not autonomous remediation or cloud monitoring.
- One selected AWS customer-plan review with durable submit, administrator approval/rejection, editable draft/rejected constraint revisions, filtered administrator review queues, rich review evidence and explicit self-approval audit paths. Approval remains separate from execution.
- Approved customer-plan revisions can be explicitly executed as bounded local dry runs. The trusted worker independently observes READY, FAILED or DEGRADED evidence, ties each local environment back to the approved revision/digest, and supports a governed local destroy request/approval/observed-destroy path. This is local fixture execution only and does not create or delete AWS resources.
- Local dry-run environments now persist customer-facing deployment outputs and observed resource inventory as first-class records. The review/API/UI show outputs such as application URL, App Runner service ARN, log group and Grafana dashboard reference plus observed resources and statuses. Destroy keeps the historical records and marks them `DESTROYED`.
- Approved customer-plan revisions can also create a persisted fixture desired-state PR publication. The package binds the exact approved digest, selected repository/branch, selected architecture profile and profile-specific delivery contract. A workspace administrator can record local fixture check state such as `CHECKS_PASSED`, but AgentConstruct still does not write GitHub, publish real checks, merge code or deploy infrastructure.
- Approved `aws-app-runner` customer-plan revisions can render a plan-only Terraform deployment contract. The UI/API preview includes service, source/ECR boundary, IAM, environment variables, secret references, HTTPS assumptions, Prometheus/Grafana monitoring, required tags, account, region and exact plan digest. It is offline validation only: no authenticated Terraform plan, apply, destroy, AWS API call or workload deployment occurs.
- Approved customer-plan revisions can run a workspace-administrator-only local cloud-readiness preflight. It checks exact digest, policy, Terraform contract, no apply command, expected account, allowed region, tags, budget, reviewed PR state, runtime identity and dry-run/plan-only mode, then records a blocked or ready-for-future-plan result. This is guardrail evidence only; it does not execute cloud actions.
- Workspace administrators can now record a Terraform plan-only review from the approved digest, generated App Runner contract and cloud-readiness preflight. Local mode records the permitted `terraform init`/`terraform plan` command shape and keeps apply unavailable. Authenticated mode is gated behind explicit request approval plus `ALLOW_CLOUD_PLAN=true`; no authenticated AWS plan was executed in this PR.
- Terraform contracts for a separate state/lock/budget foundation and private VPC, EKS, ECR, RDS, Secrets Manager and IRSA runtime.
- Hardened Kubernetes and Argo CD desired-state contracts, External Secrets and artifact-storage contracts, plus planned private observability/recovery controls.
- Customer-facing infrastructure-plan records now have separate draft, submitted, approved and rejected revision states. They are distinct from bounded execution plans: approval never deploys. Workspace-administrator self-approval is explicitly recorded and tenant-scoped.

## Boundaries

- Routine product operation still does **not** deploy a customer workload into AWS or a customer account. Customer-AWS discovery is live and read-only; it is not deployment permission. Customer-plan dry runs execute only against the local fixture worker. PR #42 separately executed and destroyed a guarded App Runner customer workload pilot twice using scripts/Terraform evidence. The hosted App Runner runtime currently uses fixture sign-in, fixture policy and ephemeral SQLite, so it is validation/demo infrastructure rather than production SaaS persistence. Cost Explorer values are delayed billing data, not settled cost evidence.
- Terraform plan-only review records are governance evidence unless a future operator deliberately enables and runs authenticated plan mode. They are not apply, destroy or workload-readiness evidence.
- The local identity issuer, intent provider and execution target are fixtures. The JWKS adapter is implemented but not connected to an enterprise issuer.
- GitHub OAuth/install initiation, real public webhook delivery, live reviewed desired-state PR writes/checks, GitHub-hosted OIDC assumption, profile-specific deployment permission, GitOps/Argo execution, enterprise IdP, external agent-client installation and billing are next work, not evidence.
- Role-aware local sign-in, `/me`, tenant-scoped workspace dashboards and administrator-only review queues are implemented for pending, approved, rejected and self-approved plan revisions. Customer-plan submission, administrator approval/rejection and revision APIs/UI are locally implemented with separate signed fixtures; they are not enterprise sign-in. A deterministic two-session E2E script exercises developer submission, administrator decision, self-approval, rejection/revision, access denial, fixture PR/check review, App Runner Terraform rendering, ready preflight, Terraform plan-only review, approved local dry-run execution, readiness failure, governed local destroy and restart persistence without touching AWS.
- The local product flow can list a GitHub App installation's authorized repositories and branches, preserve the selected branch with the project, analyze safe repository manifests, and show/disconnect tenant-owned AWS connection metadata. Fixture mode is locally verified; the existing GitHub App adapter can perform the same repository/branch/manifest reads with a configured short-lived installation token. AWS remains read-only discovery only.
- The create-plan screen produces exactly one selected AWS customer-plan review draft. It binds the selected GitHub branch, AWS target, region, typed workload specification and available inventory snapshot. The creator can revise editable constraints before submission or after rejection, with a new digest and visible diff. Prometheus-compatible metrics and Amazon Managed Grafana are required typed review components with private-access, coverage, limitation and estimated-cost information. The creator can submit the immutable review; an administrator can inspect requester/repository/AWS target/digest/policy/monitoring/cost/risk evidence and approve or reject the exact digest, including self-approval. After approval, a separate local dry-run button queues the fixture executor and shows observed environment health, estimate and destroy state. None of those decisions or dry runs deploy cloud resources.
- `make seed-demo-data` can populate a fresh local workspace with realistic draft, submitted, approved, rejected, self-approved and dry-run records for hand demos. It uses only the local API and fixture executor.
- The generated App Runner Terraform contract preview appears only after approval and remains labeled `PLAN_ONLY_NOT_APPLIED`.
- The cloud-readiness preflight appears only after approval for workspace administrators and remains labeled local/preflight-only. In the local fixture demo, an administrator can record reviewed PR/check state and enable the runtime-identity checkbox to produce `READY_FOR_AUTHORIZED_CLOUD_PLAN`; this remains governance evidence only, not cloud execution.

## Next delivery sequence

1. Replace hosted fixture sign-in/policy/ephemeral SQLite with production identity, OPA and durable PostgreSQL for the AWS-hosted control plane.
2. Add real App Runner execution from the approved-plan UI/API using the output/resource inventory model.
3. Add customer workload execution history with attempts, Terraform status, outputs, created resources, destroy proof and evidence export.

## Clean-room reproducibility

Status: the earlier V1 proof completed two clean local-runtime cycles plus one rebuilt-image confirmation. This hardening change records two additional clean-room cycles with the durable worker and browser contract. Cached Docker images are not treated as runtime state.

## Cloud contract validation

On 2026-10-09, authenticated Terraform plans and identity-only applies completed for the AgentConstruct state foundation, control-plane identity and one customer discovery connection. On 2026-10-13, Terraform applied the hosted App Runner control-plane runtime, ECR repository, runtime IAM role and runtime signing secret. The hosted runtime assumed a temporary customer read-only discovery role, recorded a live inventory snapshot, then the temporary customer stack/role and per-connection ExternalId secret were deleted. This is executed control-plane/discovery evidence only; no customer workload runtime was applied.

## Future operator workflow

CI validates Terraform and Kubernetes contracts. A manual GitHub Actions workflow defines future GitHub OIDC plan/apply/destroy gates, but it has not been dispatched. The real control-plane identity exists, but its hosted GitHub OIDC path has not yet been exercised.
