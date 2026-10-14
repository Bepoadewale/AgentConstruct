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
let dashboardSnapshot = null;
let auditSnapshot = [];
let historyPage = 1;
let auditPage = 1;
const PAGE_SIZE = 10;

const escapeHtml = (value) => String(value ?? "")
  .replaceAll("&", "&amp;")
  .replaceAll("<", "&lt;")
  .replaceAll(">", "&gt;")
  .replaceAll('"', "&quot;")
  .replaceAll("'", "&#039;");

function setButtonBusy(button, busy, busyLabel = "Working…") {
  if (!button) return;
  if (busy) {
    button.dataset.defaultLabel = button.textContent;
    button.disabled = true;
    button.textContent = busyLabel;
    button.setAttribute("aria-busy", "true");
  } else {
    button.disabled = false;
    button.textContent = button.dataset.defaultLabel || button.textContent;
    button.removeAttribute("aria-busy");
  }
}

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
  dashboardSnapshot = dashboard;
  document.querySelector("#dashboard-heading").textContent = `${dashboard.workspace.name} dashboard`;
  document.querySelector("#dashboard-projects").textContent = dashboard.projects.length;
  document.querySelector("#dashboard-connections").textContent = dashboard.cloud_connections.length;
  document.querySelector("#dashboard-plans").textContent = dashboard.plans.length;
  renderDashboardLists(dashboard);
  historyPage = 1;
  renderHistory(dashboard.plans || []);
  document.querySelector("#admin-dashboard").classList.toggle("hidden", !isAdministrator());
  if (isAdministrator()) {
    const filter = document.querySelector("#admin-plan-filter").value;
    const pending = await api(`/api/v1/admin/customer-plan-revisions?state=${encodeURIComponent(filter)}`);
    document.querySelector("#dashboard-pending").textContent = `${pending.length} plan${pending.length === 1 ? "" : "s"} require attention.`;
    const list = document.querySelector("#admin-pending-list");
    list.replaceChildren();
    pending.forEach((item) => {
      const button = document.createElement("button");
      button.type = "button";
      button.className = "secondary";
      button.textContent = `${item.title} · revision ${item.revision} · ${item.region || "region pending"}`;
      button.addEventListener("click", () => openCustomerReview(item.id).catch((error) => show(error.message, true)));
      list.append(button);
    });
  }
}

function renderDashboardLists(dashboard) {
  const projects = document.querySelector("#dashboard-recent-projects");
  const activity = document.querySelector("#dashboard-recent-activity");
  if (projects) {
    const recent = (dashboard.projects || []).slice(0, 5);
    projects.innerHTML = recent.length ? recent.map((project) => `<div class="compact-row"><span class="compact-icon">⌘</span><span><b>${escapeHtml(project.name)}</b><small>${escapeHtml(project.repository_url || "Repository not connected")}</small></span></div>`).join("") : `<div class="empty-inline">No projects yet.</div>`;
  }
  if (activity) {
    const recent = (dashboard.recent_activity || []).slice(0, 5);
    activity.innerHTML = recent.length ? recent.map((event) => `<div class="compact-row"><span class="compact-icon">•</span><span><b>${escapeHtml(formatAction(event.action))}</b><small>${escapeHtml(formatDate(event.at))}</small></span></div>`).join("") : `<div class="empty-inline">No activity yet.</div>`;
  }
}

function formatDate(value) {
  if (!value) return "Date unavailable";
  return new Date(value).toLocaleString([], { month: "short", day: "numeric", hour: "numeric", minute: "2-digit" });
}

