let token = null;
let plan = null;
let productionEnvironment = null;

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

async function refreshAudit() {
  const events = await api("/api/v1/audit-events");
  document.querySelector("#audit-events").innerHTML = events.length ? events.reverse().map((event) => `<div class="event"><time>${new Date(event.at).toLocaleString()}</time><div><strong>${event.action}</strong><br><span>${event.entity_type} · ${event.detail ? JSON.stringify(event.detail) : ""}</span></div></div>`).join("") : "No events yet.";
}

document.querySelector("#create").addEventListener("click", async () => {
  try {
    show("Interpreting your request and building an auditable plan…");
    const repository = document.querySelector("#repository").value;
    const cloudTarget = document.querySelector("#cloud-target").value;
    const cloud = await api("/api/v1/cloud-connections", { method: "POST", body: JSON.stringify({ display_name: cloudTarget }) });
    const project = await api("/api/v1/projects", { method: "POST", body: JSON.stringify({ name: `support-rag-${Date.now().toString().slice(-6)}`, repository_url: repository }) });
    const intent = await api("/api/v1/intents", { method: "POST", body: JSON.stringify({ project_id: project.id, prompt: document.querySelector("#prompt").value, source_repository: repository, cloud_connection_id: cloud.id, idempotency_key: idempotencyKey() }) });
    document.querySelector("#spec").textContent = JSON.stringify(intent.spec, null, 2);
    plan = await api(`/api/v1/intents/${intent.id}/plans`, { method: "POST" });
    const architecture = plan.payload.architecture;
    document.querySelector("#profile").textContent = `${architecture.profile} · ${architecture.region}`;
    document.querySelector("#architecture").innerHTML = architecture.components.map((item) => `<div class="component"><strong>${item.name}</strong><span>${item.service} · ${item.purpose}</span></div>`).join("") + `<p><strong>Estimated infrastructure:</strong> $${architecture.cost_estimate.monthly_low}–$${architecture.cost_estimate.monthly_high}/month</p>`;
    document.querySelector("#policy").textContent = `${plan.policy_result.replaceAll("_", " ")} · immutable plan`;
    document.querySelector("#risk").textContent = architecture.risks.join(" ") || "No additional V1 planner risk was found. Review all assumptions before approval.";
    document.querySelector("#result").classList.remove("hidden");
    document.querySelector("#approve").classList.toggle("hidden", plan.state !== "APPROVAL_REQUIRED");
    document.querySelector("#execute").classList.toggle("hidden", plan.state === "APPROVAL_REQUIRED" || plan.state === "POLICY_DENIED");
    show(`Plan created. Policy result: ${plan.policy_result}.`);
    await refreshAudit();
  } catch (error) { show(error.message, true); }
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
    productionEnvironment = result.environments.find((environment) => environment.type === "production" && environment.state === "READY") || null;
    document.querySelector("#environments").innerHTML = result.environments.map((environment) => `<div class="component"><strong>${environment.type}: ${environment.state}</strong><span>${JSON.stringify(environment.observed_state)}</span></div>`).join("");
    document.querySelector("#destroy").classList.toggle("hidden", !productionEnvironment);
    show("The bounded executor completed and the observer recorded the result."); await refreshAudit();
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
    productionEnvironment = null;
    document.querySelector("#destroy").classList.add("hidden");
    document.querySelector("#environments").innerHTML += result.environments.map((environment) => `<div class="component"><strong>${environment.type}: ${environment.state}</strong><span>${JSON.stringify(environment.observed_state)}</span></div>`).join("");
    show("The protected production environment was destroyed and cleanup was observed.");
    await refreshAudit();
  } catch (error) { show(error.message, true); }
});
document.querySelector("#refresh-audit").addEventListener("click", () => refreshAudit().catch((error) => show(error.message, true)));
login("founder").then(refreshAudit).catch((error) => show(error.message, true));
