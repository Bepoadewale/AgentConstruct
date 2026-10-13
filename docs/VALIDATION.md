# Validation

## Local V1 clean-room evidence

Date: 2026-10-08. Environment: macOS, Docker Desktop and Python 3.12.

Two clean project-runtime cycles were completed, followed by a third confirmation that rebuilt the Docker images. Before each cycle, `make clean-local` removed only AgentConstruct containers, network, PostgreSQL volume, virtual environment and `.local` data. The first two cycles retained Docker images; the third used `docker compose up -d --build`. No prior runtime state, database data or local files were needed.

Each cycle ran:

```bash
make bootstrap-local
make smoke
make demo
make demo-failure
make demo-readiness-failure
make trace-check
make verify
make opa-test
make clean-local
```

Results from every cycle:

- Smoke checks found the API, fixture executor, PostgreSQL, OPA, Prometheus, Grafana, Tempo and OpenTelemetry Collector ready.
- The success demo created staging and production environments, observed two `READY` results, required a different operator to approve production, destroyed production through the governed path and wrote audit events.
- The budget failure demo was denied by live OPA before execution.
- The readiness failure demo made the bounded executor report failure. The observer recorded `FAILED`; it did not assume `READY` because a command returned.
- Tempo returned traces for `agentconstruct-api` after the demo.
- `ruff` passed; `pytest` passed **12 tests**; `opa test` passed **3/3**; `docker compose config --quiet` passed.
- Each cleanup confirmed that project containers and `.local` data were absent. No broad Docker cleanup command was used.

This evidence is local only. No AWS resources, customer GitHub installation, customer credentials or enterprise identity provider were used.

## Static cloud-contract evidence

On 2026-10-08, `make terraform-validate` passed for the bootstrap and pilot Terraform roots. `make kubernetes-render` rendered the Kubernetes contract. The render did not contact or apply to a Kubernetes cluster. No AWS authenticated plan, apply, image push, Argo reconciliation or cloud destroy occurred.

PR 3 adds strict CI validation for those contracts and a manual GitHub OIDC operator workflow. Neither was dispatched against AWS during this readiness phase.

## V1 hardening clean-room evidence

Date: 2026-10-08. Environment: macOS, Docker Desktop and Python 3.12.

The first hardening cycle ran from a removed AgentConstruct Compose stack and PostgreSQL volume. It rebuilt the API and new worker image, then ran:

```bash
make bootstrap-local
make smoke
make browser-contract
make demo
make demo-failure
make demo-readiness-failure
make trace-check
make verify
make opa-test
make terraform-validate
make kubernetes-render
```

Results:

- The separate worker started and processed durable queued deployment and destroy jobs.
- The browser contract found the editable region, data-classification and budget controls in the real served UI.
- The success flow recorded two `READY` environments, an independently approved production destroy and 12 audit events.
- Budget denial and readiness failure both behaved as expected; the observer recorded `FAILED` rather than assuming success.
- Tempo received API and worker business spans.
- `ruff` passed; `pytest` passed **14 tests**; OPA passed **3/3**; Terraform bootstrap and pilot validation passed; Kubernetes rendering passed.

This is still local/static evidence only. The JWKS adapter, External Secrets, GitHub App delivery, ALB controller, AWS resources and real GitOps reconciliation were not executed.

A second clean cycle repeated the same commands from a removed Compose stack and ended with `make clean-local`. It again passed the browser contract, success, policy-denial, readiness-failure, trace, lint, test and OPA checks; the project Compose containers and local data were absent after cleanup.

## Minimum-necessary planner clean-room evidence

Date: 2026-10-09. Environment: macOS, Docker Desktop, Python 3.12, Terraform and kubectl.

Two clean cycles were completed after the planner change. Both began with `make clean-local`, rebuilt the local stack through `make bootstrap-local`, and ended with `make clean-local`.

Each cycle ran:

```bash
make bootstrap-local
make smoke
make browser-contract
make demo
make demo-failure
make demo-readiness-failure
make trace-check
make verify
make opa-test
make terraform-validate
make kubernetes-render
make clean-local
```

Results from both cycles:

- API, worker, fixture executor, PostgreSQL, OPA, Prometheus, Grafana and Tempo became ready.
- The browser contract passed.
- The canonical governed deployment completed with two observed `READY` environments and a governed destroy. The policy and readiness failure demos remained denied/failed as designed.
- Tempo received traces. Ruff passed. Pytest passed **28 tests**. OPA passed **3/3**. Both Terraform roots formatted and validated with `init -backend=false`. Kubernetes rendered without applying.
- Cleanup removed the project Compose containers, network, PostgreSQL volume, virtual environment and `.local` data.