function formatAction(action) {
  return String(action || "activity").replaceAll("_", " ").replaceAll(".", " · ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function renderPagination(nodeId, page, total, onChange) {
  const node = document.querySelector(`#${nodeId}`);
  if (!node) return;
  const pages = Math.max(1, Math.ceil(total / PAGE_SIZE));
  node.innerHTML = total > PAGE_SIZE ? `<span>Page ${page} of ${pages} · ${total} total</span><span><button type="button" class="secondary" data-page="prev" ${page === 1 ? "disabled" : ""}>Previous</button><button type="button" class="secondary" data-page="next" ${page === pages ? "disabled" : ""}>Next</button></span>` : (total ? `<span>${total} total</span>` : "");
  node.querySelector('[data-page="prev"]')?.addEventListener("click", () => onChange(page - 1));
  node.querySelector('[data-page="next"]')?.addEventListener("click", () => onChange(page + 1));
}

function renderHistory(plans) {
  const node = document.querySelector("#history-list");
  if (!node) return;
  const query = (document.querySelector("#history-search")?.value || "").toLowerCase().trim();
  const state = document.querySelector("#history-filter")?.value || "ALL";
  const filtered = plans.filter((item) => {
    const haystack = `${item.title} ${item.state} ${item.creator_subject || ""}`.toLowerCase();
    return (state === "ALL" || item.state === state) && (!query || haystack.includes(query));
  });
  if (!filtered.length) {
    node.innerHTML = `<div class="empty-state"><strong>${plans.length ? "No matching plans" : "No plans yet"}</strong><span>${plans.length ? "Try a different search or status filter." : "Create a plan to start your workspace history."}</span></div>`;
    return;
  }
  const pageCount = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE));
  historyPage = Math.min(historyPage, pageCount);
  const pageItems = filtered.slice((historyPage - 1) * PAGE_SIZE, historyPage * PAGE_SIZE);
  node.innerHTML = pageItems.map((item) => `<button class="history-row" type="button" data-history-id="${escapeHtml(item.id)}"><span class="history-title"><b>${escapeHtml(item.title)}</b><small>Revision ${escapeHtml(item.revision)} · ${escapeHtml(formatDate(item.created_at))}</small></span><span class="status-chip status-${escapeHtml(String(item.state).toLowerCase())}">${escapeHtml(item.state)}</span><span class="history-arrow">›</span></button>`).join("");
  node.querySelectorAll("[data-history-id]").forEach((row) => row.addEventListener("click", () => openCustomerReview(row.dataset.historyId).catch((error) => show(error.message, true))));
  renderPagination("history-pagination", historyPage, filtered.length, (nextPage) => { historyPage = nextPage; renderHistory(plans); });
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
    ? githubConnection.installations.map((installation) => `<option value="${escapeHtml(installation.id)}">${escapeHtml(installation.account_login)} · ${escapeHtml(installation.account_type)}</option>`).join("")
    : '<option value="">No accessible GitHub App installation</option>';
  const installLink = githubConnection.install_url ? ` <a href="${githubConnection.install_url}" target="_blank" rel="noreferrer">Open GitHub App install</a>.` : "";
  showGitHub(`GitHub App is ${githubConnection.execution === "SIMULATED" ? "a deterministic local fixture" : "connected in live read-only mode"}. Repository writes are disabled.${installLink}`);
  const detail = document.querySelector("#github-status-detail");
  const states = githubConnection.installation_states || [];
  const deliveries = githubConnection.recent_webhook_deliveries || [];
  if (states.length || deliveries.length) {
    detail.innerHTML = `<strong>GitHub App state</strong><p>Webhook receiver: ${githubConnection.webhooks_enabled ? "enabled" : "not configured"}<br>Writes: disabled until reviewed publication is approved.</p>` +
      states.map((state) => `<div class="component"><strong>${escapeHtml(state.account_login)}</strong><span>${escapeHtml(state.installation_id)} · ${escapeHtml(state.state)} · ${escapeHtml(state.repository_selection)}</span></div>`).join("") +
      deliveries.map((delivery) => `<div class="component"><strong>${escapeHtml(delivery.event)}</strong><span>${escapeHtml(delivery.status)} · ${escapeHtml(delivery.repository || "installation")} · ${escapeHtml(delivery.delivery_id)}</span></div>`).join("");
    detail.classList.remove("hidden");
  } else {
    detail.classList.add("hidden");
  }
  if (githubConnection.installations.length) await refreshGitHubRepositories();
}

async function refreshGitHubRepositories() {
  const installationId = document.querySelector("#github-installation").value;
  if (!installationId) return;
  const repositories = await api(`/api/v1/github/installations/${encodeURIComponent(installationId)}/repositories`);
  const picker = document.querySelector("#repository");
  picker.innerHTML = '<option value="">Choose an authorized repository</option>' + repositories.map((repository) => `<option value="${escapeHtml(repository.html_url)}" data-repository="${escapeHtml(repository.full_name)}" data-default-branch="${escapeHtml(repository.default_branch)}">${escapeHtml(repository.full_name)}</option>`).join("");
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
  picker.innerHTML = response.branches.map((branch) => `<option value="${escapeHtml(branch)}">${escapeHtml(branch)}</option>`).join("");
  picker.value = selected.dataset.defaultBranch || response.branches[0] || "";
}

function renderCloudConnections() {
  const picker = document.querySelector("#cloud-target");
  picker.innerHTML = `<option value="">Local demo target — no AWS account connected</option>${cloudConnections.map((connection) => `<option value="${escapeHtml(connection.id)}">${escapeHtml(connection.display_name)}${connection.account_id ? ` · ${escapeHtml(connection.account_id)}` : ""} · ${escapeHtml(connection.setup_state)}</option>`).join("")}`;
  selectedCloudConnection = cloudConnections.find((connection) => connection.id === picker.value) || null;
}

async function refreshCloudConnections() {
  cloudConnections = await api("/api/v1/cloud-connections");
  renderCloudConnections();
}

