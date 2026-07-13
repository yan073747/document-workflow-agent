import { NextRequest, NextResponse } from "next/server";

type TaskStatus = "waiting_human_confirm" | "completed";

type PlanStep = {
  order: number;
  agent: string;
  action: string;
  expected_output: string;
};

type TaskRecord = {
  id: string;
  objective: string;
  file_path: string;
  status: TaskStatus;
  plan: PlanStep[];
  analysis: typeof analysisFixture | null;
  report_markdown: string;
  created_at: string;
  updated_at: string;
};

const demoUser = {
  id: "demo-user",
  email: "demo@example.com"
};

const plan: PlanStep[] = [
  {
    order: 1,
    agent: "Planner Agent",
    action: "识别上传文件结构，拆解经营分析目标。",
    expected_output: "可执行的多 Agent 工作计划"
  },
  {
    order: 2,
    agent: "Data Analyst",
    action: "按区域、品类、月份和销售员聚合订单数据。",
    expected_output: "销售指标、排名和异常信号"
  },
  {
    order: 3,
    agent: "Report Writer",
    action: "把分析结果组织成管理层可读的 Markdown 报告。",
    expected_output: "结构化经营分析报告"
  },
  {
    order: 4,
    agent: "Reviewer Agent",
    action: "检查结论是否有数据支撑，并补充行动建议。",
    expected_output: "带复核结论的最终报告"
  }
];

const analysisFixture = {
  total_revenue: 1286400,
  order_count: 486,
  total_quantity: 9320,
  average_order_value: 2646.91,
  top_regions: [
    { name: "华东", revenue: 412300, quantity: 2980 },
    { name: "华南", revenue: 326800, quantity: 2310 },
    { name: "华北", revenue: 244900, quantity: 1810 }
  ],
  top_categories: [
    { name: "办公设备", revenue: 382600, quantity: 870 },
    { name: "智能硬件", revenue: 314800, quantity: 1240 },
    { name: "耗材配件", revenue: 226500, quantity: 3920 }
  ],
  monthly_trend: [
    { name: "1月", revenue: 146000, quantity: 1040 },
    { name: "2月", revenue: 158600, quantity: 1180 },
    { name: "3月", revenue: 183200, quantity: 1320 },
    { name: "4月", revenue: 221700, quantity: 1560 },
    { name: "5月", revenue: 259100, quantity: 1830 },
    { name: "6月", revenue: 317800, quantity: 2390 }
  ],
  region_ranking: [
    { name: "华东", revenue: 412300, quantity: 2980 },
    { name: "华南", revenue: 326800, quantity: 2310 },
    { name: "华北", revenue: 244900, quantity: 1810 },
    { name: "西南", revenue: 184200, quantity: 1290 },
    { name: "西北", revenue: 118200, quantity: 930 }
  ],
  category_ranking: [
    { name: "办公设备", revenue: 382600, quantity: 870 },
    { name: "智能硬件", revenue: 314800, quantity: 1240 },
    { name: "耗材配件", revenue: 226500, quantity: 3920 },
    { name: "软件订阅", revenue: 196900, quantity: 410 },
    { name: "服务支持", revenue: 165600, quantity: 2880 }
  ],
  salesperson_ranking: [
    { name: "张敏", revenue: 286000, quantity: 1830 },
    { name: "王磊", revenue: 251500, quantity: 1520 },
    { name: "陈晨", revenue: 208800, quantity: 1210 },
    { name: "刘洋", revenue: 193400, quantity: 1110 },
    { name: "赵宁", revenue: 156700, quantity: 960 }
  ],
  customer_mix: {
    企业客户: 58.4,
    渠道客户: 24.2,
    政企客户: 12.6,
    其他: 4.8
  },
  insights: [
    "华东和华南贡献 57.4% 销售额，是下一阶段资源投入重点。",
    "办公设备客单价高，但销售件数偏低，适合做重点客户方案包。",
    "耗材配件销量高、金额中等，可以作为复购和交叉销售入口。"
  ]
};

