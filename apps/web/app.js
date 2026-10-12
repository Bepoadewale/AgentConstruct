let token = null;
let plan = null;
let productionEnvironment = null;
let day2Environment = null;
let cloudConnections = [];
let selectedCloudConnection = null;
let currentUser = null;
let githubConnection = null;
let currentProject = null;
let customerReview = null;

function idempotencyKey() {
  return globalThis.crypto?.randomUUID?.() || `local-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

async function api(path, options = {}) {
  const response = await fetch(path, { ...options, headers: { "content-type": "application/json", Authorization: `Bearer ${token}`, ...(options.headers || {}) } });
  if (response.status === 204) return null;
  const body = await response.json();
  if (!response.ok) throw new Error(body.detail || "Request failed");
  return body;
}

async function login(username) {
  const response = await fetch("/api/v1/auth/local-login", { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ username }) });
  const body = await response.json();
  token = body.access_token;
  currentUser = await api("/api/v1/me");
  document.querySelector("#identity").textContent = `${currentUser.workspace.name} · ${currentUser.user.role}`;
}

function isAdministrator() {
  return currentUser?.user?.role === "administrator";
}

async function startSession(username) {
  try {
    document.querySelector("#login-message").textContent = "Signing in…";
    await login(username);
    document.querySelector("#login").classList.add("hidden");
    document.querySelector("#product-app").classList.remove("hidden");
    document.querySelector("#logout").classList.remove("hidden");
    await Promise.all([refreshDashboard(), refreshAudit(), refreshCloudConnections(), refreshGitHubConnection()]);
  } catch (error) {
    document.querySelector("#login-message").textContent = error.message;
    document.querySelector("#login-message").className = "message failure";
  }
}

function logout() {
  token = null;
  currentUser = null;
  plan = null;
  customerReview = null;
  document.querySelector("#product-app").classList.add("hidden");
  document.querySelector("#customer-review").classList.add("hidden");
  document.querySelector("#login").classList.remove("hidden");
  document.querySelector("#logout").classList.add("hidden");
  document.querySelector("#login-message").textContent = "Signed out of the local fixture.";
  document.querySelector("#login-message").className = "message success";
}

async function refreshDashboard() {
  const dashboard = await api("/api/v1/dashboard");
  document.querySelector("#dashboard-heading").textContent = `${dashboard.workspace.name} dashboard`;
  document.querySelector("#dashboard-projects").textContent = dashboard.projects.length
    ? dashboard.projects.map((project) => project.name).join(", ") : "No projects yet.";
  document.querySelector("#dashboard-connections").textContent = dashboard.cloud_connections.length
    ? dashboard.cloud_connections.map((connection) => `${connection.display_name} (${connection.setup_state})`).join(", ") : "No AWS account connected yet.";
  document.querySelector("#dashboard-plans").textContent = dashboard.plans.length
    ? dashboard.plans.map((item) => `${item.title} · ${item.state}`).join("; ") : "No customer plan revisions yet.";
  document.querySelector("#admin-dashboard").classList.toggle("hidden", !isAdministrator());
  if (isAdministrator()) {
    const filter = document.querySelector("#admin-plan-filter").value;
    const pending = await api(`/api/v1/admin/customer-plan-revisions?state=${encodeURIComponent(filter)}`);
    document.querySelector("#dashboard-pending").textContent = pending.length
      ? pending.map((item) => `${item.title} · revision ${item.revision} · ${item.state}${item.is_self_approval ? " · self-approved" : ""}`).join("; ")
      : "No pending plan approvals.";
    const list = document.querySelector("#admin-pending-list");
    list.replaceChildren();
    pending.forEach((item) => {
      const button = document.createElement("button");
      button.type = "button";
      button.className = "secondary";
      button.textContent = `Review ${item.title} · ${item.state} · ${item.region || "region pending"}`;
      button.addEventListener("click", () => openCustomerReview(item.id).catch((error) => show(error.message, true)));
      list.append(button);
    });
  }
}

function show(message, failure = false) {
  const node = document.querySelector("#message"); node.textContent = message; node.className = `message ${failure ? "failure" : "success"}`;
}

function showAwsConnection(message, failure = false) {
  const node = document.querySelector("#aws-connect-message");
  node.textContent = message;
  node.className = `message ${failure ? "failure" : "success"}`;
}

function showGitHub(message, failure = false) {
  const node = document.querySelector("#github-message");
  node.textContent = message;
  node.className = `message ${failure ? "failure" : "success"}`;
}

async function refreshGitHubConnection() {
  githubConnection = await api("/api/v1/github/connection");
  const picker = document.querySelector("#github-installation");
  picker.innerHTML = githubConnection.installations.length
    ? githubConnection.installations.map((installation) => `<option value="${installation.id}">${installation.account_login} · ${installation.account_type}</option>`).join("")
    : '<option value="">No accessible GitHub App installation</option>';
  showGitHub(`GitHub App is ${githubConnection.execution === "SIMULATED" ? "a deterministic local fixture" : "connected in live read-only mode"}. Repository writes are disabled.`);
  if (githubConnection.installations.length) await refreshGitHubRepositories();
}

async function refreshGitHubRepositories() {
  const installationId = document.querySelector("#github-installation").value;
  if (!installationId) return;
  const repositories = await api(`/api/v1/github/installations/${encodeURIComponent(installationId)}/repositories`);
  const picker = document.querySelector("#repository");
  picker.innerHTML = '<option value="">Choose an authorized repository</option>' + repositories.map((repository) => `<option value="${repository.html_url}" data-repository="${repository.full_name}" data-default-branch="${repository.default_branch}">${repository.full_name}</option>`).join("");
  if (repositories.length) {
    picker.value = repositories[0].html_url;
    await refreshGitHubBranches();
  }
}

async function refreshGitHubBranches() {
  const repository = document.querySelector("#repository");
  const selected = repository.options[repository.selectedIndex];
  const installationId = document.querySelector("#github-installation").value;
  if (!selected?.dataset?.repository || !installationId) return;
  const encodedRepository = selected.dataset.repository.split("/").map(encodeURIComponent).join("/");
  const response = await api(`/api/v1/github/installations/${encodeURIComponent(installationId)}/repositories/${encodedRepository}/branches`);
  const picker = document.querySelector("#repository-branch");
  picker.innerHTML = response.branches.map((branch) => `<option value="${branch}">${branch}</option>`).join("");
  picker.value = selected.dataset.defaultBranch || response.branches[0] || "";
}

function renderCloudConnections() {
  const picker = document.querySelector("#cloud-target");
  picker.innerHTML = `<option value="">Local demo target — no AWS account connected</option>${cloudConnections.map((connection) => `<option value="${connection.id}">${connection.display_name}${connection.account_id ? ` · ${connection.account_id}` : ""} · ${connection.setup_state}</option>`).join("")}`;
  selectedCloudConnection = cloudConnections.find((connection) => connection.id === picker.value) || null;
}

async function refreshCloudConnections() {
  cloudConnections = await api("/api/v1/cloud-connections");
  renderCloudConnections();
}

async function showCloudConnectionDetail(connectionId) {
  const detail = await api(`/api/v1/cloud-connections/${connectionId}`);
  const node = document.querySelector("#aws-target-detail");
  node.innerHTML = `<strong>${detail.display_name}</strong><p>Account: ${detail.account_id || "setup pending"}<br>Role: ${detail.role_arn || "created by AWS setup after customer review"}<br>Status: ${detail.setup_state}<br>Regions: ${detail.authorized_regions.join(", ") || "verified regions not available yet"}<br>Capabilities: ${detail.capabilities.join("; ")}<br>Last verified: ${detail.verified_at || "not verified"}<br>Deployment permission: ${detail.deployment_permission}</p>`;
  node.classList.remove("hidden");
  document.querySelector("#disconnect-aws").classList.remove("hidden");
}

function renderCustomerReview(review) {
  customerReview = review;
  const content = review.content;
  const workloadSpec = content.application_analysis?.workload_spec || {};
  document.querySelector("#customer-review").classList.remove("hidden");
  document.querySelector("#review-title").textContent = `AWS infrastructure plan · revision ${review.revision}`;
  const reviewBoundary = review.state === "DRAFT" ? content.summary.status : "immutable review; not deployed";
  document.querySelector("#review-status").textContent = `${review.state} · ${reviewBoundary} Digest: ${review.content_digest}.`;
  const summary = review.review_summary || {};
  document.querySelector("#approval-boundary").classList.toggle("hidden", review.state !== "APPROVED");
  const adminSummary = document.querySelector("#admin-review-summary");
  adminSummary.classList.toggle("hidden", !isAdministrator());
  adminSummary.innerHTML = `<strong>Review evidence</strong><p>Requester: ${summary.requester || review.creator_subject}<br>Repository: ${summary.repository || "unknown"} · ${summary.branch || "branch unknown"}<br>AWS target: ${summary.aws_account_id || "local fixture"} · ${summary.region || "region unknown"}<br>Policy: ${summary.policy_result || "unknown"}<br>Monitoring: ${summary.prometheus || "Prometheus-compatible metrics"} + ${summary.grafana || "Grafana"}<br>Digest: ${review.content_digest}<br>Boundary: ${summary.execution_boundary || "Approval does not deploy."}</p>`;
  document.querySelector("#review-summary").textContent = `${content.summary.selected_profile}: ${content.summary.why}`;
  document.querySelector("#review-application").textContent = JSON.stringify(content.application_analysis, null, 2);
  document.querySelector("#review-target").textContent = JSON.stringify(content.target, null, 2);
  document.querySelector("#review-resources").innerHTML = content.resource_breakdown.map((resource) => `<div class="component"><strong>${resource.name}</strong><span>${resource.service} · ${resource.purpose}</span></div>`).join("");
  document.querySelector("#review-security").innerHTML = content.security.map((control) => `<div class="component">${control}</div>`).join("");
  document.querySelector("#review-observability").textContent = JSON.stringify(content.observability, null, 2);
  document.querySelector("#review-cost").textContent = JSON.stringify(content.cost_estimate, null, 2);
  document.querySelector("#review-deployment").textContent = JSON.stringify(content.deployment_strategy, null, 2);
  document.querySelector("#review-risks").textContent = JSON.stringify({ risks: content.risks_and_limitations, policy: content.policy_findings }, null, 2);
  const submit = document.querySelector("#submit-review");
  const revise = document.querySelector("#revise-review");
  const regenerate = document.querySelector("#regenerate-review");
  const revisionControls = document.querySelector("#revision-controls");
  const decisions = document.querySelector("#administrator-decisions");
  const actionMessage = document.querySelector("#review-action-message");
  const localExecution = document.querySelector("#local-execution");
  const isCreator = currentUser?.user?.subject === review.creator_subject;
  const editable = ["DRAFT", "REJECTED"].includes(review.state) && isCreator;
  submit.classList.toggle("hidden", !(review.state === "DRAFT" && isCreator));
  revise.classList.toggle("hidden", !(review.state === "REJECTED" && isCreator));
  regenerate.classList.toggle("hidden", !editable);
  revisionControls.classList.toggle("hidden", !editable);
  decisions.classList.toggle("hidden", !(review.state === "SUBMITTED" && isAdministrator()));
  localExecution.classList.toggle("hidden", review.state !== "APPROVED");
  renderReviewEnvironments(review.local_executions || []);
  document.querySelector("#review-budget").value = workloadSpec.monthly_budget_usd || "";
  document.querySelector("#review-region").value = content.target?.region || "us-east-1";
  document.querySelector("#review-data-classification").value = workloadSpec.data_classification || "restricted";
  document.querySelector("#review-environment").value = (workloadSpec.environments || ["staging", "production"]).join(",");
  document.querySelector("#review-availability").value = workloadSpec.availability_target || "99.9%";
  document.querySelector("#review-workload-type").value = workloadSpec.workload_type || "";
  document.querySelector("#review-public-access").checked = workloadSpec.requires_private_connectivity === false;
  document.querySelector("#accepted-assumptions").value = (content.assumption_decisions?.accepted || []).join("\n");
  document.querySelector("#rejected-assumptions").value = (content.assumption_decisions?.rejected || []).join("\n");
  document.querySelector("#review-diff").textContent = content.revision_diff && Object.keys(content.revision_diff).length
    ? JSON.stringify(content.revision_diff, null, 2)
    : "No revised constraint differences yet.";
  if (review.state === "DRAFT") actionMessage.textContent = isCreator ? "Review the exact digest, then submit it for administrator approval. Submission never deploys infrastructure." : "Only the plan creator can submit this draft.";
  else if (review.state === "SUBMITTED") actionMessage.textContent = isAdministrator() ? "This submitted plan is ready for an administrator decision. It is not deployed." : "Submitted for administrator review. It is not deployed.";
  else if (review.state === "REJECTED") actionMessage.textContent = `Rejected: ${review.decision?.reason || "reason unavailable"}. The creator can make a new draft revision.`;
  else if (review.state === "APPROVED") actionMessage.textContent = `Approved by ${review.decision?.approver_subject || "administrator"}${review.decision?.is_self_approval ? " (self-approval recorded)" : ""}. Approved does not mean deployed.`;
}

function renderReviewEnvironments(environments) {
  const node = document.querySelector("#review-environments");
  const destroyable = environments.find((environment) => ["READY", "DEGRADED", "FAILED"].includes(environment.state));
  document.querySelector("#destroy-review-dry-run").classList.toggle("hidden", !destroyable);
  if (!environments.length) {
    node.textContent = "No local dry-run execution yet.";
    return;
  }
  node.innerHTML = environments.map((environment) => `<div class="component"><strong>${environment.type}: ${environment.state}</strong><span>${environment.execution_mode || "LOCAL_DRY_RUN"} · ${environment.cost_estimate ? `$${environment.cost_estimate.monthly_low}–$${environment.cost_estimate.monthly_high}/month estimate` : "cost estimate unavailable"} · ${JSON.stringify(environment.observed_state || {})}</span></div>`).join("");
}

async function openCustomerReview(revisionId) {
  const review = await api(`/api/v1/customer-plan-revisions/${revisionId}`);
  renderCustomerReview(review);
  document.querySelector("#customer-review").scrollIntoView({ behavior: "smooth", block: "start" });
}

async function refreshAudit() {
  const events = await api("/api/v1/audit-evidence");
  document.querySelector("#audit-events").innerHTML = events.length ? events.reverse().map((event) => `<div class="event"><time>${new Date(event.at).toLocaleString()}</time><div><strong>${event.label}</strong><br><span>${event.actor_subject} · ${event.actor_role} · ${event.entity_type}${event.revision ? ` · revision ${event.revision}` : ""}${event.plan_digest ? ` · ${event.plan_digest}` : ""}${event.decision_reason ? ` · reason: ${event.decision_reason}` : ""}</span></div></div>`).join("") : "No events yet.";
}

function renderEnvironments(environments) {
  productionEnvironment = environments.find((environment) => environment.type === "production" && environment.state === "READY") || null;
  day2Environment = productionEnvironment;
  const environmentsNode = document.querySelector("#environments");
  if (environmentsNode) {
    environmentsNode.innerHTML = environments.length ? environments.map((environment) => `<div class="component"><strong>${environment.type}: ${environment.state}</strong><span>${JSON.stringify(environment.observed_state)}</span></div>`).join("") : "No local execution yet.";
  }
  const destroy = document.querySelector("#destroy");
  const day2 = document.querySelector("#day2");
  if (destroy) destroy.classList.toggle("hidden", !productionEnvironment);
  if (day2) day2.classList.toggle("hidden", !day2Environment);
}

async function waitForWorker(ids) {
  for (let attempt = 0; attempt < 40; attempt += 1) {
    const environments = await api("/api/v1/environments");
    const selected = environments.filter((environment) => ids.includes(environment.id));
    renderEnvironments(selected);
    if (selected.length === ids.length && selected.every((environment) => ["READY", "DEGRADED", "FAILED", "DESTROYED"].includes(environment.state))) return selected;
    await new Promise((resolve) => setTimeout(resolve, 300));
  }
  throw new Error("The worker did not report a final result within the local demo timeout.");
}

async function refreshOpenCustomerReview() {
  if (!customerReview) return null;
  const review = await api(`/api/v1/customer-plan-revisions/${customerReview.id}`);
  renderCustomerReview(review);
  return review;
}

document.querySelector("#create").addEventListener("click", async () => {
  try {
    show("Interpreting your request and building an auditable plan…");
    const repository = document.querySelector("#repository").value;
    const branch = document.querySelector("#repository-branch").value;
    if (!repository || !branch) throw new Error("Choose an authorized GitHub repository and branch.");
    const cloudTarget = document.querySelector("#cloud-target").value;
    const constraints = ` Use ${document.querySelector("#region").value}. Treat data as ${document.querySelector("#data-classification").value}. Keep monthly infrastructure under $${document.querySelector("#budget").value}. Create ${document.querySelector("#environment").value}. Meet ${document.querySelector("#availability").value} availability. Workload type: ${document.querySelector("#workload-type").value}.`;
    const cloud = cloudTarget ? { id: cloudTarget } : await api("/api/v1/cloud-connections", { method: "POST", body: JSON.stringify({ display_name: "Local demo target — BYOC role contract" }) });
    const project = await api("/api/v1/projects", { method: "POST", body: JSON.stringify({ name: `support-rag-${Date.now().toString().slice(-6)}`, repository_url: repository, repository_branch: branch }) });
    currentProject = project;
    document.querySelector("#disconnect-repository").classList.remove("hidden");
    const repositoryDiscovery = await api(`/api/v1/projects/${project.id}/repository-discovery`);
    const intent = await api("/api/v1/intents", { method: "POST", body: JSON.stringify({ project_id: project.id, prompt: `${document.querySelector("#prompt").value}${constraints}`, source_repository: repository, cloud_connection_id: cloud.id, idempotency_key: idempotencyKey() }) });
    document.querySelector("#spec").textContent = JSON.stringify({ ...intent.spec, repository_discovery: repositoryDiscovery }, null, 2);
    const analysis = repositoryDiscovery.analysis || {};
    document.querySelector("#repository-analysis").innerHTML = [
      ["Runtime", analysis.runtime_hints],
      ["Frameworks", analysis.framework_hints],
      ["Manifests", analysis.manifests],
      ["Data stores", analysis.database_hints],
      ["Deployment hints", analysis.deployment_hints],
      ["Limitations", analysis.limitations],
    ].map(([label, values]) => `<div class="component"><strong>${label}</strong><span>${(values || []).join(", ") || "No signal found"}</span></div>`).join("");
    plan = await api(`/api/v1/intents/${intent.id}/plans`, { method: "POST" });
    const architecture = plan.payload.architecture;
    document.querySelector("#profile").textContent = `${architecture.profile} · ${architecture.region}`;
    document.querySelector("#architecture").innerHTML = architecture.components.map((item) => `<div class="component"><strong>${item.name}</strong><span>${item.service} · ${item.purpose}</span></div>`).join("") + `<p><strong>Estimated monthly cost including Prometheus and Grafana:</strong> $${architecture.cost_estimate.monthly_low}–$${architecture.cost_estimate.monthly_high}/month</p>`;
    document.querySelector("#recommendation-reason").textContent = architecture.recommendation_reason;
    document.querySelector("#assumptions").textContent = `Assumptions: ${architecture.assumptions.join(" ")}`;
    document.querySelector("#policy").textContent = `${plan.policy_result.replaceAll("_", " ")} · immutable plan`;
    document.querySelector("#risk").textContent = architecture.risks.join(" ") || "No additional V1 planner risk was found. Review all assumptions before approval.";
    document.querySelector("#result").classList.remove("hidden");
    const review = await api(`/api/v1/deployment-plans/${plan.id}/customer-review`, { method: "POST" });
    renderCustomerReview(review);
    show(`One AWS review draft created. Policy result: ${plan.policy_result}. It has not been submitted, approved, or deployed.`);
    await Promise.all([refreshAudit(), refreshDashboard()]);
  } catch (error) { show(error.message, true); }
});

document.querySelector("#submit-review").addEventListener("click", async () => {
  try {
    if (!customerReview) throw new Error("Create a customer-plan review first.");
    const review = await api(`/api/v1/customer-plan-revisions/${customerReview.id}/submit`, { method: "POST" });
    renderCustomerReview(review);
    show("Plan submitted for administrator approval. It has not been deployed.");
    await Promise.all([refreshDashboard(), refreshAudit()]);
  } catch (error) { show(error.message, true); }
});

document.querySelector("#approve-review").addEventListener("click", async () => {
  try {
    if (!customerReview) throw new Error("Open a submitted customer plan first.");
    const review = await api(`/api/v1/customer-plan-revisions/${customerReview.id}/decisions`, { method: "POST", body: JSON.stringify({ decision: "APPROVED", content_digest: customerReview.content_digest }) });
    renderCustomerReview(review);
    show("Plan approval is persisted. It is approved, not deployed.");
    await Promise.all([refreshDashboard(), refreshAudit()]);
  } catch (error) { show(error.message, true); }
});

document.querySelector("#reject-review").addEventListener("click", async () => {
  try {
    if (!customerReview) throw new Error("Open a submitted customer plan first.");
    const reason = document.querySelector("#rejection-reason").value.trim();
    if (!reason) throw new Error("Enter a rejection reason.");
    const review = await api(`/api/v1/customer-plan-revisions/${customerReview.id}/decisions`, { method: "POST", body: JSON.stringify({ decision: "REJECTED", content_digest: customerReview.content_digest, reason }) });
    renderCustomerReview(review);
    show("Plan rejection is persisted. The creator can now make a revised draft.");
    await Promise.all([refreshDashboard(), refreshAudit()]);
  } catch (error) { show(error.message, true); }
});

document.querySelector("#revise-review").addEventListener("click", async () => {
  try {
    if (!customerReview) throw new Error("Open a rejected customer plan first.");
    const review = await api(`/api/v1/customer-plans/${customerReview.plan_id}/revisions`, { method: "POST", body: JSON.stringify({ content: customerReview.content }) });
    renderCustomerReview(review);
    show("A new immutable draft revision was created. Update the request if needed, then submit the new digest.");
    await Promise.all([refreshDashboard(), refreshAudit()]);
  } catch (error) { show(error.message, true); }
});

document.querySelector("#regenerate-review").addEventListener("click", async () => {
  try {
    if (!customerReview) throw new Error("Open a draft or rejected customer plan first.");
    const lines = (id) => document.querySelector(id).value.split("\n").map((item) => item.trim()).filter(Boolean);
    const review = await api(`/api/v1/customer-plans/${customerReview.plan_id}/constraint-revisions`, {
      method: "POST",
      body: JSON.stringify({
        monthly_budget_usd: Number(document.querySelector("#review-budget").value),
        region: document.querySelector("#review-region").value,
        environment: document.querySelector("#review-environment").value.split(",").filter(Boolean),
        data_classification: document.querySelector("#review-data-classification").value,
        availability_target: document.querySelector("#review-availability").value,
        workload_type: document.querySelector("#review-workload-type").value,
        public_access: document.querySelector("#review-public-access").checked,
        accepted_assumptions: lines("#accepted-assumptions"),
        rejected_assumptions: lines("#rejected-assumptions"),
      }),
    });
    renderCustomerReview(review);
    show("A revised draft was created from your constraint edits. Review the new digest before submitting.");
    await Promise.all([refreshDashboard(), refreshAudit()]);
  } catch (error) { show(error.message, true); }
});

document.querySelector("#execute-review-dry-run").addEventListener("click", async () => {
  try {
    if (!customerReview || customerReview.state !== "APPROVED") throw new Error("Approve the customer plan before running a local dry run.");
    show("Queuing approved-plan local dry run. No AWS resources will be created…");
    const queued = await api(`/api/v1/customer-plan-revisions/${customerReview.id}/execute-dry-run`, { method: "POST" });
    const ids = queued.environments.map((environment) => environment.id);
    await waitForWorker(ids);
    await refreshOpenCustomerReview();
    await refreshAudit();
    show("Local dry run observed. Review the environment health evidence below.");
  } catch (error) { show(error.message, true); }
});

document.querySelector("#destroy-review-dry-run").addEventListener("click", async () => {
  try {
    if (!customerReview) throw new Error("Open an approved customer plan first.");
    const target = (customerReview.local_executions || []).find((environment) => ["READY", "DEGRADED", "FAILED"].includes(environment.state));
    if (!target) throw new Error("No local dry-run environment is ready for destroy.");
    show("Creating governed local destroy plan…");
    const destroyPlan = await api(`/api/v1/customer-plan-revisions/${customerReview.id}/environments/${target.id}/destroy-dry-run`, { method: "POST" });
    if (destroyPlan.state === "DESTROY_APPROVAL_REQUIRED") {
      if (!isAdministrator()) throw new Error("Destroy approval is required. Sign in as administrator to approve and execute this local destroy.");
      await api(`/api/v1/deployment-plans/${destroyPlan.id}/approve`, { method: "POST", body: JSON.stringify({ plan_hash: destroyPlan.plan_hash }) });
    }
    const queued = await api(`/api/v1/deployment-plans/${destroyPlan.id}/execute`, { method: "POST" });
    const ids = queued.environments.map((environment) => environment.id);
    await waitForWorker(ids);
    await refreshOpenCustomerReview();
    await refreshAudit();
    show("Local dry-run destroy was observed. No AWS resources were deleted.");
  } catch (error) { show(error.message, true); }
});

document.querySelector("#cloud-target").addEventListener("change", (event) => {
  selectedCloudConnection = cloudConnections.find((connection) => connection.id === event.target.value) || null;
  document.querySelector("#cloud-target-message").textContent = selectedCloudConnection
    ? `Connected account ${selectedCloudConnection.account_id || "setup pending"}. Setup state: ${selectedCloudConnection.setup_state}. No browser-held AWS credentials.`
    : "A connected account is optional for local planning. AgentConstruct never asks for AWS access keys.";
  if (selectedCloudConnection) showCloudConnectionDetail(selectedCloudConnection.id).catch((error) => showAwsConnection(error.message, true));
  else document.querySelector("#aws-target-detail").classList.add("hidden");
});

document.querySelector("#show-aws-connect").addEventListener("click", () => {
  document.querySelector("#aws-connect").classList.toggle("hidden");
});

document.querySelector("#open-aws-setup").addEventListener("click", async () => {
  try {
    const accountId = document.querySelector("#aws-account-id").value.trim();
    if (!/^\d{12}$/.test(accountId)) throw new Error("Enter a 12-digit AWS account ID.");
    showAwsConnection("Preparing your read-only AWS setup…");
    const connection = await api("/api/v1/cloud-connections", { method: "POST", body: JSON.stringify({ display_name: `AWS account ${accountId}` }) });
    const setup = await api(`/api/v1/cloud-connections/${connection.id}/aws-quick-create`, { method: "POST", body: JSON.stringify({ account_id: accountId }) });
    cloudConnections.push({ ...connection, account_id: accountId, setup_state: "SETUP_LINK_GENERATED" });
    renderCloudConnections();
    document.querySelector("#cloud-target").value = connection.id;
    selectedCloudConnection = cloudConnections.find((item) => item.id === connection.id);
    document.querySelector("#verify-aws").classList.remove("hidden");
    document.querySelector("#disconnect-aws").classList.remove("hidden");
    showAwsConnection("AWS will open a review page. Create the read-only role there, then return here and choose Verify connection.");
    window.open(setup.quick_create_url, "_blank", "noopener,noreferrer");
    await refreshAudit();
  } catch (error) { showAwsConnection(error.message, true); }
});

document.querySelector("#verify-aws").addEventListener("click", async () => {
  try {
    if (!selectedCloudConnection) throw new Error("Open AWS setup for an account first.");
    showAwsConnection("Queuing a read-only STS verification. No AWS resources will be created…");
    const queued = await api(`/api/v1/cloud-connections/${selectedCloudConnection.id}/aws-verify`, { method: "POST", body: JSON.stringify({ region: document.querySelector("#region").value }) });
    let verified;
    for (let attempt = 0; attempt < 40; attempt += 1) {
      await new Promise((resolve) => setTimeout(resolve, 300));
      verified = await api(`/api/v1/cloud-connections/${selectedCloudConnection.id}/aws-verification-jobs/${queued.id}`);
      if (["SUCCEEDED", "FAILED"].includes(verified.state)) break;
    }
    if (!verified || verified.state !== "SUCCEEDED") throw new Error(verified?.error || "AWS verification did not finish in time.");
    selectedCloudConnection.setup_state = "VERIFIED";
    showAwsConnection(`Connected. Recorded a credential-free inventory snapshot from ${verified.region}.`);
    await refreshCloudConnections();
    document.querySelector("#cloud-target").value = selectedCloudConnection.id;
    await showCloudConnectionDetail(selectedCloudConnection.id);
    await refreshAudit();
  } catch (error) { showAwsConnection(error.message, true); }
});

document.querySelector("#disconnect-aws").addEventListener("click", async () => {
  try {
    if (!selectedCloudConnection) throw new Error("Choose an AWS connection to disconnect.");
    await api(`/api/v1/cloud-connections/${selectedCloudConnection.id}`, { method: "DELETE" });
    selectedCloudConnection = null;
    document.querySelector("#aws-target-detail").classList.add("hidden");
    document.querySelector("#disconnect-aws").classList.add("hidden");
    await Promise.all([refreshCloudConnections(), refreshDashboard(), refreshAudit()]);
    showAwsConnection("AWS connection metadata was disconnected. No customer credentials were stored.");
  } catch (error) { showAwsConnection(error.message, true); }
});

document.querySelector("#refresh-audit").addEventListener("click", () => refreshAudit().catch((error) => show(error.message, true)));
document.querySelector("#admin-plan-filter").addEventListener("change", () => refreshDashboard().catch((error) => show(error.message, true)));
document.querySelector("#refresh-github").addEventListener("click", () => refreshGitHubConnection().catch((error) => showGitHub(error.message, true)));
document.querySelector("#github-installation").addEventListener("change", () => refreshGitHubRepositories().catch((error) => showGitHub(error.message, true)));
document.querySelector("#repository").addEventListener("change", () => refreshGitHubBranches().catch((error) => showGitHub(error.message, true)));
document.querySelector("#disconnect-repository").addEventListener("click", async () => {
  try {
    if (!currentProject) throw new Error("Create a project with this repository before disconnecting it.");
    await api(`/api/v1/projects/${currentProject.id}/repository`, { method: "DELETE" });
    currentProject = null;
    document.querySelector("#disconnect-repository").classList.add("hidden");
    showGitHub("Repository access was disconnected from this project. The GitHub App installation was not changed.");
    await Promise.all([refreshDashboard(), refreshAudit()]);
  } catch (error) { showGitHub(error.message, true); }
});
document.querySelector("#login-developer").addEventListener("click", () => startSession("founder"));
document.querySelector("#login-administrator").addEventListener("click", () => startSession("administrator"));
document.querySelector("#logout").addEventListener("click", logout);