async function showCloudConnectionDetail(connectionId) {
  const detail = await api(`/api/v1/cloud-connections/${connectionId}`);
  const node = document.querySelector("#aws-target-detail");
  node.innerHTML = `<strong>${escapeHtml(detail.display_name)}</strong><p>Account: ${escapeHtml(detail.account_id || "setup pending")}<br>Role: ${escapeHtml(detail.role_arn || "created by AWS setup after customer review")}<br>Status: ${escapeHtml(detail.setup_state)}<br>Regions: ${escapeHtml(detail.authorized_regions.join(", ") || "verified regions not available yet")}<br>Capabilities: ${escapeHtml(detail.capabilities.join("; "))}<br>Last verified: ${escapeHtml(detail.verified_at || "not verified")}<br>Deployment permission: ${escapeHtml(detail.deployment_permission)}</p>`;
  node.classList.remove("hidden");
  document.querySelector("#disconnect-aws").classList.remove("hidden");
}

function renderArchitectureMap(architecture) {
  const node = document.querySelector("#architecture-map");
  if (!node) return;
  const components = architecture.components || [];
  const application = components.find((item) => /application|service|compute/i.test(item.name)) || components[0];
  const data = components.find((item) => /database|storage|data/i.test(`${item.name} ${item.service}`));
  const monitoring = components.filter((item) => /prometheus|grafana|metric/i.test(`${item.name} ${item.service}`));
  const nodes = [
    { title: "Your repository", detail: "GitHub source", className: "primary" },
    { title: application?.service || architecture.profile, detail: application?.purpose || "Selected compute profile", className: "primary" },
    ...(data ? [{ title: data.service, detail: data.purpose, className: "" }] : []),
    { title: "Prometheus + Grafana", detail: monitoring.length ? "Metrics and dashboards" : "Monitoring contract", className: "monitoring" },
  ];
  node.innerHTML = nodes.map((item) => `<div class="map-node ${item.className}"><b>${escapeHtml(item.title)}</b><small>${escapeHtml(item.detail)}</small></div>`).join("");
}

function renderPlanHighlights(architecture) {
  const node = document.querySelector("#plan-highlights");
  if (!node || !architecture) return;
  const componentCount = (architecture.components || []).length;
  const low = architecture.cost_estimate?.monthly_low;
  const high = architecture.cost_estimate?.monthly_high;
  node.innerHTML = [
    `<span class="highlight"><b>Profile</b>${escapeHtml(architecture.profile || "AWS")}</span>`,
    `<span class="highlight"><b>Monthly estimate</b>${low != null ? `$${escapeHtml(low)}–$${escapeHtml(high)}` : "Range pending"}</span>`,
    `<span class="highlight"><b>Components</b>${componentCount}</span>`,
    `<span class="highlight"><b>Decision</b>One selected plan</span>`,
  ].join("");
}

function renderPlanTimeline(state) {
  const node = document.querySelector("#plan-timeline");
  if (!node) return;
  const states = ["DRAFT", "SUBMITTED", "APPROVED", "OBSERVED"];
  const current = state === "READY" || state === "DEGRADED" ? "OBSERVED" : state;
  const currentIndex = states.indexOf(current);
  node.innerHTML = states.map((item, index) => `<div class="timeline-step ${index <= currentIndex ? "active" : ""} ${item === current ? "current" : ""}"><span>${index + 1}</span>${item[0] + item.slice(1).toLowerCase()}<small>${item === "APPROVED" ? "Decision recorded" : item === "OBSERVED" ? "Evidence required" : ""}</small></div>`).join("");
}