const reportMarkdown = `# 销售订单经营分析报告

## 关键结论

- 半年销售额为 ¥1,286,400，订单数 486，平均客单价 ¥2,646.91。
- 华东、华南是核心区域，合计贡献超过一半销售额。
- 办公设备、智能硬件和耗材配件构成主要收入来源。

## 经营建议

1. 对华东、华南设置重点客户跟进节奏，围绕办公设备做方案型销售。
2. 用耗材配件设计复购包，提高低门槛产品的持续转化。
3. 对销售员张敏、王磊沉淀打法，并复制到低增长区域。

## Agent 复核

Reviewer Agent 已检查指标、趋势和建议之间的对应关系，报告结论均来自样例数据聚合结果。`;

function nowIso() {
  return new Date().toISOString();
}

function createTask(id: string, status: TaskStatus, objective = "分析销售订单数据并生成经营报告"): TaskRecord {
  const completed = status === "completed";
  return {
    id,
    objective,
    file_path: "vercel-demo/sales_orders.xlsx",
    status,
    plan,
    analysis: completed ? analysisFixture : null,
    report_markdown: completed ? reportMarkdown : "",
    created_at: nowIso(),
    updated_at: nowIso()
  };
}

function traceFor(taskId: string, status: TaskStatus) {
  const base = [
    trace(taskId, 1, "upload", "User", "completed", "接收销售订单文件。"),
    trace(taskId, 2, "planning", "Planner Agent", "completed", "生成 4 步多 Agent 执行计划。"),
    trace(taskId, 3, "human_confirm", "Human Operator", status === "completed" ? "completed" : "waiting", status === "completed" ? "用户确认执行计划。" : "等待用户确认执行计划。")
  ];
  if (status === "completed") {
    base.push(
      trace(taskId, 4, "analyze", "Data Analyst", "completed", "完成区域、品类、销售员和月度趋势分析。"),
      trace(taskId, 5, "write_report", "Report Writer", "completed", "生成 Markdown 经营报告。"),
      trace(taskId, 6, "review", "Reviewer Agent", "completed", "完成结论复核并输出最终报告。")
    );
  }
  return base;
}

function trace(taskId: string, id: number, node: string, agent: string, status: "completed" | "waiting", output: string) {
  return {
    id,
    task_id: taskId,
    node,
    agent,
    status,
    input_summary: "",
    output_summary: output,
    error_message: "",
    retry_count: 0,
    created_at: nowIso()
  };
}

function taskPayload(task: TaskRecord) {
  return {
    task,
    trace: traceFor(task.id, task.status)
  };
}

function checkAuth(request: NextRequest) {
  const authorization = request.headers.get("authorization") || "";
  return authorization.toLowerCase().startsWith("bearer ");
}

