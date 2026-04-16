const defaultApiBase = localStorage.getItem("qcApiBase") || "http://127.0.0.1:8000";
const state = {
  mode: "id",
  jobs: [],
  selectedJobId: null,
  apiBase: defaultApiBase,
  pollTimer: null,
};

const modeCopy = {
  id: {
    guide: "Use ID for navigation, interactions, quiz logic, accessibility, and on-screen text review.",
    examples: [
      "Review this Rise course for dead ends after each quiz question.",
      "Check every marker interaction in section 3 and note missed reveals.",
    ],
  },
  cg: {
    guide: "Use Content for storyboard text, subtitles, grammar, British English, and terminology consistency.",
    examples: [
      "Review the attached storyboard CSV for grammar and terminology issues.",
      "Check the PDF copy for British English consistency.",
    ],
  },
  fg: {
    guide: "Use Graphic for Figma links, screenshots, layout, spacing, readability, and WCAG visual checks.",
    examples: [
      "Review this Figma frame for spacing and hierarchy issues.",
      "Check the screenshot set for contrast and alignment risks.",
    ],
  },
};

const elements = {
  apiBaseInput: document.getElementById("apiBaseInput"),
  labelInput: document.getElementById("labelInput"),
  connectBtn: document.getElementById("connectBtn"),
  loginStatus: document.getElementById("loginStatus"),
  promptInput: document.getElementById("promptInput"),
  linksInput: document.getElementById("linksInput"),
  imageInput: document.getElementById("imageInput"),
  documentInput: document.getElementById("documentInput"),
  imageChips: document.getElementById("imageChips"),
  documentChips: document.getElementById("documentChips"),
  runBtn: document.getElementById("runBtn"),
  runStateBadge: document.getElementById("runStateBadge"),
  modeGuide: document.getElementById("modeGuide"),
  modeExamples: document.getElementById("modeExamples"),
  jobList: document.getElementById("jobList"),
  refreshJobsBtn: document.getElementById("refreshJobsBtn"),
  statusFilter: document.getElementById("statusFilter"),
  severityFilter: document.getElementById("severityFilter"),
  detailTitle: document.getElementById("detailTitle"),
  detailStatus: document.getElementById("detailStatus"),
  findingCount: document.getElementById("findingCount"),
  agentSummary: document.getElementById("agentSummary"),
  createdAt: document.getElementById("createdAt"),
  severityStrip: document.getElementById("severityStrip"),
  sourceSummary: document.getElementById("sourceSummary"),
  findingsTable: document.getElementById("findingsTable"),
  detailReport: document.getElementById("detailReport"),
  detailArtifacts: document.getElementById("detailArtifacts"),
};

elements.apiBaseInput.value = state.apiBase;
elements.labelInput.value = localStorage.getItem("qcLabel") || "";

function apiUrl(path) {
  return `${state.apiBase.replace(/\/$/, "")}${path}`;
}

function setMode(mode) {
  state.mode = mode;
  document.querySelectorAll(".mode-tab").forEach((button) => {
    button.classList.toggle("active", button.dataset.mode === mode);
  });
  elements.modeGuide.textContent = modeCopy[mode].guide;
  elements.modeExamples.innerHTML = modeCopy[mode].examples.map((item) => `<li>${item}</li>`).join("");
}

function renderFileChips(input, container) {
  container.innerHTML = "";
  [...input.files].forEach((file) => {
    const chip = document.createElement("span");
    chip.className = "chip";
    chip.textContent = file.name;
    container.appendChild(chip);
  });
}

async function connectBackend() {
  state.apiBase = elements.apiBaseInput.value.trim();
  localStorage.setItem("qcApiBase", state.apiBase);
  localStorage.setItem("qcLabel", elements.labelInput.value.trim());
  await fetchJson("/api/health");
  elements.loginStatus.textContent = "Backend connected.";
  await refreshJobs();
}