function renderCustomerReview(review) {
  customerReview = review;
  const content = review.content;
  const workloadSpec = content.application_analysis?.workload_spec || {};
  document.querySelector("#customer-review").classList.remove("hidden");
  document.querySelector("#review-title").textContent = `AWS infrastructure plan · revision ${review.revision}`;
  const reviewBoundary = review.state === "DRAFT" ? content.summary.status : "immutable review; not deployed";
  document.querySelector("#review-status").innerHTML = `<span class="status-chip status-${String(review.state).toLowerCase()}">${escapeHtml(review.state)}</span> <span>${escapeHtml(reviewBoundary)} Digest: <code>${escapeHtml(review.content_digest)}</code>.</span>`;
  const copyDigest = document.querySelector("#copy-digest");
  copyDigest.classList.remove("hidden");
  copyDigest.onclick = async () => {
    try { await navigator.clipboard.writeText(review.content_digest); show("Plan digest copied."); } catch { show("Digest: " + review.content_digest); }
  };
  renderPlanTimeline(review.state);
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
  const desiredStatePr = document.querySelector("#desired-state-pr");
  const terraformPlanContract = document.querySelector("#terraform-plan-contract");
  const cloudReadiness = document.querySelector("#cloud-readiness");
  const terraformPlanReview = document.querySelector("#terraform-plan-review");
  const cloudExecutionRun = document.querySelector("#cloud-execution-run");
  const markDesiredStateReviewed = document.querySelector("#mark-desired-state-reviewed");
  const runCloudPreflight = document.querySelector("#run-cloud-preflight");
  const runTerraformPlanReview = document.querySelector("#run-terraform-plan-review");
  const requestCloudExecutionRun = document.querySelector("#request-cloud-execution-run");
  const isCreator = currentUser?.user?.subject === review.creator_subject;
  const isAdmin = isAdministrator();
  const editable = ["DRAFT", "REJECTED"].includes(review.state) && isCreator;
  submit.classList.toggle("hidden", !(review.state === "DRAFT" && isCreator));
  revise.classList.toggle("hidden", !(review.state === "REJECTED" && isCreator));
  regenerate.classList.toggle("hidden", !editable);
  revisionControls.classList.toggle("hidden", !editable);
  decisions.classList.toggle("hidden", !(review.state === "SUBMITTED" && isAdmin));
  localExecution.classList.toggle("hidden", review.state !== "APPROVED");
  desiredStatePr.classList.toggle("hidden", review.state !== "APPROVED");
  terraformPlanContract.classList.toggle("hidden", review.state !== "APPROVED");
  cloudReadiness.classList.toggle("hidden", review.state !== "APPROVED");
  terraformPlanReview.classList.toggle("hidden", review.state !== "APPROVED");
  cloudExecutionRun.classList.toggle("hidden", review.state !== "APPROVED");
  markDesiredStateReviewed.classList.toggle("hidden", !(review.state === "APPROVED" && isAdmin));
  runCloudPreflight.classList.toggle("hidden", !(review.state === "APPROVED" && isAdmin));
  runTerraformPlanReview.classList.toggle("hidden", !(review.state === "APPROVED" && isAdmin));
  requestCloudExecutionRun.classList.toggle("hidden", !(review.state === "APPROVED" && isAdmin));
  renderReviewEnvironments(review.local_executions || []);
  renderDesiredStatePublications(review.desired_state_publications || []);
  renderTerraformPlanRenders(review.terraform_plan_renders || []);
  renderCloudReadinessPreflights(review.cloud_readiness_preflights || []);
  renderTerraformPlanReviews(review.terraform_plan_reviews || []);
  renderCloudExecutionRuns(review.cloud_execution_runs || []);
  document.querySelector("#guard-account").value = content.target?.account_id || "";
  document.querySelector("#guard-regions").value = content.target?.region || "us-east-1";
  const highEstimate = content.cost_estimate?.range?.monthly_high;
  if (highEstimate) document.querySelector("#guard-budget").value = highEstimate;
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

function renderCloudReadinessPreflights(preflights) {
  const node = document.querySelector("#cloud-preflight-result");
  if (!preflights.length) {
    node.textContent = "No cloud-readiness preflight yet. Future cloud execution is BLOCKED_CLOUD_RUNTIME_NOT_CONFIGURED until this checklist is evaluated and explicitly approved later.";
    return;
  }
  node.innerHTML = preflights.map((preflight) => `<div class="component"><strong>${preflight.state}</strong><span>${preflight.boundary}</span></div><div>${(preflight.checklist || []).map((item) => `<div class="component"><strong>${item.status}: ${item.label}</strong><span>${item.detail}</span></div>`).join("")}</div><pre>${JSON.stringify(preflight.would_deploy, null, 2)}</pre>`).join("");
}

function renderTerraformPlanReviews(reviews) {
  const node = document.querySelector("#terraform-plan-review-result");
  if (!reviews.length) {
    node.textContent = "No Terraform plan-only review yet. Run cloud-readiness preflight first. Apply is unavailable.";
    return;
  }
  node.innerHTML = reviews.map((review) => `<div class="component"><strong>${review.state}</strong><span>${review.mode} · apply available: ${review.apply_available}</span></div><pre>${JSON.stringify({
    command: review.command,
    evidence: review.evidence,
    boundary: review.boundary,
  }, null, 2)}</pre>`).join("");
}

function renderCloudExecutionRuns(runs) {
  const node = document.querySelector("#cloud-execution-run-result");
  if (!runs.length) {
    node.textContent = "No cloud execution run requested yet. Approval still does not deploy anything.";
    return;
  }
  node.innerHTML = runs.map((run) => `<div class="component"><strong>Attempt ${run.attempt}: ${run.state}</strong><span>${run.mode} · evidence: /api/v1/cloud-execution-runs/${run.id}/evidence<br>${run.boundary}</span></div><pre>${JSON.stringify({
    digest: run.content_digest,
    profile: run.profile,
    command: run.command,
    evidence: run.evidence,
    outputs: run.outputs,
  }, null, 2)}</pre>`).join("");
}

function renderTerraformPlanRenders(renders) {
  const node = document.querySelector("#terraform-render");
  if (!renders.length) {
    node.textContent = "No generated deployment contract yet. App Runner contracts are PLAN_ONLY_NOT_APPLIED and cannot apply AWS changes.";
    return;
  }
  node.innerHTML = renders.map((item) => {
    const render = item.render || {};
    const inputs = render.module_inputs || {};
    return `<div class="component"><strong>${item.state}</strong><span>${item.profile} · ${item.terraform_root} · digest ${item.content_digest}</span></div><pre>${JSON.stringify({
      execution_boundary: render.execution_boundary || item.boundary,
      service_name: inputs.service_name,
      aws_region: inputs.aws_region,
      image_repository: inputs.image_repository,
      module_path: item.module_path,
      commands: render.commands,
      apply_command_available: render.apply_command_available,
      tags: inputs.tags,
    }, null, 2)}</pre>`;
  }).join("");
}

function parseGuardTags(value) {
  return Object.fromEntries(value.split(",").map((item) => item.trim()).filter(Boolean).map((item) => {
    const [key, ...rest] = item.split("=");
    return [key.trim(), rest.join("=").trim()];
  }).filter(([key, val]) => key && val));
}

function renderDesiredStatePublications(publications) {
  const node = document.querySelector("#desired-state-publication");
  if (!publications.length) {
    node.textContent = "No desired-state publication yet. Cloud execution remains blocked until a reviewed PR contract exists.";
    return;
  }
  node.innerHTML = publications.map((publication) => `<div class="component"><strong>${publication.state}</strong><span>${publication.publication_url || "fixture PR"} · ${publication.branch} · checks: ${(publication.required_checks || []).join(", ")}</span></div><pre>${JSON.stringify({ profile: publication.package?.profile, files: (publication.package?.files || []).map((file) => file.path), merge_boundary: publication.merge_boundary }, null, 2)}</pre>`).join("");
}

function renderReviewEnvironments(environments) {
  const node = document.querySelector("#review-environments");
  const destroyable = environments.find((environment) => ["READY", "DEGRADED", "FAILED"].includes(environment.state));
  document.querySelector("#destroy-review-dry-run").classList.toggle("hidden", !destroyable);
  if (!environments.length) {
    node.textContent = "No local dry-run execution yet.";
    return;
  }
  node.innerHTML = environments.map((environment) => {
    const outputs = (environment.outputs || []).length
      ? `<h4>Deployment outputs</h4>${environment.outputs.map((output) => `<div class="component"><strong>${output.name}</strong><span>${output.status} · ${output.type} · ${output.sensitive ? "secret reference" : output.value}</span></div>`).join("")}`
      : "<p class=\"message\">No deployment outputs observed yet.</p>";
    const resources = (environment.resources || []).length
      ? `<h4>Observed resources</h4>${environment.resources.map((resource) => `<div class="component"><strong>${resource.provider}:${resource.type}</strong><span>${resource.status} · ${resource.name}${resource.region ? ` · ${resource.region}` : ""}${resource.external_id ? ` · ${resource.external_id}` : ""}</span></div>`).join("")}`
      : "<p class=\"message\">No resources observed yet.</p>";
    return `<div class="component"><strong>${environment.type}: ${environment.state}</strong><span>${environment.execution_mode || "LOCAL_DRY_RUN"} · ${environment.cost_estimate ? `$${environment.cost_estimate.monthly_low}–$${environment.cost_estimate.monthly_high}/month estimate` : "cost estimate unavailable"}</span>${outputs}${resources}</div>`;
  }).join("");
}

async function openCustomerReview(revisionId) {
  const review = await api(`/api/v1/customer-plan-revisions/${revisionId}`);
  renderCustomerReview(review);
  window.location.hash = "#customer-review";
}

async function refreshAudit() {
  const events = await api("/api/v1/audit-evidence");
  auditSnapshot = events;
  renderAuditEvents(events);
}

function renderAuditEvents(events) {
  const node = document.querySelector("#audit-events");
  if (!node) return;
  const query = (document.querySelector("#audit-search")?.value || "").toLowerCase().trim();
  const filter = document.querySelector("#audit-filter")?.value || "ALL";
  const filtered = events.filter((event) => {
    const haystack = `${event.label} ${event.actor_subject} ${event.entity_type} ${event.decision_reason || ""}`.toLowerCase();
    return (filter === "ALL" || event.label.toLowerCase().includes(filter)) && (!query || haystack.includes(query));
  });
  const ordered = filtered.slice().reverse();
  const pageCount = Math.max(1, Math.ceil(ordered.length / PAGE_SIZE));
  auditPage = Math.min(auditPage, pageCount);
  const pageItems = ordered.slice((auditPage - 1) * PAGE_SIZE, auditPage * PAGE_SIZE);
  node.innerHTML = pageItems.length ? pageItems.map((event) => `<div class="event"><time>${escapeHtml(formatDate(event.at))}</time><div><strong>${escapeHtml(event.label)}</strong><br><span>${escapeHtml(event.actor_subject)} · ${escapeHtml(event.actor_role)} · ${escapeHtml(event.entity_type)}${event.revision ? ` · revision ${escapeHtml(event.revision)}` : ""}${event.plan_digest ? ` · ${escapeHtml(event.plan_digest.slice(0, 12))}…` : ""}${event.decision_reason ? ` · reason: ${escapeHtml(event.decision_reason)}` : ""}</span></div></div>`).join("") : `<div class="empty-state"><strong>No matching activity</strong><span>Try a different search or event filter.</span></div>`;
  renderPagination("audit-pagination", auditPage, ordered.length, (nextPage) => { auditPage = nextPage; renderAuditEvents(events); });
}

function renderEnvironments(environments) {
  productionEnvironment = environments.find((environment) => environment.type === "production" && environment.state === "READY") || null;
  day2Environment = productionEnvironment;
  const environmentsNode = document.querySelector("#environments");
  if (environmentsNode) {
    environmentsNode.innerHTML = environments.length ? environments.map((environment) => {
      const outputSummary = (environment.outputs || []).map((output) => `${output.name}: ${output.status}`).join("; ") || "outputs pending";
      const resourceSummary = (environment.resources || []).map((resource) => `${resource.type}: ${resource.status}`).join("; ") || "resources pending";
      return `<div class="component"><strong>${environment.type}: ${environment.state}</strong><span>${outputSummary}<br>${resourceSummary}</span></div>`;
    }).join("") : "No local execution yet.";
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
  const createButton = document.querySelector("#create");
  setButtonBusy(createButton, true, "Building plan…");
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
    ].map(([label, values]) => `<div class="component"><strong>${escapeHtml(label)}</strong><span>${escapeHtml((values || []).join(", ") || "No signal found")}</span></div>`).join("");
    plan = await api(`/api/v1/intents/${intent.id}/plans`, { method: "POST" });
    const architecture = plan.payload.architecture;
    document.querySelector("#profile").textContent = `${architecture.profile} · ${architecture.region}`;
    document.querySelector("#architecture").innerHTML = architecture.components.map((item) => `<div class="component"><strong>${escapeHtml(item.name)}</strong><span><b class="service-tag">${escapeHtml(item.service)}</b> ${escapeHtml(item.purpose)}</span></div>`).join("") + `<p class="estimate-callout"><strong>Estimated monthly cost including Prometheus and Grafana:</strong> $${escapeHtml(architecture.cost_estimate.monthly_low)}–$${escapeHtml(architecture.cost_estimate.monthly_high)}/month</p>`;
    renderPlanHighlights(architecture);
    renderArchitectureMap(architecture);
    document.querySelector("#recommendation-reason").textContent = architecture.recommendation_reason;
    document.querySelector("#assumptions").textContent = `Assumptions: ${architecture.assumptions.join(" ")}`;
    document.querySelector("#policy").textContent = `${plan.policy_result.replaceAll("_", " ")} · immutable plan`;
    document.querySelector("#risk").textContent = architecture.risks.join(" ") || "No additional V1 planner risk was found. Review all assumptions before approval.";
    document.querySelector("#open-review").classList.remove("hidden");
    document.querySelector("#result").classList.remove("hidden");
    const review = await api(`/api/v1/deployment-plans/${plan.id}/customer-review`, { method: "POST" });
    renderCustomerReview(review);
    window.location.hash = "#result";
    show(`One AWS review draft created. Policy result: ${plan.policy_result}. It has not been submitted, approved, or deployed.`);
    await Promise.all([refreshAudit(), refreshDashboard()]);
  } catch (error) { show(error.message, true); }
  finally { setButtonBusy(createButton, false); }
});

