let token = null;
let plan = null;
let productionEnvironment = null;
let day2Environment = null;
let cloudConnections = [];
let selectedCloudConnection = null;
let currentUser = null;
let githubConnection = null;
let currentProject = null;

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
  document.querySelector("#product-app").classList.add("hidden");
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
    const pending = await api("/api/v1/admin/pending-approvals");
    document.querySelector("#dashboard-pending").textContent = pending.length
      ? pending.map((item) => `${item.title} · revision ${item.revision}`).join("; ")
      : "No pending plan approvals.";
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

function optionLabel(candidate, selectedId, index) {
  if (candidate.candidate_id === selectedId) return "Recommended";
  if (candidate.candidate_class === "kubernetes" || candidate.candidate_class === "gpu_inference") return "Kubernetes / specialised";
  return index === 0 ? "Leanest" : "Scale-ready";
}

function renderAlternatives(architecture) {
  const ordered = architecture.candidates.filter((candidate) => candidate.valid).sort((left, right) => left.cost_estimate.monthly_low - right.cost_estimate.monthly_low);
  const rejected = architecture.candidates.filter((candidate) => !candidate.valid);
  document.querySelector("#recommendation-reason").textContent = architecture.recommendation_reason;
  document.querySelector("#alternatives").innerHTML = ordered.map((candidate, index) => `<div class="option ${candidate.candidate_id === architecture.selected_candidate_id ? "selected" : ""}"><span class="option-label">${optionLabel(candidate, architecture.selected_candidate_id, index)}</span><strong>${candidate.display_name}</strong><span>$${candidate.cost_estimate.monthly_low}–$${candidate.cost_estimate.monthly_high}/month · complexity ${candidate.operational_complexity}/5</span><p>${candidate.candidate_id === architecture.selected_candidate_id ? "Selected because it meets the requirements with the lowest necessary complexity." : candidate.upgrade_triggers.join(" ")}</p></div>`).join("") + (rejected.length ? `<p class="message"><strong>Not selected:</strong> ${rejected.map((candidate) => `${candidate.display_name} — ${candidate.rejected_reasons.join(", ")}`).join("; ")}</p>` : "");
  const selected = architecture.candidates.find((candidate) => candidate.candidate_id === architecture.selected_candidate_id);
  document.querySelector("#assumptions").textContent = `Assumptions: ${architecture.assumptions.join(" ")}`;
  document.querySelector("#upgrade-triggers").textContent = selected ? `Upgrade when: ${selected.upgrade_triggers.join(" ")}` : "";
}

async function refreshAudit() {
  const events = await api("/api/v1/audit-events");
  document.querySelector("#audit-events").innerHTML = events.length ? events.reverse().map((event) => `<div class="event"><time>${new Date(event.at).toLocaleString()}</time><div><strong>${event.action}</strong><br><span>${event.entity_type} · ${event.detail ? JSON.stringify(event.detail) : ""}</span></div></div>`).join("") : "No events yet.";
}