The first fresh bootstrap exposed a PostgreSQL race between the API and worker creating the migration table. The code now takes a PostgreSQL transaction-scoped advisory lock before migrations. Both recorded cycles passed with that fix.

This evidence proves local planner and runtime behavior only. AWS inventory/pricing remain deterministic fixtures; no AWS account, billable resource, GitHub App, or customer role was contacted.

## Governed agent-interface validation

Date: 2026-10-09. The CLI and stdio MCP server were tested as thin API clients, not as alternate execution authorities.

- The MCP catalogue exposed analysis, planning, comparison, estimate, status, audit, eligible-execution, and destroy-plan operations.
- It deliberately exposed no approval, cloud credential, secret, shell, Terraform or Kubernetes tool.
- CLI request construction preserved the caller's project, repository, cloud-connection reference and idempotency key.
- Unit validation passed with **33 tests**.

Two clean Compose cycles then passed with the installed `agentconstruct-mcp` entry point included in each cycle. Each cycle passed smoke, browser contract, canonical demo, policy failure, readiness failure, Tempo trace check, Ruff, all then-current 32 tests, OPA 3/3, Terraform `fmt`/offline-backend `init`/`validate`, Kubernetes render, MCP `tools/list`, and scoped cleanup. The final 33-test run added a tenant-scoped agent-read test. The MCP contract confirmed the tools were available without an approval tool.

## Governed Day-2 loop clean-room evidence

Date: 2026-10-09. Environment: macOS, Docker Desktop, Python 3.12, Terraform and kubectl.

Two clean cycles began and ended with `make clean-local`. Each rebuilt Compose from scratch and ran:

```bash
make bootstrap-local
make smoke
make browser-contract
make demo
make demo-day2
make demo-failure
make demo-readiness-failure
make trace-check
make verify
make opa-test
make terraform-validate
make kubernetes-render
printf '%s\n' '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' | AGENTCONSTRUCT_TOKEN=fixture-token .venv/bin/agentconstruct-mcp
make clean-local
```

Both cycles passed. The Day-2 demo created a production environment, read deterministic high-latency evidence, created a `CHANGE` plan, required a separate operator to approve the exact plan, observed the fixed local change result, and then used the existing governed destroy path. Ruff passed, pytest passed **36 tests**, OPA passed **3/3**, both Terraform roots formatted and validated with `init -backend=false`, Kubernetes rendered without applying, and the MCP catalogue included the non-mutating recommendation and governed change-plan tools.

This is local fixture evidence only. The telemetry, cost delta and fixed change endpoint do not represent a cloud metric source, actual AWS cost, customer workload, or autonomous remediation.

## Customer planning and degraded-state clean-room evidence

Date: 2026-10-09. Environment: macOS, Docker Desktop, Python 3.12, Terraform and kubectl.

Two clean Compose cycles began and ended with `make clean-local`. Each rebuilt the stack and ran:

```bash
make bootstrap-local
make smoke
make browser-contract
make demo-simple
make demo-complex
make demo-degraded
make demo-day2
make demo
make demo-failure
make demo-readiness-failure
make trace-check
make verify
make opa-test
make terraform-validate
make kubernetes-render
make clean-local
```

Both cycles passed. `demo-simple` selected `aws-app-runner` for the low-traffic container API; `demo-complex` selected `aws-eks-governed` only for the explicit multi-service GPU/Kubernetes request. `demo-degraded` recorded `DEGRADED` state and an open PostgreSQL incident. `demo-day2` persisted a recommendation, required the separate operator to approve the production `CHANGE` plan, observed the fixed local outcome, then resolved the incident. Browser, policy, readiness-failure, traces, Ruff, pytest (**38 tests**), OPA (**3/3**), Terraform offline validation and Kubernetes rendering also passed.

This remains local fixture/static evidence. Neither App Runner, EKS, GPU capacity, Terraform apply nor an AWS account was executed.

## Governed integration-contract clean-room evidence

Date: 2026-10-09. Environment: macOS, Docker Desktop, Python 3.12, Terraform and kubectl.

Two clean Compose cycles began and ended with `make clean-local`. Each cycle ran:

```bash
make bootstrap-local
make smoke
make browser-contract
make demo-simple
make demo-complex
make demo-degraded
make demo-day2
make demo
make demo-failure
make demo-readiness-failure
make trace-check
make verify
make opa-test
make terraform-validate
make kubernetes-render
make clean-local
```

