# 功能截图清单

这个目录用于保存项目展示截图。建议截图时统一使用浏览器宽度 1440px 左右，先清理无关浏览器书签栏和下载提示，保证画面聚焦在系统本身。

## 截图顺序

## 已生成截图

当前已生成：

```text
docs/screenshots/01-dashboard-overview.png
docs/screenshots/03-planner-human-confirm.png
docs/screenshots/04-langgraph-trace.png
docs/screenshots/05-report-preview-download.png
docs/screenshots/09-failed-task-trace.png
```

后续如果需要更完整的 GitHub 展示，可以继续补齐 `02`、`06`、`07`、`08`、`10`。

### 01-dashboard-overview.png

页面状态：

- 打开 `http://127.0.0.1:8020/app/`。
- 保留顶部控制台、任务指标卡、创建任务表单、执行计划区域。

展示重点：

- 这是一个 Agent Workflow 控制台，不是普通聊天页面。
- 可以看到 FastAPI、LangGraph、SQLite 技术标签。
- 顶部指标展示任务总数、完成数、等待确认数和可下载报告数。

### 02-create-task-form.png

页面状态：

- 聚焦“创建办公任务”区域。
- 任务目标填入：`分析销售数据，找出重点区域、热销品类和经营建议，生成一份经营报告。`
- 选择 `sample-data/sales_orders.csv`。

展示重点：

- 用户输入自然语言任务目标。
- 用户上传销售数据文件。
- 业务入口是办公任务，不是单轮 Prompt。

### 03-planner-human-confirm.png

页面状态：

- 点击“创建任务并生成计划”后停留在等待确认状态。
- 执行计划区域显示 Planner Agent 生成的步骤。
- “确认计划并继续执行”按钮可点击。

展示重点：

- Planner Agent 负责拆解任务。
- Human-in-the-loop 人工确认节点已经生效。
- 系统不会未经确认直接执行后续分析。

### 04-langgraph-trace.png

页面状态：

- 点击确认后任务执行完成。
- 截取 LangGraph 工作流图和 Agent Trace 区域。

展示重点：

- LangGraph 拆成规划图和执行图。
- Trace 记录每个 Agent 节点的 started/completed/waiting 状态。
- 可以看到 Planner、Data Analyst、Writer、Reviewer 的协作链路。

### 05-report-preview-download.png

页面状态：

- 任务执行完成。
- 报告区域显示 Markdown 报告。
- “下载 MD”和“下载 PDF”按钮处于可点击状态。

展示重点：

- 系统不是只生成页面文本，而是可以交付报告文件。
- Markdown/PDF 双格式体现办公交付闭环。

### 06-task-history-review.png

页面状态：

- 任务历史列表中至少有 2 条任务。
- 选中一个已完成任务。
- 页面右侧或下方恢复该任务的计划、Trace、报告。

展示重点：

- 历史任务可复盘。
- 每个任务都有状态、计划步数、Trace 数量和报告状态。
- 点击历史任务能恢复完整详情。

### 07-status-filter.png

页面状态：

- 在任务历史区切换筛选条件，例如“已完成”或“等待确认”。

展示重点：

- 平台支持按任务状态管理工作流。
- 这更接近企业 Agent Workflow 管理后台。

### 08-pdf-output.png

页面状态：

- 点击“下载 PDF”后打开导出的 PDF。
- 截取 PDF 首页，能看到中文标题、核心指标和表格。

展示重点：

- ReportLab 后端生成 PDF。
- 中文、表格、列表可以正常展示。
- 从数据上传到报告文件交付形成完整闭环。

### 09-failed-task-trace.png

页面状态：

- 上传 `sample-data/sales_orders_missing_total_amount.csv`。
- 创建任务、确认计划后让任务进入失败状态。
- 截取 Agent Trace 中 `data_analysis failed` 的错误信息。

展示重点：

- 错误不是静默失败。
- Trace 能显示失败节点和字段缺失原因。
- 历史任务中失败状态会标红。

### 10-retry-recovery.png

页面状态：

- 选中失败任务。
- 在重试区域上传 `sample-data/sales_orders.csv`。
- 点击“重新执行失败任务”后进入等待确认，再确认执行到完成。

展示重点：

- 失败任务可以上传修复后的文件恢复。
- 旧 Trace 保留，新 Trace 追加。
- 系统具备异常闭环，而不只是成功 Demo。

## README 推荐展示图

建议 README 中优先放这 4 张：

1. `01-dashboard-overview.png`
2. `03-planner-human-confirm.png`
3. `04-langgraph-trace.png`
4. `05-report-preview-download.png`

如果 GitHub 页面篇幅允许，再补：

5. `06-task-history-review.png`
6. `08-pdf-output.png`
7. `09-failed-task-trace.png`
8. `10-retry-recovery.png`

## 截图命名规范

```text
docs/screenshots/01-dashboard-overview.png
docs/screenshots/02-create-task-form.png
docs/screenshots/03-planner-human-confirm.png
docs/screenshots/04-langgraph-trace.png
docs/screenshots/05-report-preview-download.png
docs/screenshots/06-task-history-review.png
docs/screenshots/07-status-filter.png
docs/screenshots/08-pdf-output.png
docs/screenshots/09-failed-task-trace.png
docs/screenshots/10-retry-recovery.png
```

## 截图前检查

- 后端服务正常运行：`http://127.0.0.1:8020/health`
- 前端页面正常打开：`http://127.0.0.1:8020/app/`
- 至少执行过一个完整任务。
- 至少保留一个等待确认任务，方便截人工确认节点。
- 至少创建一个失败任务，方便截错误 Trace 和重试恢复。
- PDF 下载可以正常打开。
