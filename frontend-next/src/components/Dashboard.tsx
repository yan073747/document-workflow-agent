"use client";

import {
  Activity,
  Bot,
  CheckCircle2,
  Database,
  Download,
  FileSpreadsheet,
  Loader2,
  RefreshCw,
  ShieldCheck
} from "lucide-react";
import { FormEvent, useEffect, useMemo, useState } from "react";
import { AnalyticsCharts, type ChartMetricItem } from "@/components/AnalyticsCharts";
import { apiGet, apiPost, apiPostForm, apiPostJson, downloadReportFile } from "@/lib/api";
import {
  clearDemoHistoryState,
  getDemoHistorySummaries,
  getDemoTaskPayload,
  readDemoHistoryState,
  upsertDemoTaskPayload,
  writeDemoHistoryState
} from "@/lib/demoHistory";

type TaskStatus =
  | "created"
  | "planning"
  | "queued"
  | "waiting_human_confirm"
  | "analyzing"
  | "writing_report"
  | "reviewing"
  | "completed"
  | "failed";

type PlanStep = {
  order: number;
  agent: string;
  action: string;
  expected_output: string;
};

type SalesAnalysis = {
  total_revenue: number;
  order_count: number;
  total_quantity: number;
  average_order_value: number;
  top_regions: ChartMetricItem[];
  top_categories: ChartMetricItem[];
  monthly_trend: ChartMetricItem[];
  region_ranking: ChartMetricItem[];
  category_ranking: ChartMetricItem[];
  salesperson_ranking: ChartMetricItem[];
  customer_mix: Record<string, number>;
  insights: string[];
};

type TaskRecord = {
  id: string;
  objective: string;
  file_path: string;
  status: TaskStatus;
  plan: PlanStep[];
  analysis: SalesAnalysis | null;
  report_markdown: string;
  created_at: string;
  updated_at: string;
};

type TraceEvent = {
  id: number | null;
  task_id: string;
  node: string;
  agent: string;
  status: "started" | "completed" | "failed" | "waiting";
  input_summary: string;
  output_summary: string;
  error_message: string;
  retry_count: number;
  created_at: string | null;
};

type TaskSummary = {
  id: string;
  objective: string;
  status: TaskStatus;
  has_report: boolean;
  plan_step_count: number;
  trace_count: number;
  created_at: string;
  updated_at: string;
};

type TaskPayload = {
  task: TaskRecord;
  trace: TraceEvent[];
};

type WorkflowGraphPayload = {
  engine: string;
  graphs: Record<string, string[]>;
  human_confirm_node: string;
  llm_provider: ProviderStatus;
  description: string;
};

type ProviderStatus = {
  provider: string;
  model: string;
  enabled: boolean;
  base_url?: string;
};

type AuthUser = {
  id: string;
  email: string;
};

type AuthTokenResponse = {
  access_token: string;
  token_type: string;
  user: AuthUser;
};

const defaultObjective = "分析销售订单数据，识别重点区域、热销品类和经营风险，并生成一份管理层可读的经营报告。";

const statusLabels: Record<TaskStatus, string> = {
  created: "已创建",
  planning: "规划中",
  queued: "队列中",
  waiting_human_confirm: "等待人工确认",
  analyzing: "分析中",
  writing_report: "生成报告中",
  reviewing: "审核中",
  completed: "已完成",
  failed: "失败"
};