export async function GET(request: NextRequest, context: { params: { path: string[] } }) {
  const path = context.params.path.join("/");

  if (path === "auth/me") {
    if (!checkAuth(request)) return NextResponse.json({ detail: "Missing bearer token." }, { status: 401 });
    return NextResponse.json(demoUser);
  }

  if (path === "workflow/graph") {
    return NextResponse.json({
      engine: "Next.js Route Handlers demo",
      graphs: {
        planning: ["upload", "planning", "human_confirm"],
        execution: ["analyze", "write_report", "review", "complete"]
      },
      human_confirm_node: "human_confirm",
      llm_provider: { provider: "vercel-demo", model: "deterministic-fixture", enabled: true },
      description: "Vercel 版演示使用 serverless API 模拟完整 Agent 工作流。"
    });
  }

  if (path === "llm/status") {
    return NextResponse.json({ provider: "vercel-demo", model: "deterministic-fixture", enabled: true });
  }

  if (path === "tasks") {
    if (!checkAuth(request)) return NextResponse.json({ detail: "Missing bearer token." }, { status: 401 });
    return NextResponse.json({
      items: [
        {
          id: "demo-completed",
          objective: "分析销售订单数据并生成经营报告",
          status: "completed",
          has_report: true,
          plan_step_count: 4,
          trace_count: 6,
          created_at: nowIso(),
          updated_at: nowIso()
        }
      ]
    });
  }

  const reportMatch = path.match(/^tasks\/([^/]+)\/report\.(md|pdf)$/);
  if (reportMatch) {
    if (!checkAuth(request)) return NextResponse.json({ detail: "Missing bearer token." }, { status: 401 });
    const [, taskId, format] = reportMatch;
    if (format === "md") {
      return new NextResponse(reportMarkdown, {
        headers: {
          "content-type": "text/markdown; charset=utf-8",
          "content-disposition": `attachment; filename="sales-report-${taskId}.md"`
        }
      });
    }
    return new NextResponse(minimalPdf(reportMarkdown), {
      headers: {
        "content-type": "application/pdf",
        "content-disposition": `attachment; filename="sales-report-${taskId}.pdf"`
      }
    });
  }

  const taskMatch = path.match(/^tasks\/([^/]+)$/);
  if (taskMatch) {
    if (!checkAuth(request)) return NextResponse.json({ detail: "Missing bearer token." }, { status: 401 });
    return NextResponse.json(taskPayload(createTask(taskMatch[1], "completed")));
  }

  const traceMatch = path.match(/^tasks\/([^/]+)\/trace$/);
  if (traceMatch) {
    if (!checkAuth(request)) return NextResponse.json({ detail: "Missing bearer token." }, { status: 401 });
    return NextResponse.json({ items: traceFor(traceMatch[1], "completed") });
  }

  return NextResponse.json({ detail: "Not found" }, { status: 404 });
}

export async function POST(request: NextRequest, context: { params: { path: string[] } }) {
  const path = context.params.path.join("/");

  if (path === "auth/login") {
    const payload = await request.json().catch(() => null);
    if (!payload || payload.email !== "demo@example.com" || payload.password !== "demo123456") {
      return NextResponse.json({ detail: "Invalid email or password." }, { status: 401 });
    }
    return NextResponse.json({
      access_token: "vercel-demo-token",
      token_type: "bearer",
      user: demoUser
    });
  }

  if (path === "tasks") {
    if (!checkAuth(request)) return NextResponse.json({ detail: "Missing bearer token." }, { status: 401 });
    const form = await request.formData();
    const objective = String(form.get("objective") || "分析销售订单数据并生成经营报告");
    const task = createTask(`demo-${Date.now()}`, "waiting_human_confirm", objective);
    return NextResponse.json(taskPayload(task));
  }

  const confirmMatch = path.match(/^tasks\/([^/]+)\/confirm$/);
  if (confirmMatch) {
    if (!checkAuth(request)) return NextResponse.json({ detail: "Missing bearer token." }, { status: 401 });
    return NextResponse.json(taskPayload(createTask(confirmMatch[1], "completed")));
  }

  return NextResponse.json({ detail: "Not found" }, { status: 404 });
}

function minimalPdf(text: string) {
  const escaped = text
    .replace(/[^\x20-\x7E\n]/g, "")
    .replace(/\\/g, "\\\\")
    .replace(/\(/g, "\\(")
    .replace(/\)/g, "\\)")
    .split("\n")
    .slice(0, 24)
    .map((line, index) => `BT /F1 10 Tf 50 ${760 - index * 18} Td (${line || " "}) Tj ET`)
    .join("\n");
  const stream = `${escaped}\n`;
  const objects = [
    "1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj",
    "2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj",
    "3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >> endobj",
    "4 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj",
    `5 0 obj << /Length ${stream.length} >> stream\n${stream}endstream endobj`
  ];
  let offset = "%PDF-1.4\n".length;
  const xref = ["0000000000 65535 f "];
  for (const object of objects) {
    xref.push(`${String(offset).padStart(10, "0")} 00000 n `);
    offset += object.length + 1;
  }
  const body = `%PDF-1.4\n${objects.join("\n")}\n`;
  const startxref = body.length;
  return `${body}xref\n0 ${objects.length + 1}\n${xref.join("\n")}\ntrailer << /Size ${objects.length + 1} /Root 1 0 R >>\nstartxref\n${startxref}\n%%EOF`;
}