document.querySelector("#open-review").addEventListener("click", () => { window.location.hash = "#customer-review"; });
document.querySelector("#history-new-plan").addEventListener("click", () => { window.location.hash = "#describe"; });
document.querySelector("#history-search").addEventListener("input", () => renderHistory(dashboardSnapshot?.plans || []));
document.querySelector("#history-filter").addEventListener("change", () => { historyPage = 1; renderHistory(dashboardSnapshot?.plans || []); });
document.querySelector("#audit-search").addEventListener("input", () => renderAuditEvents(auditSnapshot));
document.querySelector("#audit-filter").addEventListener("change", () => { auditPage = 1; renderAuditEvents(auditSnapshot); });

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

document.querySelector("#publish-desired-state").addEventListener("click", async () => {
  try {
    if (!customerReview || customerReview.state !== "APPROVED") throw new Error("Approve the customer plan before creating a desired-state PR contract.");
    show("Creating reviewed desired-state PR publication. Fixture mode stores it locally; live mode opens a GitHub PR when explicitly enabled…");
    const publication = await api(`/api/v1/customer-plan-revisions/${customerReview.id}/desired-state-publications`, {
      method: "POST",
      body: JSON.stringify({ content_digest: customerReview.content_digest }),
    });
    renderDesiredStatePublications([publication]);
    await refreshOpenCustomerReview();
    await refreshAudit();
    show("Desired-state publication recorded. Human review remains required before any future cloud execution.");
  } catch (error) { show(error.message, true); }
});