Both cycles passed. The simple workload used `aws-app-runner`; the complex workload used `aws-eks-governed`; each local execution carried the selected profile into the bounded executor. Browser, policy and readiness-failure paths passed. Tempo received traces. Ruff passed, pytest passed **44 tests**, OPA passed **3/3**, both Terraform roots formatted and validated with `init -backend=false`, and Kubernetes rendered without being applied. The final cleanup confirmed that no project Compose container, volume, virtual environment or local state remained.

The GitHub desired-state pull-request/check contract, GitHub webhook contract and customer AWS OIDC/STS role contract are tested as deterministic fixtures only. No GitHub App installation, webhook, repository write, AWS credentials, AWS role assumption, Terraform apply, Argo reconciliation or Kubernetes cluster was contacted.

## Final product-proof clean-room evidence

Date: 2026-10-09. Environment: macOS, Docker Desktop, Python 3.12, Terraform and kubectl.

Two clean cycles began and ended with `make clean-local`. Each cycle rebuilt the Compose stack and ran the full customer and agent-client proof:

```bash
make bootstrap-local
make smoke
make browser-contract
make demo-simple
make demo-complex
make demo-degraded
make demo-day2
make demo
make demo-failure
make demo-readiness-failure
make trace-check
make verify
make opa-test
make terraform-validate
make kubernetes-render
printf '%s\n' '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' | AGENTCONSTRUCT_TOKEN=fixture-token .venv/bin/agentconstruct-mcp
make clean-local
```

Both cycles passed. The browser contract and all three planning stories passed: a small request selected App Runner, a complex GPU/Kubernetes request selected EKS, and degraded Day-2 evidence created a governed change with an independent approval. Policy denial and observed readiness failure passed. Tempo received traces; the MCP catalogue exposed governed tools with no approval tool. Ruff passed, pytest passed **44 tests**, OPA passed **3/3**, both Terraform roots formatted and validated offline, and Kubernetes rendered without an apply. Final cleanup left no project containers, volume, virtual environment or local state.

This is local and static evidence. It is not AWS execution, customer-cloud access, external identity, GitHub App delivery, live agent-client integration, actual cloud billing, or a cloud-pilot claim.

## Customer AWS connection contract validation

Date: 2026-10-09. `make lint`, `make test`, and `make terraform-validate` passed. Pytest passed **46 tests**. Terraform formatted, initialised with `-backend=false`, and validated the bootstrap, customer-connection and pilot roots.

The new customer-connection root is an identity-only contract: a read-only discovery role and an empty future-execution role. Static tests verify that the discovery policy contains no create, update, delete, secret-read or execution permission and that apply/destroy require a separate confirmation string.

## Executed customer AWS discovery connection

Date: 2026-10-09. Environment: macOS, Terraform, AWS CLI and the authenticated customer AWS account.

The following identity-only Terraform roots were planned against the authenticated account and then applied after review:

- `agentconstruct-bootstrap`: encrypted/versioned AgentConstruct state bucket, public-access block and DynamoDB lock table (**5 added**).
- `management-identity`: GitHub OIDC provider, `agentconstruct-control-plane-github`, and its narrowly scoped `sts:AssumeRole` policy (**3 added**).
- `customer-connection`: `agentconstruct-adewale-primary-aws-discovery`, its read-only inventory/cost policy, and `agentconstruct-adewale-primary-aws-execution` with **no permissions** (**3 added**).

The state for all three roots was migrated to the new encrypted bucket and DynamoDB lock table. Follow-up authenticated plans reported **No changes**. A temporary customer-owner trust path was used only to prove the two-hop STS chain, then removed by Terraform. The final control-plane trust policy permits only GitHub OIDC for `Bepoadewale/AgentConstruct` on `main`.

The verified STS path was: temporary owner verification identity → AgentConstruct control-plane role → customer read-only discovery role with an external ID. The discovery session returned one VPC, one ECR repository, six S3 buckets, and no EKS, ECS, RDS or App Runner workload. Cost Explorer returned daily unblended values for 2026-10-01 through 2026-10-08. Those values are recorded as delayed billing data, not settled billing.

The live result was stored through the running AgentConstruct API as a tenant-scoped, credential-free inventory snapshot with `live-read-only-sts-discovery` provenance and an audit event. No access key was created or stored. No application, VPC, compute, database, EKS, ECS, App Runner, GitOps, or other customer workload resource was deployed.

## Executed GitHub App read-only discovery

Date: 2026-10-09. The existing GitHub App `ai-platform-control-plane-pilot` was installed on the selected customer repository `Bepoadewale/ai-platform-control-plane`. AgentConstruct used the App private key only from the owner-protected local file, minted a short-lived installation token for installation `167128937`, and read the repository metadata: `main` is its default branch.