async function fetchJson(path, options = {}) {
  const response = await fetch(apiUrl(path), { ...options, headers: { ...(options.headers || {}) } });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(data.detail || "Request failed");
  }
  return data;
}

function currentFiltersMatch(job) {
  const statusValue = elements.statusFilter.value;
  const severityValue = elements.severityFilter.value;
  if (statusValue && job.status !== statusValue) {
    return false;
  }
  if (severityValue && !(job.severity_counts || {})[severityValue]) {
    return false;
  }
  return true;
}

function renderJobs() {
  const visibleJobs = state.jobs.filter(currentFiltersMatch);
  elements.jobList.innerHTML = visibleJobs
    .map((job) => {
      const severitySummary = Object.entries(job.severity_counts || {})
        .map(([key, value]) => `${key}:${value}`)
        .join(" · ") || "No findings yet";
      return `
        <article class="job-card ${job.job_id === state.selectedJobId ? "active" : ""}" data-job-id="${job.job_id}">
          <div class="job-meta">
            <strong>${job.mode.toUpperCase()}</strong>
            <span>${job.status}</span>
          </div>
          <h3>${job.prompt_preview || "Untitled run"}</h3>
          <p>${severitySummary}</p>
          <div class="job-meta">
            <span>${job.created_at}</span>
            <span>${job.created_by_label}</span>
          </div>
        </article>
      `;
    })
    .join("");
  document.querySelectorAll(".job-card").forEach((card) => {
    card.addEventListener("click", () => selectJob(card.dataset.jobId));
  });
}

function renderJobDetail(job) {
  if (!job) {
    elements.detailTitle.textContent = "No run selected";
    elements.detailStatus.textContent = "Waiting";
    return;
  }
  elements.detailTitle.textContent = `${job.mode.toUpperCase()} run · ${job.job_id}`;
  elements.detailStatus.textContent = job.status;
  elements.findingCount.textContent = String(job.findings_count || 0);
  const agents = [...new Set((job.findings || []).map((finding) => finding.source_agent))];
  elements.agentSummary.textContent = agents.length ? agents.join(", ") : "Pending";
  elements.createdAt.textContent = job.created_at;
  elements.severityStrip.innerHTML = Object.entries(job.severity_counts || {})
    .map(([severity, count]) => `<span class="severity-pill">${severity}: ${count}</span>`)
    .join("");
  elements.sourceSummary.innerHTML = (job.source_summary || []).length
    ? `<h3>Source Summary</h3><ul>${job.source_summary.map((item) => `<li>${item}</li>`).join("")}</ul>`
    : "<p class='hint'>No source summary yet.</p>";
  elements.findingsTable.innerHTML = (job.findings || []).length
    ? job.findings
        .map(
          (finding) => `
            <article class="finding-card">
              <div class="finding-top">
                <strong>${finding.id} · ${finding.area}</strong>
                <span class="severity-${finding.severity.toLowerCase()}">${finding.severity}</span>
              </div>
              <p><strong>Agent:</strong> ${finding.source_agent}</p>
              <p><strong>Evidence:</strong> ${finding.evidence}</p>
              <p><strong>Impact:</strong> ${finding.impact}</p>
              <p><strong>Recommended fix:</strong> ${finding.recommended_fix}</p>
            </article>
          `
        )
        .join("")
    : "<p class='hint'>Findings will appear here when the run completes.</p>";
  elements.detailReport.innerHTML = job.report_html || "<p class='hint'>Full report is not available yet.</p>";
  elements.detailArtifacts.innerHTML = (job.artifact_urls || []).length
    ? job.artifact_urls
        .map((item) => `<a href="${apiUrl(item.url)}" target="_blank" rel="noreferrer">${item.name}</a>`)
        .join("")
    : "<p class='hint'>No artifacts available yet.</p>";
}

async function refreshJobs() {
  if (!state.apiBase) {
    return;
  }
  state.jobs = await fetchJson("/api/jobs");
  renderJobs();
  if (state.selectedJobId) {
    await selectJob(state.selectedJobId, false);
  }
}