document.querySelector("#mark-desired-state-reviewed").addEventListener("click", async () => {
  try {
    if (!customerReview || customerReview.state !== "APPROVED") throw new Error("Approve the customer plan before recording PR checks.");
    const publication = (customerReview.desired_state_publications || [])[0];
    if (!publication) throw new Error("Create the desired-state PR publication first.");
    if (!isAdministrator()) throw new Error("Only an administrator can record PR checks.");
    show("Recording PR checks passed. AgentConstruct will not merge or deploy…");
    const updated = await api(`/api/v1/customer-plan-revisions/${customerReview.id}/desired-state-publications/${publication.id}/state`, {
      method: "POST",
      body: JSON.stringify({ content_digest: customerReview.content_digest, state: "CHECKS_PASSED" }),
    });
    renderDesiredStatePublications([updated]);
    await refreshOpenCustomerReview();
    await refreshAudit();
    show("PR checks passed were recorded. AgentConstruct still cannot merge or deploy.");
  } catch (error) { show(error.message, true); }
});

document.querySelector("#render-terraform-contract").addEventListener("click", async () => {
  try {
    if (!customerReview || customerReview.state !== "APPROVED") throw new Error("Approve the customer plan before generating a Terraform contract.");
    show("Generating plan-only App Runner Terraform contract. No Terraform plan/apply/destroy or AWS call will occur…");
    const render = await api(`/api/v1/customer-plan-revisions/${customerReview.id}/terraform-plan-renders`, {
      method: "POST",
      body: JSON.stringify({ content_digest: customerReview.content_digest }),
    });
    renderTerraformPlanRenders([render]);
    await refreshOpenCustomerReview();
    await refreshAudit();
    show("Plan-only Terraform contract generated. It is not applied and cannot deploy AWS resources.");
  } catch (error) { show(error.message, true); }
});

