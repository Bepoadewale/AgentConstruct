# Implementation Status

## Executed locally

| Capability | Evidence |
| --- | --- |
| Intent to typed specification | Provider interface, deterministic fixture, schema validation, provenance and material follow-up questions |
| Architecture and cost proposal | Constrained AWS V1 candidate planner: hard-constraint rejection, fixture inventory reuse, component cost ranges, complexity scores, rejected alternatives and upgrade triggers |
| Governance | Live OPA policy, immutable SHA-256 plan hash, independent approval and audit |
| Durable state | PostgreSQL in Compose; SQLite only in fast unit tests |
| Customer AWS discovery | Executed: Terraform-created read-only discovery role, permissionless future-execution role, GitHub OIDC control-plane identity, STS chain, live inventory and Cost Explorer query. AgentConstruct stores only connection metadata and a credential-free inventory snapshot. |
| Customer AWS Quick Create | Implemented: UI target picker/account-ID flow, API setup contract, durable server-side STS verification jobs, encrypted local / Secrets Manager production ExternalId contract, and credential-free inventory storage. The CloudFormation template is authenticated-validated. Hosting the versioned public template, creating the separate runtime identity, and using this new UI path against a new account remain unexecuted. |
| GitHub repository discovery and intelligence | Executed: the selected GitHub App installation issued a short-lived token to read `Bepoadewale/ai-platform-control-plane` metadata. Implemented: safe manifest analysis for runtime, framework, database, secret and deployment hints; persisted repository-analysis records; planner/review binding. The live adapter refuses write, PR publication and webhook processing. |
| Connection experience | Local UI/API lists deterministic GitHub App installations, permitted repositories and branches; it persists the selected branch and credential-free repository analysis with a project. The existing live adapter can list configured-installation repositories, branches and selected manifests using a short-lived token. AWS target detail/status and disconnect are tenant-scoped and credential-free. |
| One AWS customer-plan review | A local typed review draft binds repository branch, AWS target/region, workload spec, cost, security and policy findings. It presents one selected AWS design, never a customer-facing alternatives list. Draft and rejected reviews can create new edited constraint revisions with visible diffs before submission. Prometheus-compatible metrics and Amazon Managed Grafana are mandatory typed components with coverage, access boundary, limitations and estimated monitoring cost. |
| Customer-plan decision workflow | Creator-only submission validates the typed AWS review and freezes its digest. Workspace administrators approve or reject only the submitted digest; rejection requires a reason; rejected plans can create a new immutable draft revision from explicit user constraints. Administrator self-approval is explicitly recorded. Filtered review queues cover pending, approved, rejected and self-approved revisions. Every path is approval-only and never deploys. |
| Customer-plan local dry run | Approved customer-plan revisions can be explicitly queued into the bounded local fixture executor. Environments record the originating revision/digest, execution mode, estimated cost and observed READY/FAILED/DEGRADED state. Production destroy uses the existing destroy plan, administrator approval and observed DESTROYED path. No AWS resources are created or deleted. |
| Customer-plan E2E proof | Separate local developer and administrator HTTP sessions prove submission, administrator approval, self-approval, rejection/revision, stale-digest rejection, developer/tenant denial, approved-plan local dry-run execution, readiness failure, governed local destroy, audit evidence and persistence after API restart. Browser controls are contract-checked against the served UI. |
| Local execution | API persists a `QUEUED` job; a separate trusted worker invokes only the fixed fixture executor and records READY, FAILED or DESTROYED evidence |
| Day-2 change loop | Deterministic latency evidence → explanation → immutable `CHANGE` plan → production approval → durable worker → observed recovery and audit |
| Customer decision view | Browser renders one selected AWS plan, with its fixture cost range, security, Prometheus/Grafana contract, assumptions, risks and deployment boundary; internal alternatives remain planner evidence only |
| Incident evidence | PostgreSQL persists local degraded-health incidents and the recommendation lifecycle from proposed to applied/resolved |
| Identity boundary | Local signed-token fixture plus an unconfigured JWT/JWKS verifier interface for a future trusted issuer |
| Workspace views | Separate signed local developer and administrator fixture identities; backend-enforced current-user, tenant-scoped dashboard and administrator-only review APIs; browser sign-in/sign-out, filtered administrator queues, rich review evidence, explicit approved-not-deployed banners and seedable demo records |
| Audit evidence | Human-readable audit evidence endpoint and UI timeline with actor, role, action label, revision, digest, decision reason and export-ready structure for governance review |
| UI and monitoring | Plain JavaScript browser UI with editable region/data/budget/environment/availability/workload/access constraints, assumption decisions and revision diff display; `/metrics`, Prometheus, business OTel spans, Tempo and Grafana datasources/dashboard for request, plan-policy and observed-execution outcomes |
| Agent clients | Authenticated REST API, thin CLI, and stdio MCP server. They use the same API and do not expose approval, cloud credentials, shell, Terraform, Kubernetes, or secrets. The full local Compose proof exercises MCP tool discovery. |

## Simulated

- Natural-language understanding uses deterministic parsing, not a paid model.
- The default planner inventory and pricing remain local fixtures. The separately recorded customer discovery snapshot is live, read-only evidence; it does not grant deployment permission.
- Customer-plan dry-run deployment, destroy and Day-2 change application are bounded local fixtures, not AWS, Terraform, Docker or Kubernetes execution.
- The selected AWS review, cost and monitoring configuration are deterministic local planning fixtures, not live AWS pricing, managed Prometheus/Grafana provisioned resources, or a deployed workload.
- Local signed JWT, developer/administrator sign-in, and workspace dashboards are development fixtures. The JWKS verifier adapter is code, not enterprise OIDC execution evidence.

## Roadmap only

GitHub OAuth/install initiation, GitHub-hosted control-plane OIDC assumption, GitHub webhooks/reviewed PR publication, profile-specific Terraform rendering/deployment, real GitOps/Argo execution, enterprise identity, external agent-client installation, subscription billing, model runtime controls and automated remediation.

## Statically validated cloud contract

Terraform describes separate state/lock/budget guardrails plus a private VPC, EKS, ECR, RDS, Secrets Manager and IRSA foundation. Kubernetes describes hardened API replicas, probes, a PDB, default-deny policy and placeholder-only secret/image references. Argo CD describes reviewed desired-state reconciliation. Terraform format, offline-backend initialisation and validation passed. None of those resources or controllers has run in AWS.

GitHub Actions runs lint, tests, dependency audit, secret scan, OPA tests, SBOM, filesystem scan, image build, Terraform/Kubernetes contract checks, realistic demo seeding and the full local proof (simple, complex, degraded, Day-2, customer-plan dry-run/destroy, policy/readiness failure, traces and MCP tool discovery). A manual GitHub OIDC workflow has exact plan/apply/destroy confirmations and an account check, but it has not been dispatched. The live control-plane role was verified locally through a temporary owner chain that was removed afterward; the GitHub OIDC route remains unexecuted.