function renderEnvironments(environments) {
  productionEnvironment = environments.find((environment) => environment.type === "production" && environment.state === "READY") || null;
  day2Environment = productionEnvironment;
  document.querySelector("#environments").innerHTML = environments.length ? environments.map((environment) => `<div class="component"><strong>${environment.type}: ${environment.state}</strong><span>${JSON.stringify(environment.observed_state)}</span></div>`).join("") : "No local execution yet.";
  document.querySelector("#destroy").classList.toggle("hidden", !productionEnvironment);
  document.querySelector("#day2").classList.toggle("hidden", !day2Environment);
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

document.querySelector("#create").addEventListener("click", async () => {
  try {
    show("Interpreting your request and building an auditable plan…");
    const repository = document.querySelector("#repository").value;
    const branch = document.querySelector("#repository-branch").value;
    if (!repository || !branch) throw new Error("Choose an authorized GitHub repository and branch.");
    const cloudTarget = document.querySelector("#cloud-target").value;
    const constraints = ` Use ${document.querySelector("#region").value}. Treat data as ${document.querySelector("#data-classification").value}. Keep monthly infrastructure under $${document.querySelector("#budget").value}.`;
    const cloud = cloudTarget ? { id: cloudTarget } : await api("/api/v1/cloud-connections", { method: "POST", body: JSON.stringify({ display_name: "Local demo target — BYOC role contract" }) });
    const project = await api("/api/v1/projects", { method: "POST", body: JSON.stringify({ name: `support-rag-${Date.now().toString().slice(-6)}`, repository_url: repository, repository_branch: branch }) });
    currentProject = project;
    document.querySelector("#disconnect-repository").classList.remove("hidden");
    const repositoryDiscovery = await api(`/api/v1/projects/${project.id}/repository-discovery`);
    const intent = await api("/api/v1/intents", { method: "POST", body: JSON.stringify({ project_id: project.id, prompt: `${document.querySelector("#prompt").value}${constraints}`, source_repository: repository, cloud_connection_id: cloud.id, idempotency_key: idempotencyKey() }) });
    document.querySelector("#spec").textContent = JSON.stringify({ ...intent.spec, repository_discovery: repositoryDiscovery }, null, 2);
    plan = await api(`/api/v1/intents/${intent.id}/plans`, { method: "POST" });
    const architecture = plan.payload.architecture;
    document.querySelector("#profile").textContent = `${architecture.profile} · ${architecture.region}`;
    document.querySelector("#architecture").innerHTML = architecture.components.map((item) => `<div class="component"><strong>${item.name}</strong><span>${item.service} · ${item.purpose}</span></div>`).join("") + `<p><strong>Estimated infrastructure:</strong> $${architecture.cost_estimate.monthly_low}–$${architecture.cost_estimate.monthly_high}/month</p>`;
    renderAlternatives(architecture);
    document.querySelector("#policy").textContent = `${plan.policy_result.replaceAll("_", " ")} · immutable plan`;
    document.querySelector("#risk").textContent = architecture.risks.join(" ") || "No additional V1 planner risk was found. Review all assumptions before approval.";
    document.querySelector("#result").classList.remove("hidden");
    document.querySelector("#approve").classList.toggle("hidden", plan.state !== "APPROVAL_REQUIRED");
    document.querySelector("#execute").classList.toggle("hidden", plan.state === "APPROVAL_REQUIRED" || plan.state === "POLICY_DENIED");
    show(`Plan created. Policy result: ${plan.policy_result}.`);
    await Promise.all([refreshAudit(), refreshDashboard()]);
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

document.querySelector("#approve").addEventListener("click", async () => {
  try {
    if (!isAdministrator()) throw new Error("Sign in as a workspace administrator to approve this protected local execution plan.");
    plan = await api(`/api/v1/deployment-plans/${plan.id}/approve`, { method: "POST", body: JSON.stringify({ plan_hash: plan.plan_hash }) });
    document.querySelector("#approve").classList.add("hidden"); document.querySelector("#execute").classList.remove("hidden"); show("Workspace administrator approved the exact immutable plan."); await refreshAudit();
  } catch (error) { show(error.message, true); }
});

document.querySelector("#execute").addEventListener("click", async () => {
  try {
    const result = await api(`/api/v1/deployment-plans/${plan.id}/execute`, { method: "POST" });
    renderEnvironments(result.environments);
    show("The durable worker is running the bounded local job…");
    await waitForWorker(result.environments.map((environment) => environment.id));
    show("The worker completed and the observer recorded the result."); await refreshAudit();
  } catch (error) { show(error.message, true); }
});

document.querySelector("#destroy").addEventListener("click", async () => {
  try {
    if (!productionEnvironment) throw new Error("No ready production environment is available to destroy.");
    if (!isAdministrator()) throw new Error("Sign in as a workspace administrator to approve protected destruction.");
    let destroyPlan = await api(`/api/v1/environments/${productionEnvironment.id}/destroy-plan`, { method: "POST" });
    if (destroyPlan.state === "DESTROY_APPROVAL_REQUIRED") {
      destroyPlan = await api(`/api/v1/deployment-plans/${destroyPlan.id}/approve`, { method: "POST", body: JSON.stringify({ plan_hash: destroyPlan.plan_hash }) });
    }
    const result = await api(`/api/v1/deployment-plans/${destroyPlan.id}/execute`, { method: "POST" });
    await waitForWorker(result.environments.map((environment) => environment.id));
    show("The protected production environment was destroyed and cleanup was observed.");
    await refreshAudit();
  } catch (error) { show(error.message, true); }
});
document.querySelector("#optimize").addEventListener("click", async () => {
  try {
    if (!day2Environment) throw new Error("No ready production environment is available to diagnose.");
    const recommendation = await api(`/api/v1/environments/${day2Environment.id}/recommendation`);
    document.querySelector("#recommendation-summary").textContent = `${recommendation.diagnosis} Proposed change: minimum replicas ${recommendation.proposed_change.from} → ${recommendation.proposed_change.to}; estimated change: $${recommendation.estimated_monthly_cost_delta.monthly_low}–$${recommendation.estimated_monthly_cost_delta.monthly_high}/month. This is deterministic local telemetry, not AWS billing.`;
    let changePlan = await api(`/api/v1/environments/${day2Environment.id}/change-plan`, { method: "POST" });
    if (changePlan.state === "APPROVAL_REQUIRED") {
      if (!isAdministrator()) throw new Error("Sign in as a workspace administrator to approve this protected change.");
      changePlan = await api(`/api/v1/deployment-plans/${changePlan.id}/approve`, { method: "POST", body: JSON.stringify({ plan_hash: changePlan.plan_hash }) });
    }
    const result = await api(`/api/v1/deployment-plans/${changePlan.id}/execute`, { method: "POST" });
    show("The approved bounded change is running through the durable local worker…");
    await waitForWorker(result.environments.map((environment) => environment.id));
    show("The change completed and the observer recorded its result."); await refreshAudit();
  } catch (error) { show(error.message, true); }
});
document.querySelector("#refresh-audit").addEventListener("click", () => refreshAudit().catch((error) => show(error.message, true)));
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