document.querySelector("#run-cloud-preflight").addEventListener("click", async () => {
  try {
    if (!customerReview || customerReview.state !== "APPROVED") throw new Error("Approve the customer plan before running cloud-readiness preflight.");
    show("Running local cloud-readiness preflight. No Terraform or AWS call will occur…");
    const account = document.querySelector("#guard-account").value.trim();
    const preflight = await api(`/api/v1/customer-plan-revisions/${customerReview.id}/cloud-readiness-preflights`, {
      method: "POST",
      body: JSON.stringify({
        content_digest: customerReview.content_digest,
        expected_account_id: account || null,
        allowed_regions: document.querySelector("#guard-regions").value.split(",").map((item) => item.trim()).filter(Boolean),
        required_tags: parseGuardTags(document.querySelector("#guard-tags").value),
        budget_ceiling_usd: Number(document.querySelector("#guard-budget").value),
        execution_mode: "DRY_RUN_ONLY",
        require_reviewed_pr: document.querySelector("#guard-reviewed-pr").checked,
        runtime_identity_configured: document.querySelector("#guard-runtime").checked,
      }),
    });
    renderCloudReadinessPreflights([preflight]);
    await refreshOpenCustomerReview();
    await refreshAudit();
    show(`Cloud-readiness preflight recorded: ${preflight.state}. No AWS resources were created.`);
  } catch (error) { show(error.message, true); }
});

document.querySelector("#run-terraform-plan-review").addEventListener("click", async () => {
  try {
    if (!customerReview || customerReview.state !== "APPROVED") throw new Error("Approve the customer plan before requesting a Terraform plan-only review.");
    const preflights = customerReview.cloud_readiness_preflights || [];
    const latestPreflight = preflights[0];
    show("Recording Terraform plan-only review evidence. Apply is unavailable…");
    const account = document.querySelector("#guard-account").value.trim();
    const review = await api(`/api/v1/customer-plan-revisions/${customerReview.id}/terraform-plan-reviews`, {
      method: "POST",
      body: JSON.stringify({
        content_digest: customerReview.content_digest,
        preflight_id: latestPreflight?.id || null,
        expected_account_id: account || null,
        expected_region: document.querySelector("#guard-regions").value.split(",").map((item) => item.trim()).filter(Boolean)[0] || null,
        mode: "LOCAL_CONTRACT_ONLY",
        allow_cloud_plan: false,
      }),
    });
    renderTerraformPlanReviews([review]);
    await refreshOpenCustomerReview();
    await refreshAudit();
    show(`Terraform plan-only review recorded: ${review.state}. Apply remains unavailable.`);
  } catch (error) { show(error.message, true); }
});