The local AgentConstruct API then created a tenant-scoped project connection, ran repository discovery through the live App adapter, and recorded an audit event. The adapter explicitly rejected a desired-state write. No token, private key, webhook secret, pull request, commit, repository setting, or customer code was written or stored. Webhooks and reviewed desired-state PR publication remain unexecuted.

## AWS Quick Create onboarding contract

Date: 2026-10-09. `aws cloudformation validate-template` authenticated successfully against the AWS account for `infrastructure/cloudformation/customer-discovery-role.yaml`. Validation created no stack, role, workload, or other AWS resource. The template defines one customer-side discovery role with an AgentConstruct control-plane trust principal, per-connection external ID, short sessions, and metadata-only policy. Unit tests also verify that it has no secret-value, S3-object, IAM pass-role, or create permission.

No authenticated plan was run. An eventual plan requires a real AgentConstruct control-plane IAM role ARN, unique external ID, dedicated encrypted state backend, and explicit customer approval. No IAM role, credential, workload, network or other AWS resource was created.

## AWS connection wizard contract

Date: 2026-10-09. The browser contract and unit tests cover the AWS target picker, account-ID validation, Quick Create handoff, and server-side verification endpoint. The verification adapter only uses STS `AssumeRole` in the control-plane process, verifies that the resulting account matches the requested account, and stores a credential-free inventory snapshot. Tests use a deterministic STS adapter; no new customer stack, public template bucket, or live UI verification occurred.

The public-template Terraform root uses a versioned S3 object key and permits public `GetObject` only under its `cloudformation/` prefix. It blocks public ACLs and all bucket listing. Its plan, apply and destroy commands are account-guarded; apply and destroy require an explicit confirmation string.

Date: 2026-10-13. An authenticated plan against AWS account `654654474502` completed with **7 to add, 0 to change, 0 to destroy**: the dedicated template bucket, ownership controls, versioning, encryption, narrowly scoped public-read policy, public-access configuration, and one hash-versioned YAML object.

The first non-interactive apply attempt failed safely because Terraform still requested interactive approval after the script-level confirmation. The script was fixed to pass `-auto-approve` only after the explicit `CONFIRM_TEMPLATE_HOST_APPLY=APPLY_AGENTCONSTRUCT_TEMPLATE_HOST` guard is present. A second apply completed with **7 added, 0 changed, 0 destroyed**.

Verification found that the first object upload had `x-amz-version-id: null` because S3 versioning completed after the object upload. The Terraform root was tightened so the object depends on bucket ownership controls, encryption and versioning. The object was tainted and re-applied, completing with **1 added, 0 changed, 1 destroyed** for the template object only.

Final evidence:

```text
customer_discovery_template_url = "https://agentconstruct-customer-templates-654654474502.s3.us-east-1.amazonaws.com/cloudformation/customer-discovery-role-0e3209bff02286acf582ec3ed73858266261b294ae0c7e0d30ae37550a8926b2.yaml"
bucket versioning = Enabled
bucket encryption = AES256
template object HTTP status = 200
template object x-amz-version-id = sRcSIAyRmBYcnqUEvImdK7MhtqQJ60xM
bucket root HTTP status = 403 AccessDenied
```

No customer workload, VPC, compute, database, Kubernetes, App Runner, GitOps, secret, or application resource was created by this template-host apply. This is AgentConstruct control-plane foundation only. The hosted runtime identity remains unexecuted because there is not yet an AgentConstruct runtime OIDC issuer.

## Customer-plan approval workflow clean-room evidence

Date: 2026-10-11. Environment: macOS, Docker Desktop, Python 3.12, Terraform, kubectl and the local fixture identities.

Two clean cycles began and ended with `make clean-local`. Each cycle ran the Compose bootstrap, smoke and browser-contract checks, the customer-plan two-session E2E, an API restart and persistence check, the simple/complex/degraded/Day-2 demos, both failure demonstrations, trace, lint, unit, OPA, Terraform and Kubernetes checks, and the MCP tool catalogue check.

```bash
make bootstrap-local
make smoke
make browser-contract
make customer-plan-e2e
docker compose restart api
make smoke
make customer-plan-persistence
make demo-simple && make demo-complex && make demo-degraded && make demo-day2
make demo && make demo-failure && make demo-readiness-failure
make trace-check && make verify && make opa-test
make terraform-validate && make kubernetes-render
printf '%s\n' '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' | AGENTCONSTRUCT_TOKEN=fixture-token .venv/bin/agentconstruct-mcp
make clean-local
```

