import assert from "node:assert/strict";
import fs from "node:fs";
import { createRequire } from "node:module";
import vm from "node:vm";
import ts from "typescript";

const require = createRequire(import.meta.url);
const source = fs.readFileSync(new URL("../src/lib/demoHistory.ts", import.meta.url), "utf8");
const compiled = ts.transpileModule(source, {
  compilerOptions: {
    module: ts.ModuleKind.CommonJS,
    target: ts.ScriptTarget.ES2020,
    esModuleInterop: true
  }
}).outputText;

const module = { exports: {} };
vm.runInNewContext(compiled, {
  exports: module.exports,
  module,
  require,
  console
});

const {
  createEmptyDemoHistoryState,
  getDemoHistorySummaries,
  getDemoTaskPayload,
  upsertDemoTaskPayload
} = module.exports;

function payload(id, status, createdAt) {
  return {
    task: {
      id,
      objective: `objective-${id}`,
      file_path: "sample-data/sales_orders.xlsx",
      status,
      plan: [
        { order: 1, agent: "Planner", action: "Plan", expected_output: "Steps" },
        { order: 2, agent: "Analyst", action: "Analyze", expected_output: "Metrics" }
      ],
      analysis: status === "completed" ? { total_revenue: 100 } : null,
      report_markdown: status === "completed" ? "# Report" : "",
      created_at: createdAt,
      updated_at: createdAt
    },
    trace: [
      { id: 1, task_id: id, node: "upload", agent: "User", status: "completed" },
      { id: 2, task_id: id, node: "planning", agent: "Planner", status: "completed" }
    ]
  };
}

let state = createEmptyDemoHistoryState();
state = upsertDemoTaskPayload(state, payload("demo-1", "waiting_human_confirm", "2026-07-14T10:00:00.000Z"));
state = upsertDemoTaskPayload(state, payload("demo-2", "completed", "2026-07-14T10:05:00.000Z"));

assert.equal(getDemoHistorySummaries(state).length, 2);
assert.equal(JSON.stringify(getDemoHistorySummaries(state).map((item) => item.id)), JSON.stringify(["demo-2", "demo-1"]));
assert.equal(getDemoHistorySummaries(state)[0].has_report, true);
assert.equal(getDemoHistorySummaries(state)[0].plan_step_count, 2);
assert.equal(getDemoHistorySummaries(state)[0].trace_count, 2);
assert.equal(getDemoTaskPayload(state, "demo-1").task.status, "waiting_human_confirm");

state = upsertDemoTaskPayload(state, payload("demo-1", "completed", "2026-07-14T10:10:00.000Z"));
assert.equal(getDemoHistorySummaries(state).length, 2);
assert.equal(getDemoTaskPayload(state, "demo-1").task.status, "completed");
assert.equal(getDemoHistorySummaries(state).find((item) => item.id === "demo-1").has_report, true);

console.log("demo history tests passed");