document.querySelector("#request-cloud-execution-run").addEventListener("click", async () => {
  try {
    if (!customerReview || customerReview.state !== "APPROVED") throw new Error("Approve the customer plan before requesting AWS execution.");
    show("Requesting guarded App Runner execution run. Local/default mode cannot apply Terraform…");
    const account = document.querySelector("#guard-account").value.trim();
    const renders = customerReview.terraform_plan_renders || [];
    const preflights = customerReview.cloud_readiness_preflights || [];
    const planReviews = customerReview.terraform_plan_reviews || [];
    const run = await api(`/api/v1/customer-plan-revisions/${customerReview.id}/cloud-execution-runs`, {
      method: "POST",
      body: JSON.stringify({
        content_digest: customerReview.content_digest,
        terraform_render_id: renders[0]?.id || null,
        preflight_id: preflights[0]?.id || null,
        terraform_plan_review_id: planReviews[0]?.id || null,
        expected_account_id: account || null,
        expected_region: document.querySelector("#guard-regions").value.split(",").map((item) => item.trim()).filter(Boolean)[0] || null,
        mode: "GUARDED_CLOUD_EXECUTION",
        confirmation: null,
      }),
    });
    renderCloudExecutionRuns([run]);
    await refreshOpenCustomerReview();
    await refreshAudit();
    show(`Cloud execution run recorded: ${run.state}. No AWS resources were created.`);
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

const mobileMenuToggle = document.querySelector("#mobile-menu-toggle");
const mobileNav = document.querySelector("#mobile-nav");
mobileMenuToggle?.addEventListener("click", () => {
  const open = mobileNav.classList.toggle("hidden") === false;
  mobileMenuToggle.setAttribute("aria-expanded", String(open));
});
mobileNav?.querySelectorAll("a").forEach((link) => link.addEventListener("click", () => {
  mobileNav.classList.add("hidden");
  mobileMenuToggle.setAttribute("aria-expanded", "false");
}));

function syncActiveNavigation() {
  const current = window.location.hash || "#dashboard";
  const screen = current.slice(1) || "dashboard";
  const validScreens = ["dashboard", "describe", "result", "customer-review", "history", "audit"];
  const target = validScreens.includes(screen) ? screen : "dashboard";
  document.querySelectorAll("[data-screen]").forEach((node) => {
    const active = node.dataset.screen === target && !node.classList.contains("hidden");
    node.classList.toggle("screen-active", active);
  });
  document.querySelectorAll(".sidebar-link, header nav a, .mobile-nav a").forEach((link) => {
    link.classList.toggle("active", link.getAttribute("href") === `#${target}`);
  });
}
window.addEventListener("hashchange", syncActiveNavigation);
syncActiveNavigation();

const commandPalette = document.querySelector("#command-palette");
const commandSearch = document.querySelector("#command-search");
function closeCommandPalette() { commandPalette.classList.add("hidden"); }
function openCommandPalette() { commandPalette.classList.remove("hidden"); commandSearch.value = ""; commandSearch.focus(); }
function runCommand(command) {
  closeCommandPalette();
  if (command === "new-plan") window.location.hash = "#describe";
  if (command === "dashboard") window.location.hash = "#dashboard";
  if (command === "audit") window.location.hash = "#audit";
}
document.querySelector("#open-command-palette")?.addEventListener("click", openCommandPalette);
document.querySelector(".workspace-switcher")?.addEventListener("click", openCommandPalette);
document.querySelector("#close-command-palette")?.addEventListener("click", closeCommandPalette);
commandPalette?.addEventListener("click", (event) => { if (event.target === commandPalette) closeCommandPalette(); });
document.querySelectorAll("[data-command]").forEach((item) => item.addEventListener("click", () => runCommand(item.dataset.command)));
commandSearch?.addEventListener("input", () => {
  const query = commandSearch.value.toLowerCase();
  document.querySelectorAll("#command-list button").forEach((item) => { item.classList.toggle("hidden", !item.textContent.toLowerCase().includes(query)); });
});
document.addEventListener("keydown", (event) => {
  if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k") { event.preventDefault(); openCommandPalette(); }
  if (event.key === "Escape") closeCommandPalette();
  if (!event.metaKey && !event.ctrlKey && !event.altKey && event.key.toLowerCase() === "n" && document.activeElement?.tagName !== "INPUT" && document.activeElement?.tagName !== "TEXTAREA") runCommand("new-plan");
});