Both cycles passed. The E2E proved that a developer can submit a FastAPI plan, cannot approve it, sees an administrator approval after an API restart, receives a persisted rejection reason, and can create revision 2. It also proved that a workspace administrator can submit and self-approve their own plan with the explicit self-approval policy and audit record. A cross-tenant read was denied; a stale digest and duplicate decision were rejected. The selected simple plan used App Runner and included Prometheus-compatible metrics plus Amazon Managed Grafana rather than EKS. Ruff passed, pytest passed **72 tests**, OPA passed **3/3**, all Terraform roots formatted and validated with `init -backend=false`, Kubernetes rendered without a cluster apply, Tempo received traces, and the MCP catalogue was available. Final cleanup left no project Compose container, volume, virtual environment or local state.

This is locally verified fixture evidence. It is not live GitHub authorization, live AWS role assumption, customer-cloud resource creation, Grafana/Prometheus deployment, or a production deployment claim.

## Seeded local product demo and browser proof

Date: 2026-10-12. Environment: macOS, Docker Desktop, Python 3.12 and local fixture identities.

The PR 5 local proof ran the expanded customer-plan workflow and seeded demo data that a browser user can inspect immediately:

```bash
node --check apps/web/app.js
.venv/bin/python -m ruff check apps/api/src tests scripts
.venv/bin/python -m pytest -q
make clean-local
make bootstrap-local
make smoke
make browser-contract
make customer-plan-e2e
make seed-demo-data
docker compose restart api
make smoke
make customer-plan-persistence
make trace-check
make verify
docker compose config --quiet
```

Results:

- JavaScript syntax check passed.
- Ruff passed.
- Pytest passed **80 tests**.
- Clean local bootstrap passed.
- Smoke and browser-contract checks passed.
- The customer-plan E2E proved developer submission, administrator approval, administrator rejection, administrator self-approval, developer approval denial, stale digest denial, cross-tenant denial, local dry-run execution, observed readiness failure, governed local destroy, and audit evidence.
- `make seed-demo-data` created realistic local records for a developer, administrator, GitHub fixture, AWS fixture, draft plan, submitted plan, approved plan, rejected plan, administrator self-approved plan, and approved-plan dry-run environments.
- API restart persistence passed after seeding and dry-run execution.
- Tempo trace check passed.
- `make verify` passed after the restart.
- Docker Compose configuration validated.

An initial seed prompt containing the phrase `no GPU requirement` exposed a deterministic keyword ambiguity in the local fixture parser. The seed prompt was rewritten before final validation so the simple demo remains a non-GPU, non-EKS plan.

This is local fixture evidence only. No AWS resources, Terraform apply, Kubernetes apply, GitHub write, pull request, GitOps sync, or production deployment occurred.

## Local GitHub App workflow contract

Date: 2026-10-12. Environment: macOS, Docker Desktop, Python 3.12 and local fixture identities.

This validation added a local GitHub App webhook workflow contract without enabling repository writes or public GitHub callback delivery.

```bash
.venv/bin/python -m ruff check apps/api/src tests scripts
.venv/bin/python -m pytest tests/test_connection_experience.py tests/test_integration_contracts.py -q
node --check apps/web/app.js
.venv/bin/python -m pytest -q
docker compose up -d --build
make smoke
make browser-contract
docker compose config --quiet
git diff --check
```

Results:

- Focused GitHub/integration tests passed: **13 passed**.
- Full pytest suite passed: **85 passed**.
- Browser contract passed against the rebuilt local UI.
- The local webhook endpoint verifies fixture signatures, rejects invalid signatures, deduplicates delivery IDs, records replay attempts as duplicates, persists installation state, and exposes installation/repository/branch status in the UI.
- Tested webhook states include connected installation, revoked installation, repository access change, branch update and missing permission.

This is local fixture evidence. It does not prove that GitHub delivered a public webhook, create a pull request, write a branch, publish checks, merge code, or deploy infrastructure.

## Fixture desired-state PR publication

Date: 2026-10-12. Environment: macOS, Docker Desktop, Python 3.12 and local fixture identities.

This validation added a persisted fixture desired-state PR publication path for approved customer-plan revisions.

```bash
.venv/bin/python -m ruff check apps/api/src tests scripts
.venv/bin/python -m pytest tests/test_customer_plan_review.py tests/test_product.py::test_approved_plan_can_only_shape_a_simulated_reviewed_desired_state_pull_request -q
node --check apps/web/app.js
.venv/bin/python -m pytest -q
docker compose up -d --build
make smoke
make browser-contract
docker compose config --quiet
git diff --check
```

