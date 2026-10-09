let token = null;
let plan = null;
let productionEnvironment = null;
let day2Environment = null;
let cloudConnections = [];
let selectedCloudConnection = null;

function idempotencyKey() {
  return globalThis.crypto?.randomUUID?.() || `local-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

async function api(path, options = {}) {
  const response = await fetch(path, { ...options, headers: { "content-type": "application/json", Authorization: `Bearer ${token}`, ...(options.headers || {}) } });
  const body = await response.json();
  if (!response.ok) throw new Error(body.detail || "Request failed");
  return body;
}

async function login(username) {
  const response = await fetch("/api/v1/auth/local-login", { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ username }) });
  const body = await response.json();
  token = body.access_token;
  document.querySelector("#identity").textContent = `local identity · ${username}`;
}

function show(message, failure = false) {
  const node = document.querySelector("#message"); node.textContent = message; node.className = `message ${failure ? "failure" : "success"}`;
}

function showAwsConnection(message, failure = false) {
  const node = document.querySelector("#aws-connect-message");
  node.textContent = message;
  node.className = `message ${failure ? "failure" : "success"}`;
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
    const cloudTarget = document.querySelector("#cloud-target").value;
    const constraints = ` Use ${document.querySelector("#region").value}. Treat data as ${document.querySelector("#data-classification").value}. Keep monthly infrastructure under $${document.querySelector("#budget").value}.`;
    const cloud = cloudTarget ? { id: cloudTarget } : await api("/api/v1/cloud-connections", { method: "POST", body: JSON.stringify({ display_name: "Local demo target — BYOC role contract" }) });
    const project = await api("/api/v1/projects", { method: "POST", body: JSON.stringify({ name: `support-rag-${Date.now().toString().slice(-6)}`, repository_url: repository }) });
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
    await refreshAudit();
  } catch (error) { show(error.message, true); }
});

document.querySelector("#cloud-target").addEventListener("change", (event) => {
  selectedCloudConnection = cloudConnections.find((connection) => connection.id === event.target.value) || null;
  document.querySelector("#cloud-target-message").textContent = selectedCloudConnection
    ? `Connected account ${selectedCloudConnection.account_id || "setup pending"}. Setup state: ${selectedCloudConnection.setup_state}. No browser-held AWS credentials.`
    : "A connected account is optional for local planning. AgentConstruct never asks for AWS access keys.";
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
    showAwsConnection("AWS will open a review page. Create the read-only role there, then return here and choose Verify connection.");
    window.open(setup.quick_create_url, "_blank", "noopener,noreferrer");
    await refreshAudit();
  } catch (error) { showAwsConnection(error.message, true); }
});

document.querySelector("#verify-aws").addEventListener("click", async () => {
  try {
    if (!selectedCloudConnection) throw new Error("Open AWS setup for an account first.");
    showAwsConnection("Using short-lived STS credentials to verify the read-only role…");
    const verified = await api(`/api/v1/cloud-connections/${selectedCloudConnection.id}/aws-verify`, { method: "POST", body: JSON.stringify({ region: document.querySelector("#region").value }) });
    selectedCloudConnection.setup_state = "VERIFIED";
    showAwsConnection(`Connected. Recorded a credential-free inventory snapshot from ${verified.region}.`);
    await refreshCloudConnections();
    document.querySelector("#cloud-target").value = selectedCloudConnection.id;
    await refreshAudit();
  } catch (error) { showAwsConnection(error.message, true); }
});

document.querySelector("#approve").addEventListener("click", async () => {
  try {
    await login("operator");
    plan = await api(`/api/v1/deployment-plans/${plan.id}/approve`, { method: "POST", body: JSON.stringify({ plan_hash: plan.plan_hash }) });
    document.querySelector("#approve").classList.add("hidden"); document.querySelector("#execute").classList.remove("hidden"); show("Independent operator approved the exact immutable plan."); await refreshAudit();
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
    await login("founder");
    let destroyPlan = await api(`/api/v1/environments/${productionEnvironment.id}/destroy-plan`, { method: "POST" });
    if (destroyPlan.state === "DESTROY_APPROVAL_REQUIRED") {
      await login("operator");
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
      await login("operator");
      changePlan = await api(`/api/v1/deployment-plans/${changePlan.id}/approve`, { method: "POST", body: JSON.stringify({ plan_hash: changePlan.plan_hash }) });
    }
    const result = await api(`/api/v1/deployment-plans/${changePlan.id}/execute`, { method: "POST" });
    show("The approved bounded change is running through the durable local worker…");
    await waitForWorker(result.environments.map((environment) => environment.id));
    show("The change completed and the observer recorded its result."); await refreshAudit();
  } catch (error) { show(error.message, true); }
});
document.querySelector("#refresh-audit").addEventListener("click", () => refreshAudit().catch((error) => show(error.message, true)));
login("founder").then(async () => { await refreshAudit(); await refreshCloudConnections(); }).catch((error) => show(error.message, true));
