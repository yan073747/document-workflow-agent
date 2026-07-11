const API_BASE = window.location.origin.includes("8020") ? "" : "http://127.0.0.1:8020";

let currentTaskId = null;
let allHistoryTasks = [];

const taskForm = document.querySelector("#taskForm");
const objectiveInput = document.querySelector("#objective");
const fileInput = document.querySelector("#file");
const taskStatus = document.querySelector("#taskStatus");
const taskIdText = document.querySelector("#taskIdText");
const planList = document.querySelector("#planList");
const traceList = document.querySelector("#traceList");
const reportBox = document.querySelector("#reportBox");
const confirmButton = document.querySelector("#confirmButton");
const graphBox = document.querySelector("#graphBox");
const providerText = document.querySelector("#providerText");
const downloadMarkdownButton = document.querySelector("#downloadMarkdownButton");
const downloadPdfButton = document.querySelector("#downloadPdfButton");
const historyList = document.querySelector("#historyList");
const historyFilter = document.querySelector("#historyFilter");
const refreshHistoryButton = document.querySelector("#refreshHistoryButton");
const metricTotal = document.querySelector("#metricTotal");
const metricCompleted = document.querySelector("#metricCompleted");
const metricWaiting = document.querySelector("#metricWaiting");
const metricReports = document.querySelector("#metricReports");
const retryBox = document.querySelector("#retryBox");
const retryFile = document.querySelector("#retryFile");
const retryButton = document.querySelector("#retryButton");

loadWorkflowGraph();
loadProviderStatus();
loadTaskHistory();

taskForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  if (!fileInput.files.length) {
    alert("请先选择销售 CSV 或 Excel 文件。");
    return;
  }

  const form = new FormData();
  form.append("objective", objectiveInput.value.trim());
  form.append("file", fileInput.files[0]);

  setBusy("正在创建任务...");
  setDownloadButtons(false);
  const response = await fetch(`${API_BASE}/api/tasks`, {
    method: "POST",
    body: form,
  });

  if (!response.ok) {
    const error = await response.text();
    setBusy("任务创建失败");
    alert(error);
    return;
  }

  const payload = await response.json();
  currentTaskId = payload.task.id;
  renderTask(payload.task, payload.trace);
  confirmButton.disabled = false;
  await loadTaskHistory();
});

confirmButton.addEventListener("click", async () => {
  if (!currentTaskId) return;
  confirmButton.disabled = true;
  setBusy("Agent 正在执行...");

  const response = await fetch(`${API_BASE}/api/tasks/${currentTaskId}/confirm`, {
    method: "POST",
  });

  if (!response.ok) {
    const error = await response.text();
    setBusy("执行失败");
    alert(error);
    return;
  }

  const payload = await response.json();
  renderTask(payload.task, payload.trace);
  await loadTaskHistory();
});

downloadMarkdownButton.addEventListener("click", () => {
  downloadReport("md");
});

downloadPdfButton.addEventListener("click", () => {
  downloadReport("pdf");
});

refreshHistoryButton.addEventListener("click", () => {
  loadTaskHistory();
});

historyFilter.addEventListener("change", () => {
  renderHistory();
});

retryButton.addEventListener("click", async () => {
  if (!currentTaskId) return;
  const form = new FormData();
  if (retryFile.files.length) {
    form.append("file", retryFile.files[0]);
  }

  setBusy("正在重新规划失败任务...");
  const response = await fetch(`${API_BASE}/api/tasks/${currentTaskId}/retry`, {
    method: "POST",
    body: form,
  });

  if (!response.ok) {
    const error = await response.text();
    setBusy("重试启动失败");
    alert(error);
    return;
  }

  const payload = await response.json();
  retryFile.value = "";
  renderTask(payload.task, payload.trace);
  await loadTaskHistory();
});

function setBusy(message) {
  taskStatus.textContent = message;
}

function renderTask(task, trace) {
  currentTaskId = task.id;
  taskStatus.textContent = statusLabel(task.status);
  taskStatus.dataset.status = task.status;
  taskIdText.textContent = `任务 ID：${task.id}`;
  renderPlan(task.plan || []);
  renderTrace(trace || []);
  reportBox.textContent = task.report_markdown || "任务完成后，报告会显示在这里。";
  setDownloadButtons(Boolean(task.report_markdown));
  confirmButton.disabled = task.status !== "waiting_human_confirm";
  retryBox.classList.toggle("hidden", task.status !== "failed");
}

function renderPlan(plan) {
  if (!plan.length) {
    planList.className = "empty";
    planList.textContent = "任务创建后，Planner Agent 会在这里生成计划。";
    return;
  }

  planList.className = "";
  planList.innerHTML = plan
    .map(
      (step) => `
        <article class="plan-item">
          <strong>${step.order}. ${escapeHtml(step.agent)}</strong>
          <p>${escapeHtml(step.action)}</p>
          <p>输出：${escapeHtml(step.expected_output)}</p>
        </article>
      `,
    )
    .join("");
}

function renderTrace(trace) {
  if (!trace.length) {
    traceList.className = "trace empty";
    traceList.textContent = "暂无执行记录。";
    return;
  }

  traceList.className = "trace";
  traceList.innerHTML = trace
    .map(
      (event) => `
        <article class="trace-item">
          <strong>
            ${escapeHtml(event.agent)} / ${escapeHtml(event.node)}
            <span class="trace-status ${escapeHtml(event.status)}">${escapeHtml(event.status)}</span>
          </strong>
          <p>${escapeHtml(event.output_summary || event.input_summary || event.error_message || "已记录执行事件。")}</p>
        </article>
      `,
    )
    .join("");
}