Results:

- Focused customer-plan/publication tests passed: **12 passed**.
- Full pytest suite passed: **90 passed**.
- Browser contract passed against the rebuilt local UI.
- The desired-state publication path requires an approved customer-plan revision, exact digest, connected repository branch, and publishable GitHub App state.
- The generated fixture package includes App Runner/ECS/EKS-aware delivery contracts, required checks, the approved digest and the rule that AgentConstruct never merges customer code or desired state.
- Failure fixtures passed for stale digest, changed branch and revoked GitHub App installation.

This is local fixture evidence only. It did not create a GitHub branch, pull request, check run, merge, GitOps sync, Terraform plan/apply, AWS resource, or production deployment.

## App Runner plan-only Terraform renderer

Date: 2026-10-12. Environment: macOS, Python 3.12, local fixture identities and Terraform CLI.

This validation added an approved-plan to Terraform-contract renderer for the first real profile: `aws-app-runner`.

```bash
.venv/bin/python -m pytest tests/test_customer_plan_review.py -q
terraform fmt -recursive infrastructure/terraform
node --check apps/web/app.js
.venv/bin/python -m ruff check apps/api/src tests scripts
TF_DATA_DIR=/tmp/agentconstruct-tfvalidate-apprunner-renderer terraform -chdir=infrastructure/terraform/renderers/app-runner-plan init -backend=false -input=false
TF_DATA_DIR=/tmp/agentconstruct-tfvalidate-apprunner-renderer terraform -chdir=infrastructure/terraform/renderers/app-runner-plan validate
.venv/bin/python -m pytest -q
make terraform-validate
docker compose up -d --build
make smoke
make browser-contract
make verify
make opa-test
git diff --check
```

Results:

- Focused customer-plan tests passed: **15 passed**.
- Full pytest suite passed: **94 passed**.
- JavaScript syntax check passed.
- Ruff passed.
- App Runner renderer Terraform root initialized with `-backend=false` and validated successfully.
- `make terraform-validate` passed across the existing Terraform contracts plus the new App Runner renderer.
- Rebuilt Docker Compose services passed smoke and browser-contract checks.
- `make verify` passed: Ruff, **94 pytest tests**, and Compose config validation.
- OPA policy tests passed: **3/3**.
- `git diff --check` passed.
- The renderer requires an approved customer-plan revision and exact approved digest.
- A simple FastAPI plan renders an `aws-app-runner` contract, not an EKS contract.
- An EKS plan is rejected by the App Runner renderer.
- The approved digest is embedded in module inputs, environment variables, tags and file previews.
- The render payload exposes no apply command and is labeled `PLAN_ONLY_NOT_APPLIED`.

This is local/offline evidence only. It did not run authenticated `terraform plan`, `terraform apply`, `terraform destroy`, AWS APIs, GitHub writes, GitOps sync, Kubernetes commands, or production deployment.

## Cloud-readiness guardrails

Date: 2026-10-12. Environment: macOS, Docker Desktop, Python 3.12, Terraform CLI and local fixture identities.

This validation added a local preflight gate for future cloud actions.

```bash
.venv/bin/python -m pytest tests/test_customer_plan_review.py -q
node --check apps/web/app.js
.venv/bin/python -m ruff check apps/api/src tests scripts
.venv/bin/python -m pytest -q
terraform fmt -recursive infrastructure/terraform
make terraform-validate
docker compose up -d --build
make smoke
make browser-contract
make verify
make opa-test
git diff --check
```

Results:

- Focused customer-plan/preflight tests passed: **19 passed**.
- Full pytest suite passed: **98 passed**.
- JavaScript syntax check passed.
- Ruff passed.
- `make terraform-validate` passed.
- Rebuilt Docker Compose services passed smoke and browser-contract checks.
- `make verify` passed: Ruff, **98 pytest tests**, and Compose config validation.
- OPA policy tests passed: **3/3**.
- `git diff --check` passed.

The preflight stores a `would_deploy` preview and checklist for exact digest, policy, Terraform contract, no apply command, expected account, region, tags, budget, reviewed PR, runtime identity and dry-run/plan-only mode.

Failure fixtures proved wrong account, wrong region, missing tag, budget exceeded, stale digest, no reviewed PR and no runtime identity. This is local guardrail evidence only. It did not call AWS, run authenticated Terraform plan/apply/destroy, write GitHub, sync GitOps, or deploy a workload.

## Terraform plan-only review gate

Date: 2026-10-13. Environment: macOS, Python 3.12 virtualenv, local fixture identities.