export function Dashboard() {
  const [token, setToken] = useState<string | null>(null);
  const [user, setUser] = useState<AuthUser | null>(null);
  const [objective, setObjective] = useState(defaultObjective);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [currentTask, setCurrentTask] = useState<TaskRecord | null>(null);
  const [trace, setTrace] = useState<TraceEvent[]>([]);
  const [history, setHistory] = useState<TaskSummary[]>([]);
  const [historyFilter, setHistoryFilter] = useState<TaskStatus | "all">("all");
  const [graph, setGraph] = useState<WorkflowGraphPayload | null>(null);
  const [provider, setProvider] = useState<ProviderStatus | null>(null);
  const [busyText, setBusyText] = useState("等待创建任务");
  const [errorText, setErrorText] = useState("");
  const [loginEmail, setLoginEmail] = useState("demo@example.com");
  const [loginPassword, setLoginPassword] = useState("demo123456");

  useEffect(() => {
    const storedToken = window.localStorage.getItem("workflow_token");
    if (!storedToken) return;
    setToken(storedToken);
    void apiGet<AuthUser>("/api/auth/me", { token: storedToken })
      .then((nextUser) => {
        setUser(nextUser);
        return Promise.all([loadWorkflowGraph(), loadProviderStatus(), loadTaskHistory(storedToken)]);
      })
      .catch(() => {
        window.localStorage.removeItem("workflow_token");
        setToken(null);
        setUser(null);
      });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function loadWorkflowGraph() {
    try {
      setGraph(await apiGet<WorkflowGraphPayload>("/api/workflow/graph"));
    } catch {
      setGraph(null);
    }
  }

  async function loadProviderStatus() {
    try {
      setProvider(await apiGet<ProviderStatus>("/api/llm/status"));
    } catch {
      setProvider(null);
    }
  }

  async function loadTaskHistory(nextToken = token) {
    if (!nextToken) return;
    const state = readDemoHistoryState(window.localStorage);
    setHistory(getDemoHistorySummaries(state) as TaskSummary[]);
  }

  async function loadTaskDetail(taskId: string) {
    if (!token) return;
    setBusyText("正在加载任务详情...");
    setErrorText("");
    try {
      const savedPayload = getDemoTaskPayload(readDemoHistoryState(window.localStorage), taskId);
      if (savedPayload) {
        renderPayload(savedPayload as TaskPayload);
        return;
      }
      const payload = await apiGet<TaskPayload>(`/api/tasks/${taskId}`, { token });
      persistPayload(payload);
      renderPayload(payload);
    } catch (error) {
      showError(error, "任务详情加载失败");
    }
  }

  function persistPayload(payload: TaskPayload) {
    const nextState = upsertDemoTaskPayload(readDemoHistoryState(window.localStorage), payload);
    writeDemoHistoryState(window.localStorage, nextState);
    setHistory(getDemoHistorySummaries(nextState) as TaskSummary[]);
  }

  function renderPayload(payload: TaskPayload) {
    setCurrentTask(payload.task);
    setTrace(payload.trace || []);
    setBusyText(statusLabels[payload.task.status] || payload.task.status);
  }

  async function handleCreateTask(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!token) return;
    if (!selectedFile) {
      setErrorText("请先选择一份 CSV 或 Excel 文件。");
      return;
    }

    const form = new FormData();
    form.append("objective", objective.trim());
    form.append("file", selectedFile);

    setBusyText("Planner Agent 正在生成执行计划...");
    setErrorText("");
    try {
      const payload = await apiPostForm<TaskPayload>("/api/tasks", form, { token });
      persistPayload(payload);
      renderPayload(payload);
    } catch (error) {
      showError(error, "任务创建失败");
    }
  }

  async function handleConfirmTask() {
    if (!currentTask || !token) return;
    setBusyText("Agent 团队正在分析数据...");
    setErrorText("");
    try {
      const payload = await apiPost<TaskPayload>(`/api/tasks/${currentTask.id}/confirm`, { token });
      persistPayload(payload);
      renderPayload(payload);
    } catch (error) {
      showError(error, "执行失败");
    }
  }

  function showError(error: unknown, fallback: string) {
    setBusyText(fallback);
    setErrorText(error instanceof Error ? error.message : fallback);
  }

  async function handleLogin(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setErrorText("");
    setBusyText("正在登录演示账号...");
    try {
      const payload = await apiPostJson<AuthTokenResponse>("/api/auth/login", {
        email: loginEmail,
        password: loginPassword
      });
      window.localStorage.setItem("workflow_token", payload.access_token);
      setToken(payload.access_token);
      setUser(payload.user);
      await Promise.all([loadWorkflowGraph(), loadProviderStatus(), loadTaskHistory(payload.access_token)]);
      setBusyText("等待创建任务");
    } catch (error) {
      showError(error, "登录失败");
    }
  }

  function handleLogout() {
    window.localStorage.removeItem("workflow_token");
    setToken(null);
    setUser(null);
    setCurrentTask(null);
    setTrace([]);
    setHistory([]);
    setBusyText("等待创建任务");
  }

  function handleClearDemoHistory() {
    clearDemoHistoryState(window.localStorage);
    setHistory([]);
    setCurrentTask(null);
    setTrace([]);
    setBusyText("等待创建任务");
  }

  async function handleDownload(format: "md" | "pdf") {
    if (!currentTask || !token || !currentTask.report_markdown) return;
    try {
      await downloadReportFile(currentTask.id, format, token);
    } catch (error) {
      showError(error, "报告下载失败");
    }
  }

  const filteredHistory = useMemo(() => {
    return historyFilter === "all" ? history : history.filter((task) => task.status === historyFilter);
  }, [history, historyFilter]);

  const metrics = useMemo(() => {
    return {
      total: history.length,
      completed: history.filter((task) => task.status === "completed").length,
      waiting: history.filter((task) => task.status === "waiting_human_confirm").length,
      reports: history.filter((task) => task.has_report).length
    };
  }, [history]);

  const providerMode = provider
    ? `${provider.enabled ? "规则引擎演示模式" : "本地演示模式"} · ${provider.provider} / ${provider.model}`
    : "模型状态读取失败";

  return (
    <main className="shell">
      <nav className="topbar">
        <div className="brand">
          <span className="brand-mark">DW</span>
          <div>
            <strong>Document Workflow Agent</strong>
            <small>Vercel serverless demo</small>
          </div>
        </div>
        <div className="topbar-meta">
          {user ? <span>{user.email}</span> : null}
          <span>Next.js</span>
          <span>Serverless API</span>
          <span>Agent Workflow</span>
        </div>
      </nav>

      <section className="hero">
        <div>
          <p className="eyebrow">Agent Demo 01</p>
          <h1>文档工作流 Agent 控制台</h1>
          <p className="subtitle">
            上传销售表格，系统模拟 Planner、Data Analyst、Writer、Reviewer 协作完成计划生成、人工确认、数据分析和报告输出。
          </p>
        </div>
        <div className="status-card">
          {busyText.includes("正在") ? <Loader2 className="spin" size={18} /> : <Activity size={18} />}
          <div>
            <strong>{busyText}</strong>
            <p>{currentTask ? `任务 ID：${currentTask.id}` : "等待上传演示文件"}</p>
            <p>{providerMode}</p>
          </div>
        </div>
      </section>

      {errorText ? <div className="error-banner">{errorText}</div> : null}

      {!token ? (
        <section className="login-layout">
          <form className="panel login-panel" onSubmit={handleLogin}>
            <div className="panel-title">
              <span>L</span>
              <h2>登录演示账号</h2>
            </div>
            <label>
              邮箱
              <input value={loginEmail} onChange={(event) => setLoginEmail(event.target.value)} />
            </label>
            <label>
              密码
              <input
                type="password"
                value={loginPassword}
                onChange={(event) => setLoginPassword(event.target.value)}
              />
            </label>
            <button type="submit">
              <ShieldCheck size={18} />
              进入控制台
            </button>
            <p className="hint">默认账号：demo@example.com / demo123456</p>
          </form>
        </section>
      ) : (
        <>
          <div className="session-row">
            <span>当前用户：{user?.email || "已登录"}</span>
            <button className="secondary-button" type="button" onClick={handleLogout}>
              退出登录
            </button>
          </div>

          <section className="metrics-grid" aria-label="任务概览">
            <MetricCard label="任务总数" value={metrics.total} icon={<Database size={18} />} />
            <MetricCard label="已完成" value={metrics.completed} icon={<CheckCircle2 size={18} />} />
            <MetricCard label="待确认" value={metrics.waiting} icon={<ShieldCheck size={18} />} />
            <MetricCard label="可下载报告" value={metrics.reports} icon={<Download size={18} />} />
          </section>

          <section className="workspace">
            <form className="panel" onSubmit={handleCreateTask}>
              <PanelTitle marker="1" title="创建分析任务" />
              <label>
                分析目标
                <textarea value={objective} rows={5} onChange={(event) => setObjective(event.target.value)} />
              </label>
              <label>
                销售数据文件
                <input
                  type="file"
                  accept=".csv,.xlsx"
                  onChange={(event) => setSelectedFile(event.target.files?.[0] || null)}
                />
              </label>
              <button type="submit">
                <FileSpreadsheet size={18} />
                上传并生成执行计划
              </button>
              <p className="hint">可使用仓库里的 sample-data/sales_orders.xlsx；线上演示会使用安全样例数据。</p>
            </form>

            <section className="panel">
              <PanelTitle marker="2" title="执行计划" />
              <PlanList plan={currentTask?.plan || []} />
              <button
                type="button"
                disabled={currentTask?.status !== "waiting_human_confirm"}
                onClick={handleConfirmTask}
              >
                <Bot size={18} />
                确认计划并继续执行
              </button>
            </section>
          </section>

          <section className="panel graph-panel">
            <PanelTitle marker="G" title="Agent 工作流图" />
            <WorkflowGraph graph={graph} />
          </section>

          <section className="panel history-panel">
            <div className="panel-title split-title">
              <div className="title-left">
                <span>H</span>
                <h2>任务历史</h2>
              </div>
              <div className="history-actions">
                <select
                  aria-label="筛选任务状态"
                  value={historyFilter}
                  onChange={(event) => setHistoryFilter(event.target.value as TaskStatus | "all")}
                >
                  <option value="all">全部</option>
                  <option value="waiting_human_confirm">等待确认</option>
                  <option value="completed">已完成</option>
                  <option value="failed">失败</option>
                </select>
                <button className="secondary-button" type="button" onClick={() => void loadTaskHistory()}>
                  <RefreshCw size={16} />
                  刷新
                </button>
                <button className="secondary-button" type="button" onClick={handleClearDemoHistory}>
                  清空
                </button>
              </div>
            </div>
            <HistoryList
              tasks={filteredHistory}
              activeTaskId={currentTask?.id}
              onSelectTask={(taskId) => void loadTaskDetail(taskId)}
            />
          </section>

          <AnalyticsCharts analysis={currentTask?.analysis || null} />

          <section className="grid">
            <section className="panel">
              <PanelTitle marker="3" title="Agent Trace" />
              <TraceList trace={trace} />
            </section>

            <section className="panel">
              <div className="panel-title split-title">
                <div className="title-left">
                  <span>4</span>
                  <h2>报告预览</h2>
                </div>
                <div className="download-actions">
                  <a
                    className={`secondary-link ${currentTask?.report_markdown ? "" : "disabled"}`}
                    href="#"
                    onClick={(event) => {
                      event.preventDefault();
                      void handleDownload("md");
                    }}
                  >
                    <Download size={16} />
                    MD
                  </a>
                  <a
                    className={`secondary-link ${currentTask?.report_markdown ? "" : "disabled"}`}
                    href="#"
                    onClick={(event) => {
                      event.preventDefault();
                      void handleDownload("pdf");
                    }}
                  >
                    <Download size={16} />
                    PDF
                  </a>
                </div>
              </div>
              <pre className="report">{currentTask?.report_markdown || "任务完成后，报告会显示在这里。"}</pre>
            </section>
          </section>
        </>
      )}
    </main>
  );
}

function MetricCard({ label, value, icon }: { label: string; value: number; icon: React.ReactNode }) {
  return (
    <article className="metric-card">
      <span>{icon}</span>
      <div>
        <small>{label}</small>
        <strong>{value}</strong>
      </div>
    </article>
  );
}

function PanelTitle({ marker, title }: { marker: string; title: string }) {
  return (
    <div className="panel-title">
      <span>{marker}</span>
      <h2>{title}</h2>
    </div>
  );
}

function PlanList({ plan }: { plan: PlanStep[] }) {
  if (!plan.length) {
    return <div className="empty">创建任务后，Planner Agent 会在这里生成可确认的执行计划。</div>;
  }
  return (
    <div>
      {plan.map((step) => (
        <article className="plan-item" key={`${step.order}-${step.agent}`}>
          <strong>
            {step.order}. {step.agent}
          </strong>
          <p>{step.action}</p>
          <p>输出：{step.expected_output}</p>
        </article>
      ))}
    </div>
  );
}

function WorkflowGraph({ graph }: { graph: WorkflowGraphPayload | null }) {
  if (!graph) {
    return <div className="empty">工作流图读取失败，请确认 API 已启动。</div>;
  }
  return (
    <div className="graph-box">
      {Object.entries(graph.graphs).map(([name, nodes]) => (
        <div className="graph-column" key={name}>
          <h3>{name === "planning" ? "规划图：生成计划并等待确认" : "执行图：确认后自动运行"}</h3>
          <div className="node-chain">
            {nodes.map((node, index) => (
              <div className="node-segment" key={node}>
                <span className="node-pill">{node}</span>
                {index < nodes.length - 1 ? <span className="node-arrow">→</span> : null}
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}

function HistoryList({
  tasks,
  activeTaskId,
  onSelectTask
}: {
  tasks: TaskSummary[];
  activeTaskId?: string;
  onSelectTask: (taskId: string) => void;
}) {
  if (!tasks.length) {
    return <div className="history-list empty">暂无符合条件的任务。</div>;
  }
  return (
    <div className="history-list">
      {tasks.map((task) => (
        <button
          className={`history-item ${task.id === activeTaskId ? "active" : ""}`}
          key={task.id}
          type="button"
          onClick={() => onSelectTask(task.id)}
        >
          <span className="history-main">
            <strong>{shortText(task.objective, 52)}</strong>
            <small>{formatDateTime(task.created_at)}</small>
          </span>
          <span className="history-meta">
            <span className={`status-badge status-${task.status}`}>{statusLabels[task.status]}</span>
            <span>{task.plan_step_count} 步计划</span>
            <span>{task.trace_count} 条 Trace</span>
            <span>{task.has_report ? "已生成报告" : "暂无报告"}</span>
          </span>
        </button>
      ))}
    </div>
  );
}

function TraceList({ trace }: { trace: TraceEvent[] }) {
  if (!trace.length) {
    return <div className="trace empty">暂无执行记录。</div>;
  }
  return (
    <div className="trace">
      {trace.map((event) => (
        <article className="trace-item" key={event.id || `${event.node}-${event.created_at}`}>
          <strong>
            {event.agent} / {event.node}
            <span className={`trace-status ${event.status}`}>{event.status}</span>
          </strong>
          <p>{event.error_message || event.output_summary || event.input_summary || "已记录执行事件。"}</p>
        </article>
      ))}
    </div>
  );
}

function shortText(value: string, maxLength: number): string {
  return value.length > maxLength ? `${value.slice(0, maxLength)}...` : value;
}

function formatDateTime(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString("zh-CN", {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit"
  });
}