function statusLabel(status) {
  const labels = {
    created: "已创建",
    planning: "规划中",
    waiting_human_confirm: "等待人工确认",
    analyzing: "分析中",
    writing_report: "报告生成中",
    reviewing: "审核中",
    completed: "已完成",
    failed: "失败",
  };
  return labels[status] || status;
}

function setDownloadButtons(enabled) {
  downloadMarkdownButton.disabled = !enabled;
  downloadPdfButton.disabled = !enabled;
}

function downloadReport(format) {
  if (!currentTaskId) return;
  window.location.href = `${API_BASE}/api/tasks/${currentTaskId}/report.${format}`;
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

async function loadWorkflowGraph() {
  try {
    const response = await fetch(`${API_BASE}/api/workflow/graph`);
    const payload = await response.json();
    graphBox.innerHTML = Object.entries(payload.graphs)
      .map(([name, nodes]) => renderGraphColumn(name, nodes))
      .join("");
  } catch (error) {
    graphBox.textContent = "工作流图读取失败，请确认后端服务已启动。";
  }
}

async function loadProviderStatus() {
  try {
    const response = await fetch(`${API_BASE}/api/llm/status`);
    const payload = await response.json();
    const mode = payload.enabled ? "远程 LLM" : "本地规则回退";
    providerText.textContent = `${mode}：${payload.provider} / ${payload.model}`;
  } catch (error) {
    providerText.textContent = "模型状态读取失败";
  }
}

async function loadTaskHistory() {
  try {
    const response = await fetch(`${API_BASE}/api/tasks`);
    const payload = await response.json();
    allHistoryTasks = payload.items || [];
    renderMetrics();
    renderHistory();
    await loadInitialTaskFromQuery();
  } catch (error) {
    historyList.className = "history-list empty";
    historyList.textContent = "历史任务读取失败。";
  }
}

async function loadInitialTaskFromQuery() {
  const taskId = new URLSearchParams(window.location.search).get("taskId");
  if (!taskId || currentTaskId === taskId) return;
  if (!allHistoryTasks.some((task) => task.id === taskId)) return;
  await loadTaskDetail(taskId);
}

function renderMetrics() {
  const total = allHistoryTasks.length;
  const completed = allHistoryTasks.filter((task) => task.status === "completed").length;
  const waiting = allHistoryTasks.filter((task) => task.status === "waiting_human_confirm").length;
  const reports = allHistoryTasks.filter((task) => task.has_report).length;
  metricTotal.textContent = total;
  metricCompleted.textContent = completed;
  metricWaiting.textContent = waiting;
  metricReports.textContent = reports;
}

function renderHistory() {
  const filter = historyFilter.value;
  const tasks = filter === "all" ? allHistoryTasks : allHistoryTasks.filter((task) => task.status === filter);

  if (!tasks.length) {
    historyList.className = "history-list empty";
    historyList.textContent = "暂无符合条件的历史任务。";
    return;
  }

  historyList.className = "history-list";
  historyList.innerHTML = tasks.map((task) => renderHistoryItem(task)).join("");
  document.querySelectorAll("[data-task-id]").forEach((button) => {
    button.addEventListener("click", () => {
      loadTaskDetail(button.dataset.taskId);
    });
  });
}

function renderHistoryItem(task) {
  const activeClass = task.id === currentTaskId ? "active" : "";
  const reportText = task.has_report ? "已生成报告" : "暂无报告";
  return `
    <button class="history-item ${activeClass}" type="button" data-task-id="${escapeHtml(task.id)}">
      <span class="history-main">
        <strong>${escapeHtml(shortText(task.objective, 52))}</strong>
        <small>${escapeHtml(formatDateTime(task.created_at))}</small>
      </span>
      <span class="history-meta">
        <span class="status-badge status-${escapeHtml(task.status)}">${escapeHtml(statusLabel(task.status))}</span>
        <span>${task.plan_step_count} 步计划</span>
        <span>${task.trace_count} 条 Trace</span>
        <span>${escapeHtml(reportText)}</span>
      </span>
    </button>
  `;
}

async function loadTaskDetail(taskId) {
  setBusy("正在加载历史任务...");
  const response = await fetch(`${API_BASE}/api/tasks/${taskId}`);
  if (!response.ok) {
    const error = await response.text();
    setBusy("历史任务加载失败");
    alert(error);
    return;
  }

  const payload = await response.json();
  renderTask(payload.task, payload.trace);
  renderHistory();
}

function renderGraphColumn(name, nodes) {
  const title = name === "planning" ? "规划图：生成计划并暂停" : "执行图：确认后自动运行";
  const chain = nodes
    .map((node) => `<span class="node-pill">${escapeHtml(node)}</span>`)
    .join(`<span class="node-arrow">→</span>`);
  return `
    <div class="graph-column">
      <h3>${title}</h3>
      <div class="node-chain">${chain}</div>
    </div>
  `;
}

function shortText(value, maxLength) {
  const text = String(value || "");
  return text.length > maxLength ? `${text.slice(0, maxLength)}...` : text;
}

function formatDateTime(value) {
  if (!value) return "";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return String(value);
  return date.toLocaleString("zh-CN", {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}
