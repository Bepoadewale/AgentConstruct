# Project Status

## Current state

**AgentConstruct V1 foundation — implemented locally; customer-AWS and GitHub repository discovery executed; workload/cloud runtime not executed.**

The GitHub repository has been renamed from `ai-platform-product-strategy` to `AgentConstruct`. It is a private commercial product repository.

## What is implemented

- Multi-organisation product domain and PostgreSQL persistence.
- Signed local development identity fixture, tenant checks and a production-facing JWT/JWKS verifier interface.
- Natural-language intent fixture → typed `WorkloadSpec`.
- Small, auditable AWS V1 catalogue that considers static, serverless, managed application, managed containers, VM, Kubernetes, managed-AI, CPU and GPU options. It rejects hard-constraint failures, reuses fixture-approved resources, and selects the lowest-complexity option in the configurable cheapest viable cost band.
- OPA policy, immutable plan hashes, independent production approval and durable audit.
- Tenant-scoped GitHub repository and AWS BYOC connection metadata. No reusable cloud credentials are stored.
- Durable local execution jobs processed by a separate bounded worker, with observed READY, FAILED and DESTROYED states.
- Web UI with editable region, data and budget constraints; Prometheus metrics, OpenTelemetry business traces, Tempo and Grafana dashboard provisioning.
- One governed REST API shared by the browser, a thin CLI, and a stdio MCP server. Agent clients can analyse, plan, compare, estimate, inspect, request eligible execution, and create a destroy plan; they cannot self-approve or receive cloud, shell, Terraform, Kubernetes, or secret access.
- GitHub App read-only discovery and repository intelligence. The selected `Bepoadewale/ai-platform-control-plane` repository was read through a short-lived installation token. The adapter can inspect safe repository metadata plus selected manifest files, persists credential-free runtime/framework/data/deployment hints, and refuses GitHub writes. Fixture webhook and reviewed-PR contracts remain simulated.
- Executed customer-AWS discovery connection: Terraform created an encrypted, versioned AgentConstruct state bucket, a DynamoDB lock table, GitHub OIDC control-plane identity, one read-only discovery role and one empty future-execution role. STS role chaining, real account inventory and Cost Explorer discovery were proved. No workload, network, database or compute resource was created.
- Customer AWS connection UI is implemented: a user can choose an AWS target, enter an account ID, open a CloudFormation Quick Create review, and queue server-side STS verification. Connection external IDs are protected through a control-plane secret-store interface; the browser and normal connection record never hold them. A separate runtime-role Terraform contract prevents the GitHub Actions role from being the production runtime identity. The public template host, runtime role and new customer Quick Create path have not been applied.
- A bounded Day-2 loop: deterministic latency evidence, a transparent replica recommendation, immutable `CHANGE` plan, independent production approval, durable worker, observed result and audit. It is local fixture evidence, not autonomous remediation or cloud monitoring.
- One selected AWS customer-plan review with durable submit, administrator approval/rejection, revision and explicit self-approval audit paths. Approval remains separate from execution.
- Terraform contracts for a separate state/lock/budget foundation and private VPC, EKS, ECR, RDS, Secrets Manager and IRSA runtime.
- Hardened Kubernetes and Argo CD desired-state contracts, External Secrets and artifact-storage contracts, plus planned private observability/recovery controls.
- Customer-facing infrastructure-plan records now have separate draft, submitted, approved and rejected revision states. They are distinct from bounded execution plans: approval never deploys. Workspace-administrator self-approval is explicitly recorded and tenant-scoped.

## Boundaries

- This does **not** deploy a workload into AWS or a customer account. One customer-AWS discovery connection is live and read-only; it is not deployment permission. Cost Explorer values are delayed billing data, not settled cost evidence.
- The local identity issuer, intent provider and execution target are fixtures. The JWKS adapter is implemented but not connected to an enterprise issuer.
- GitHub OAuth/install initiation, webhooks/reviewed desired-state PRs, GitHub-hosted OIDC assumption, profile-specific deployment permission, GitOps/Argo execution, enterprise IdP, external agent-client installation and billing are next work, not evidence.
- Role-aware local sign-in, `/me`, tenant-scoped workspace dashboards and an administrator-only pending-approval queue are implemented. Customer-plan submission, administrator approval/rejection and revision APIs/UI are locally implemented with separate signed fixtures; they are not enterprise sign-in. A deterministic two-session E2E script exercises developer submission, administrator decision, self-approval, rejection/revision, access denial and restart persistence without calling deployment endpoints.
- The local product flow can list a GitHub App installation's authorized repositories and branches, preserve the selected branch with the project, analyze safe repository manifests, and show/disconnect tenant-owned AWS connection metadata. Fixture mode is locally verified; the existing GitHub App adapter can perform the same repository/branch/manifest reads with a configured short-lived installation token. AWS remains read-only discovery only.
- The create-plan screen produces exactly one selected AWS customer-plan review draft. It binds the selected GitHub branch, AWS target, region, typed workload specification and available inventory snapshot. Prometheus-compatible metrics and Amazon Managed Grafana are required typed review components with private-access, coverage, limitation and estimated-cost information. The creator can submit the immutable review; an administrator can approve or reject the exact digest, including self-approval. Those decisions are local fixture evidence only and never deploy cloud resources.

## Next delivery sequence

1. Run a separately authorised cloud pilot: plan, create, smoke, failure proof, observability, cost query, destroy and absence verification.

## Clean-room reproducibility

Status: the earlier V1 proof completed two clean local-runtime cycles plus one rebuilt-image confirmation. This hardening change records two additional clean-room cycles with the durable worker and browser contract. Cached Docker images are not treated as runtime state.

## Cloud contract validation

On 2026-10-09, authenticated Terraform plans and identity-only applies completed for the AgentConstruct state foundation, control-plane identity and one customer discovery connection. The follow-up plans reported no changes. This is executed identity/discovery evidence only; no workload runtime was applied.

## Future operator workflow

CI validates Terraform and Kubernetes contracts. A manual GitHub Actions workflow defines future GitHub OIDC plan/apply/destroy gates, but it has not been dispatched. The real control-plane identity exists, but its hosted GitHub OIDC path has not yet been exercised.
