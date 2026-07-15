export type DemoTaskStatus =
  | "created"
  | "planning"
  | "queued"
  | "waiting_human_confirm"
  | "analyzing"
  | "writing_report"
  | "reviewing"
  | "completed"
  | "failed";

export type DemoPlanStep = {
  order: number;
  agent: string;
  action: string;
  expected_output: string;
};

export type DemoTaskRecord = {
  id: string;
  objective: string;
  file_path: string;
  status: DemoTaskStatus;
  plan: DemoPlanStep[];
  analysis: unknown;
  report_markdown: string;
  created_at: string;
  updated_at: string;
};

export type DemoTraceEvent = {
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

export type DemoTaskPayload = {
  task: DemoTaskRecord;
  trace: DemoTraceEvent[];
};

export type DemoTaskSummary = {
  id: string;
  objective: string;
  status: DemoTaskStatus;
  has_report: boolean;
  plan_step_count: number;
  trace_count: number;
  created_at: string;
  updated_at: string;
};

export type DemoHistoryState = {
  payloads: Record<string, DemoTaskPayload>;
};

export const DEMO_HISTORY_STORAGE_KEY = "document_workflow_demo_history_v1";

export function createEmptyDemoHistoryState(): DemoHistoryState {
  return { payloads: {} };
}

export function upsertDemoTaskPayload(state: DemoHistoryState, payload: DemoTaskPayload): DemoHistoryState {
  return {
    payloads: {
      ...state.payloads,
      [payload.task.id]: payload
    }
  };
}

export function getDemoTaskPayload(state: DemoHistoryState, taskId: string): DemoTaskPayload | null {
  return state.payloads[taskId] || null;
}

export function getDemoHistorySummaries(state: DemoHistoryState): DemoTaskSummary[] {
  return Object.values(state.payloads)
    .map((payload) => ({
      id: payload.task.id,
      objective: payload.task.objective,
      status: payload.task.status,
      has_report: Boolean(payload.task.report_markdown),
      plan_step_count: payload.task.plan.length,
      trace_count: payload.trace.length,
      created_at: payload.task.created_at,
      updated_at: payload.task.updated_at
    }))
    .sort((left, right) => new Date(right.updated_at).getTime() - new Date(left.updated_at).getTime());
}

export function readDemoHistoryState(storage: Storage): DemoHistoryState {
  const raw = storage.getItem(DEMO_HISTORY_STORAGE_KEY);
  if (!raw) return createEmptyDemoHistoryState();

  try {
    const parsed = JSON.parse(raw) as Partial<DemoHistoryState>;
    if (!parsed.payloads || typeof parsed.payloads !== "object") {
      return createEmptyDemoHistoryState();
    }
    return { payloads: parsed.payloads as Record<string, DemoTaskPayload> };
  } catch {
    return createEmptyDemoHistoryState();
  }
}

export function writeDemoHistoryState(storage: Storage, state: DemoHistoryState): void {
  storage.setItem(DEMO_HISTORY_STORAGE_KEY, JSON.stringify(state));
}

export function clearDemoHistoryState(storage: Storage): void {
  storage.removeItem(DEMO_HISTORY_STORAGE_KEY);
}