This validation added an administrator-only Terraform plan-review record for approved App Runner customer-plan revisions.

```bash
.venv/bin/python -m pytest tests/test_customer_plan_review.py -q
.venv/bin/python -m ruff check apps/api/src tests scripts
node --check apps/web/app.js
.venv/bin/python -m pytest -q
make verify
```

Results:

- Focused customer-plan tests passed: **25 passed**.
- Ruff passed.
- JavaScript syntax check passed.
- Full pytest suite passed: **104 passed**.
- `make verify` passed: Ruff, **104 pytest tests**, and Compose config validation.

The tests prove administrator-only access, exact digest binding, App Runner contract requirement, cloud-readiness preflight requirement, failed-preflight blockers, local plan-only evidence, authenticated-mode `ALLOW_CLOUD_PLAN=true` gating and stale-digest rejection.

This is plan-review governance evidence only. It did not run authenticated `terraform plan`, `terraform apply`, `terraform destroy`, AWS APIs, GitHub writes, GitOps sync, Kubernetes commands or workload deployment.

## Local stability hardening: reviewed fixture PR to plan-only review

Date: 2026-10-13. Environment: macOS, Docker Desktop, Python 3.12 virtualenv, local fixture identities.

This validation made the post-approval cloud-readiness path reachable through product APIs and UI controls, not database edits.

```bash
.venv/bin/python -m py_compile scripts/customer_plan_e2e.py
.venv/bin/python -m pytest tests/test_customer_plan_review.py -q
.venv/bin/python -m ruff check apps/api/src tests scripts
node --check apps/web/app.js
.venv/bin/python -m pytest -q
docker compose up -d --build
make smoke
make browser-contract
make customer-plan-e2e
docker compose restart api
./scripts/smoke.sh
make customer-plan-persistence
make verify
make opa-test
```

Results:

- Customer-plan focused tests passed: **27 passed**.
- Ruff passed.
- JavaScript syntax check passed.
- Full pytest suite passed: **106 passed**.
- Docker Compose rebuilt API, worker and fixture-executor images.
- Smoke passed for API, worker, fixture executor, Prometheus, Grafana, Tempo and OPA.
- Browser contract passed and includes the new fixture PR check action.
- `make customer-plan-e2e` passed, including fixture desired-state PR creation, administrator-recorded `CHECKS_PASSED`, App Runner Terraform render, ready cloud-readiness preflight, Terraform plan-only review, local dry-run execution, readiness failure, governed local destroy and audit evidence.
- API restart plus `make customer-plan-persistence` passed.
- `make verify` passed: Ruff, **106 pytest tests**, and Compose config validation.
- OPA policy tests passed: **3/3**.

This is local product stability evidence only. It did not write GitHub, run authenticated Terraform, run `terraform apply`, create AWS resources, run Kubernetes, sync GitOps or deploy a workload.

## Demo data readiness seed

Date: 2026-10-13. Environment: macOS, Docker Desktop, Python 3.12 virtualenv, running local AgentConstruct stack.

```bash
.venv/bin/python -m py_compile scripts/seed_demo_data.py
make seed-demo-data
```

Results:

- The seed script created draft, submitted, approved, rejected and administrator self-approved customer-plan revisions.
- The approved seeded revision also created a fixture desired-state PR, recorded `CHECKS_PASSED`, rendered the App Runner Terraform contract, recorded `READY_FOR_AUTHORIZED_CLOUD_PLAN`, recorded `LOCAL_CONTRACT_PLAN_REVIEWED`, and queued observed local dry-run environments.
- The output boundary explicitly states no AWS resources, GitHub writes, authenticated Terraform plan/apply, Kubernetes or GitOps execution occurred.

## Administrator-gated readiness actions

Date: 2026-10-13. Environment: macOS, Docker Desktop, Python 3.12 virtualenv, running local AgentConstruct stack.

This validation made future cloud-readiness controls workspace-administrator-only. A developer can still create, submit and view plans, but cannot run the operator preflight or see the operator-only UI controls.

```bash
.venv/bin/python -m pytest tests/test_customer_plan_review.py -q
.venv/bin/python -m ruff check apps/api/src tests scripts
node --check apps/web/app.js
.venv/bin/python -m pytest -q
docker compose up -d --build
make smoke
make browser-contract
make customer-plan-e2e
make seed-demo-data
make verify
git diff --check
```

Results:

- Focused customer-plan tests passed: **27 passed**.
- Ruff passed.
- JavaScript syntax check passed.
- Full pytest suite passed: **106 passed**.
- Docker Compose rebuilt and started the local API, worker and fixture executor.
- Smoke passed for API, worker, fixture executor, Prometheus, Grafana, Tempo and OPA.
- Browser contract passed.
- `make customer-plan-e2e` passed, including developer submission, administrator decision, administrator self-approval, local dry-run execution, readiness failure, governed destroy and audit.
- `make seed-demo-data` created fixture records through the local API, including desired-state PR/check state, App Runner Terraform render, ready preflight, plan-only review and local dry-run environments.
- `make verify` passed: Ruff, **106 pytest tests**, and Compose config validation.
- `git diff --check` passed.

This is local product hardening evidence only. It did not write GitHub, run authenticated Terraform, run `terraform apply`, create AWS resources, run Kubernetes, sync GitOps or deploy a workload.

## Local proof developer experience and clean-room repeat

Date: 2026-10-13. Environment: macOS, Docker Desktop, Python 3.12, clean local Compose volumes.

This validation added `make help` and `make local-proof`, updated stale current-state documentation, and repeated the local product proof twice from a clean state. A later hardening update made `make local-proof` self-contained by depending on `make bootstrap-local`.

Warm-stack command check:

```bash
make help
make local-proof
git diff --check
```

Clean-room repeat:

```bash
make local-proof
make clean-local
make local-proof
make clean-local
```

Results:

- `make help` printed the local operator command list and cloud-safety boundary.
- Both cold cycles rebuilt the Python virtualenv and Docker Compose services from scratch.
- Both cold cycles passed service readiness for API, worker, fixture executor, Prometheus, Grafana, Tempo and OPA.
- Both cold cycles passed the browser contract.
- Both cold cycles passed `make customer-plan-e2e`, proving developer submission, administrator decision, administrator self-approval, local dry-run execution, readiness failure, governed destroy and audit.
- Both cold cycles passed `make seed-demo-data`, including fixture desired-state PR/check state, App Runner Terraform render, ready cloud-readiness preflight, plan-only review and local dry-run environment records.
- Both cold cycles passed Tempo trace verification.
- Both cold cycles passed `make verify`: Ruff, **106 pytest tests**, and Compose config validation.
- Final cleanup removed local project containers, volumes, `.venv` and `.local`.

This is local clean-room evidence only. It did not write GitHub, run authenticated Terraform, run `terraform apply`, create AWS resources, run Kubernetes, sync GitOps or deploy a workload.

## Self-contained local proof command

Date: 2026-10-13. Environment: macOS, Docker Desktop, Python 3.12, local stack initially stopped.

This validation changed `make local-proof` to bootstrap the local stack before running the proof sequence.

```bash
make local-proof
git diff --check
```

Results:

- `make local-proof` installed/reused the local Python environment and ran `docker compose up -d --build`.
- Smoke passed for API, worker, fixture executor, Prometheus, Grafana, Tempo and OPA.
- Browser contract passed.
- `make customer-plan-e2e` passed, including developer submission, administrator decision, administrator self-approval, local dry-run execution, readiness failure, governed destroy and audit.
- `make seed-demo-data` created realistic fixture records, including desired-state PR/check state, App Runner Terraform render, ready preflight, Terraform plan-only review and local dry-run environments.
- Tempo trace verification passed.
- `make verify` passed: Ruff, **106 pytest tests**, and Compose config validation.
- `git diff --check` passed.

This is local product proof only. It did not write GitHub, run authenticated Terraform, run `terraform apply`, create AWS resources, run Kubernetes, sync GitOps or deploy a workload.

## Agent client customer-plan review parity

Date: 2026-10-13. Environment: macOS, Docker Desktop, Python 3.12, running local AgentConstruct stack.

This validation added safe customer-plan review operations to the CLI and MCP surfaces while preserving the rule that MCP has no approval tool and neither interface obtains cloud credentials.

```bash
.venv/bin/python -m pytest tests/test_agent_interfaces.py -q
.venv/bin/python -m ruff check apps/api/src tests scripts
make local-proof
git diff --check
```

Results:

- Agent-interface tests passed: **8 passed**.
- Ruff passed.
- `make local-proof` passed: local bootstrap, smoke, browser contract, customer-plan E2E, seed data, Tempo trace verification, Ruff, **106 pytest tests**, and Compose config validation.
- MCP exposes customer-plan review creation/read/submission and approved dry-run request forwarding.
- MCP still exposes no approval or credential tool.
- CLI forwards customer-plan review operations to the governed API using the caller's bearer token.

This is local agent-interface evidence only. It did not write GitHub, run authenticated Terraform, run `terraform apply`, create AWS resources, run Kubernetes, sync GitOps or deploy a workload.
