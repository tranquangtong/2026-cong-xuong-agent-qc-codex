const renderApiBase = "https://cong-xuong-agent-qc-api.onrender.com";
const isLocalHost = ["localhost", "127.0.0.1"].includes(window.location.hostname);
const defaultApiBase = localStorage.getItem("qcApiBase") || (isLocalHost ? "http://127.0.0.1:8000" : renderApiBase);
const uiCopy = {
  evidenceVi: "Bằng chứng",
  impactVi: "Ảnh hưởng",
  recommendedFixVi: "Đề xuất sửa",
  severityVi: "Mức độ",
};

const state = {
  mode: "id",
  jobs: [],
  selectedJobId: null,
  apiBase: defaultApiBase,
  pollTimer: null,
  pastedImages: [],
  reportDownloadUrl: null,
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
  imagePasteZone: document.getElementById("imagePasteZone"),
  imageBrowseBtn: document.getElementById("imageBrowseBtn"),
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
  reportDownloadBtn: document.getElementById("reportDownloadBtn"),
};

elements.apiBaseInput.value = state.apiBase;
elements.labelInput.value = localStorage.getItem("qcLabel") || "";

function apiUrl(path) {
  return `${state.apiBase.replace(/\/$/, "")}${path}`;
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function mojibakeScore(value) {
  return (value.match(/[ÃÂÄÅÆá»â€]/g) || []).length;
}

function vietnameseScore(value) {
  return (value.match(/[àáạảãâăđèéẹẻẽêìíịỉĩòóọỏõôơùúụủũưỳýỵỷỹÀÁẠẢÃÂĂĐÈÉẸẺẼÊÌÍỊỈĨÒÓỌỎÕÔƠÙÚỤỦŨƯỲÝỴỶỸ]/g) || []).length;
}

function repairText(value) {
  if (typeof value !== "string" || !/[ÃÂÄÅÆá»â€]/.test(value)) {
    return value ?? "";
  }
  try {
    const bytes = Uint8Array.from(Array.from(value, (character) => character.charCodeAt(0) & 0xff));
    const repaired = new TextDecoder("utf-8").decode(bytes);
    const originalScore = vietnameseScore(value) - mojibakeScore(value);
    const repairedScore = vietnameseScore(repaired) - mojibakeScore(repaired);
    return repairedScore > originalScore ? repaired : value;
  } catch {
    return value;
  }
}

function setMode(mode) {
  state.mode = mode;
  document.querySelectorAll(".mode-tab").forEach((button) => {
    button.classList.toggle("active", button.dataset.mode === mode);
  });
  elements.modeGuide.textContent = modeCopy[mode].guide;
  elements.modeExamples.innerHTML = modeCopy[mode].examples.map((item) => `<li>${escapeHtml(item)}</li>`).join("");
}

function setFiles(input, files) {
  const transfer = new DataTransfer();
  files.forEach((file) => transfer.items.add(file));
  input.files = transfer.files;
}

function makePastedFile(file, index) {
  const extension = file.type.split("/")[1] || "png";
  const name = file.name && file.name !== "image.png" ? file.name : `pasted-screenshot-${Date.now()}-${index + 1}.${extension}`;
  return new File([file], name, { type: file.type || "image/png", lastModified: Date.now() });
}

function selectedImageItems() {
  const fileItems = [...elements.imageInput.files].map((file, index) => ({
    kind: "input",
    key: `input-${index}-${file.name}-${file.size}-${file.lastModified}`,
    file,
  }));
  const pastedItems = state.pastedImages.map((file, index) => ({
    kind: "pasted",
    key: `pasted-${index}-${file.name}-${file.size}-${file.lastModified}`,
    file,
  }));
  return [...fileItems, ...pastedItems];
}

function removeImageItem(key) {
  if (key.startsWith("input-")) {
    const remaining = [...elements.imageInput.files].filter((file, index) => `input-${index}-${file.name}-${file.size}-${file.lastModified}` !== key);
    setFiles(elements.imageInput, remaining);
  } else {
    state.pastedImages = state.pastedImages.filter((file, index) => `pasted-${index}-${file.name}-${file.size}-${file.lastModified}` !== key);
  }
  renderImageChips();
}

function renderImageChips() {
  const items = selectedImageItems();
  elements.imageChips.innerHTML = items.length
    ? items
        .map(
          (item) => `
            <span class="chip">
              <span>${escapeHtml(item.file.name)}</span>
              <button type="button" data-remove-image="${escapeHtml(item.key)}" aria-label="Remove ${escapeHtml(item.file.name)}">x</button>
            </span>
          `
        )
        .join("")
    : "<span class='hint'>No screenshots selected yet.</span>";
  elements.imageChips.querySelectorAll("[data-remove-image]").forEach((button) => {
    button.addEventListener("click", () => removeImageItem(button.dataset.removeImage));
  });
}

function renderFileChips(input, container, emptyMessage) {
  container.innerHTML = "";
  if (!input.files.length) {
    container.innerHTML = `<span class="hint">${escapeHtml(emptyMessage)}</span>`;
    return;
  }
  [...input.files].forEach((file) => {
    const chip = document.createElement("span");
    chip.className = "chip";
    chip.textContent = file.name;
    container.appendChild(chip);
  });
}

function addPastedImages(fileList) {
  const images = fileList.filter((file) => file.type.startsWith("image/"));
  if (!images.length) {
    return false;
  }
  state.pastedImages = [...state.pastedImages, ...images.map(makePastedFile)];
  renderImageChips();
  elements.imagePasteZone.classList.add("is-focused");
  return true;
}

function filesFromDataTransferItems(items) {
  return [...items]
    .map((item) => (typeof item.getAsFile === "function" ? item.getAsFile() : null))
    .filter(Boolean);
}

function parseMarkdownTable(tableBlock) {
  const lines = tableBlock
    .split("\n")
    .map((line) => line.trim())
    .filter((line) => line.startsWith("|"));
  if (lines.length < 3) {
    return [];
  }
  return lines.slice(2).map((line) => line.slice(1, -1).split("|").map((cell) => repairText(cell.trim())));
}

function extractMarkdownTables(markdown) {
  return markdown.match(/\|[^\n]+\|\n\|[-| :]+\|\n(?:\|[^\n]+\|\n?)+/g) || [];
}

function isVietnameseFindingsTable(tableBlock) {
  const headerLine = tableBlock.split("\n")[0] || "";
  const headers = headerLine
    .slice(1, -1)
    .split("|")
    .map((cell) => repairText(cell.trim()));
  return headers.includes(uiCopy.severityVi) && headers.includes(uiCopy.evidenceVi) && headers.includes(uiCopy.recommendedFixVi);
}

function extractVietnameseFindingMap(reportMarkdown) {
  const markdown = repairText(reportMarkdown || "");
  const tableBlock = extractMarkdownTables(markdown).find(isVietnameseFindingsTable);
  if (!tableBlock) {
    return new Map();
  }
  const rows = parseMarkdownTable(tableBlock);
  const findingMap = new Map();
  rows.forEach((cells) => {
    if (cells.length < 6) {
      return;
    }
    findingMap.set(cells[0], {
      severity: cells[1],
      area: cells[2],
      evidence: cells[3],
      impact: cells[4],
      recommended_fix: cells[5],
    });
  });
  return findingMap;
}

function shouldShowSecondaryText(primaryText, secondaryText) {
  const primary = repairText(primaryText || "").replace(/\s+/g, " ").trim();
  const secondary = repairText(secondaryText || "").replace(/\s+/g, " ").trim();
  return Boolean(secondary) && secondary !== primary;
}

function singleField(label, text) {
  const value = repairText(text || "");
  return `
    <div class="finding-block">
      <p class="finding-label">${escapeHtml(label)}</p>
      <p class="finding-text">${escapeHtml(value)}</p>
    </div>
  `;
}

function bilingualField(labelEn, labelVi, englishText, vietnameseText) {
  const english = repairText(englishText || "");
  const vietnamese = repairText(vietnameseText || "");
  const showVietnamese = shouldShowSecondaryText(english, vietnamese);
  return `
    <div class="finding-block">
      <p class="finding-label">${escapeHtml(labelEn)} / ${escapeHtml(labelVi)}</p>
      <p class="finding-text">${escapeHtml(english)}</p>
      ${showVietnamese ? `<p class="finding-text vi-copy">${escapeHtml(vietnamese)}</p>` : ""}
    </div>
  `;
}

function updateReportDownload(job) {
  if (state.reportDownloadUrl) {
    URL.revokeObjectURL(state.reportDownloadUrl);
    state.reportDownloadUrl = null;
  }
  const reportArtifact = (job?.artifact_urls || []).find((item) => item.name === "report.md");
  const reportMarkdown = repairText(job?.report_markdown || "");
  if (reportArtifact) {
    elements.reportDownloadBtn.href = apiUrl(reportArtifact.url);
    elements.reportDownloadBtn.download = "report.md";
    elements.reportDownloadBtn.classList.remove("is-disabled");
    elements.reportDownloadBtn.setAttribute("aria-disabled", "false");
    return;
  }
  if (reportMarkdown) {
    state.reportDownloadUrl = URL.createObjectURL(new Blob([reportMarkdown], { type: "text/markdown;charset=utf-8" }));
    elements.reportDownloadBtn.href = state.reportDownloadUrl;
    elements.reportDownloadBtn.download = "report.md";
    elements.reportDownloadBtn.classList.remove("is-disabled");
    elements.reportDownloadBtn.setAttribute("aria-disabled", "false");
    return;
  }
  elements.reportDownloadBtn.href = "#";
  elements.reportDownloadBtn.classList.add("is-disabled");
  elements.reportDownloadBtn.setAttribute("aria-disabled", "true");
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
      const severitySummary =
        Object.entries(job.severity_counts || {})
          .map(([key, value]) => `${key}:${value}`)
          .join(" | ") || "No findings yet";
      return `
        <article class="job-card ${job.job_id === state.selectedJobId ? "active" : ""}" data-job-id="${escapeHtml(job.job_id)}">
          <div class="job-meta">
            <strong>${escapeHtml(job.mode.toUpperCase())}</strong>
            <span>${escapeHtml(repairText(job.status))}</span>
          </div>
          <h3>${escapeHtml(repairText(job.prompt_preview || "Untitled run"))}</h3>
          <p>${escapeHtml(repairText(severitySummary))}</p>
          <div class="job-meta">
            <span>${escapeHtml(repairText(job.created_at))}</span>
            <span>${escapeHtml(repairText(job.created_by_label))}</span>
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
    elements.findingCount.textContent = "0";
    elements.agentSummary.textContent = "-";
    elements.createdAt.textContent = "-";
    elements.severityStrip.innerHTML = "";
    elements.sourceSummary.innerHTML = "<p class='hint'>No source summary yet.</p>";
    elements.findingsTable.innerHTML = "<div class='finding-empty'>Findings will appear here when the run completes.</div>";
    updateReportDownload(null);
    return;
  }

  const translatedFindings = extractVietnameseFindingMap(job.report_markdown);
  elements.detailTitle.textContent = `${repairText(job.mode.toUpperCase())} run - ${repairText(job.job_id)}`;
  elements.detailStatus.textContent = repairText(job.status);
  elements.findingCount.textContent = String(job.findings_count || 0);
  const agents = [...new Set((job.findings || []).map((finding) => repairText(finding.source_agent)))];
  elements.agentSummary.textContent = agents.length ? agents.join(", ") : "Pending";
  elements.createdAt.textContent = repairText(job.created_at);
  elements.severityStrip.innerHTML = Object.entries(job.severity_counts || {})
    .map(([severity, count]) => `<span class="severity-pill">${escapeHtml(repairText(severity))}: ${escapeHtml(count)}</span>`)
    .join("");
  elements.sourceSummary.innerHTML = (job.source_summary || []).length
    ? `<h3>Source Summary</h3><ul>${job.source_summary.map((item) => `<li>${escapeHtml(repairText(item))}</li>`).join("")}</ul>`
    : "<p class='hint'>No source summary yet.</p>";
  elements.findingsTable.innerHTML = (job.findings || []).length
    ? job.findings
        .map((finding) => {
          const translated = translatedFindings.get(finding.id) || {};
          const translatedArea = repairText(translated.area || "");
          const showVietnameseArea = shouldShowSecondaryText(finding.area, translatedArea);
          return `
            <article class="finding-card">
              <div class="finding-top">
                <div class="finding-title">
                  <strong>${escapeHtml(repairText(finding.id))} - ${escapeHtml(repairText(finding.area))}</strong>
                  ${showVietnameseArea ? `<span class="vi-copy">${escapeHtml(translatedArea)}</span>` : ""}
                </div>
                <span class="severity-${escapeHtml(finding.severity.toLowerCase())}">${escapeHtml(repairText(finding.severity))}</span>
              </div>
              ${singleField("Agent", finding.source_agent)}
              ${bilingualField("Evidence", uiCopy.evidenceVi, finding.evidence, translated.evidence)}
              ${bilingualField("Impact", uiCopy.impactVi, finding.impact, translated.impact)}
              ${bilingualField("Recommended fix", uiCopy.recommendedFixVi, finding.recommended_fix, translated.recommended_fix)}
            </article>
          `;
        })
        .join("")
    : "<div class='finding-empty'>Findings will appear here when the run completes.</div>";
  updateReportDownload(job);
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
  state.pastedImages.forEach((file) => form.append("images", file));
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

document.querySelectorAll(".preset-pill").forEach((button) => {
  button.addEventListener("click", () => {
    elements.promptInput.value = button.dataset.preset;
  });
});

elements.imageBrowseBtn.addEventListener("click", (event) => {
  event.stopPropagation();
  elements.imageInput.click();
});

elements.imagePasteZone.addEventListener("click", () => {
  elements.imagePasteZone.focus();
});

elements.imagePasteZone.addEventListener("focus", () => {
  elements.imagePasteZone.classList.add("is-focused");
});

elements.imagePasteZone.addEventListener("blur", () => {
  elements.imagePasteZone.classList.remove("is-focused");
});

elements.imagePasteZone.addEventListener("paste", (event) => {
  const files = filesFromDataTransferItems(event.clipboardData?.items || []);
  if (addPastedImages(files)) {
    event.preventDefault();
  }
});

document.addEventListener("paste", (event) => {
  const target = event.target;
  const isTypingTarget =
    target instanceof HTMLInputElement ||
    target instanceof HTMLTextAreaElement ||
    target?.isContentEditable;
  if (isTypingTarget) {
    return;
  }
  const files = filesFromDataTransferItems(event.clipboardData?.items || []);
  if (addPastedImages(files)) {
    event.preventDefault();
  }
});

elements.imagePasteZone.addEventListener("dragover", (event) => {
  event.preventDefault();
  elements.imagePasteZone.classList.add("is-dragover");
});

elements.imagePasteZone.addEventListener("dragleave", () => {
  elements.imagePasteZone.classList.remove("is-dragover");
});

elements.imagePasteZone.addEventListener("drop", (event) => {
  event.preventDefault();
  elements.imagePasteZone.classList.remove("is-dragover");
  addPastedImages([...event.dataTransfer.files]);
});

elements.imageInput.addEventListener("change", renderImageChips);
elements.documentInput.addEventListener("change", () => renderFileChips(elements.documentInput, elements.documentChips, "No documents selected yet."));
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
elements.reportDownloadBtn.addEventListener("click", (event) => {
  if (elements.reportDownloadBtn.classList.contains("is-disabled")) {
    event.preventDefault();
  }
});

setMode(state.mode);
renderImageChips();
renderFileChips(elements.documentInput, elements.documentChips, "No documents selected yet.");
renderJobDetail(null);
if (state.apiBase) {
  elements.loginStatus.textContent = "Ready to connect.";
  refreshJobs().catch(console.error);
}