async function selectJob(jobId, rerender = true) {
  state.selectedJobId = jobId;
  const job = await fetchJson(`/api/jobs/${jobId}`);
  const index = state.jobs.findIndex((item) => item.job_id === jobId);
  if (index >= 0) {
    state.jobs[index] = { ...state.jobs[index], ...job };
  } else {
    state.jobs.unshift(job);
  }
  if (rerender) {
    renderJobs();
  }
  renderJobDetail(job);
  if (["queued", "running"].includes(job.status)) {
    startPolling(job.job_id);
  } else if (state.pollTimer) {
    window.clearInterval(state.pollTimer);
    state.pollTimer = null;
  }
}

function startPolling(jobId) {
  if (state.pollTimer) {
    window.clearInterval(state.pollTimer);
  }
  state.pollTimer = window.setInterval(async () => {
    try {
      const job = await fetchJson(`/api/jobs/${jobId}`);
      const index = state.jobs.findIndex((item) => item.job_id === jobId);
      if (index >= 0) {
        state.jobs[index] = { ...state.jobs[index], ...job };
      }
      renderJobs();
      renderJobDetail(job);
      if (!["queued", "running"].includes(job.status)) {
        window.clearInterval(state.pollTimer);
        state.pollTimer = null;
        elements.runStateBadge.textContent = job.status === "completed" ? "Completed" : "Needs attention";
      }
    } catch (error) {
      console.error(error);
    }
  }, 2500);
}

async function createJob() {
  const form = new FormData();
  form.append("mode", state.mode);
  form.append("prompt_text", elements.promptInput.value);
  form.append("created_by_label", elements.labelInput.value.trim() || "Workspace User");
  elements.linksInput.value
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean)
    .forEach((link) => form.append("links", link));
  [...elements.imageInput.files].forEach((file) => form.append("images", file));
  [...elements.documentInput.files].forEach((file) => form.append("documents", file));
  elements.runStateBadge.textContent = "Queued";
  const job = await fetchJson("/api/jobs", { method: "POST", body: form });
  state.selectedJobId = job.job_id;
  await refreshJobs();
  renderJobDetail(job);
  startPolling(job.job_id);
}

document.querySelectorAll(".mode-tab").forEach((button) => {
  button.addEventListener("click", () => setMode(button.dataset.mode));
});

document.querySelectorAll(".detail-tab").forEach((button) => {
  button.addEventListener("click", () => {
    document.querySelectorAll(".detail-tab").forEach((tab) => tab.classList.toggle("active", tab === button));
    document.querySelectorAll(".detail-view").forEach((view) => view.classList.remove("active"));
    document.getElementById(`detail${button.dataset.detail.charAt(0).toUpperCase()}${button.dataset.detail.slice(1)}`).classList.add("active");
  });
});

document.querySelectorAll(".preset-pill").forEach((button) => {
  button.addEventListener("click", () => {
    elements.promptInput.value = button.dataset.preset;
  });
});

elements.imageInput.addEventListener("change", () => renderFileChips(elements.imageInput, elements.imageChips));
elements.documentInput.addEventListener("change", () => renderFileChips(elements.documentInput, elements.documentChips));
elements.connectBtn.addEventListener("click", async () => {
  try {
    await connectBackend();
  } catch (error) {
    elements.loginStatus.textContent = error.message;
  }
});
elements.runBtn.addEventListener("click", async () => {
  try {
    await createJob();
  } catch (error) {
    elements.runStateBadge.textContent = "Error";
    elements.loginStatus.textContent = error.message;
  }
});
elements.refreshJobsBtn.addEventListener("click", refreshJobs);
elements.statusFilter.addEventListener("change", renderJobs);
elements.severityFilter.addEventListener("change", renderJobs);

setMode(state.mode);
if (state.apiBase) {
  elements.loginStatus.textContent = "Ready to connect.";
  refreshJobs().catch(console.error);
}
