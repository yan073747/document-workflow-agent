# 第 2 天：接入 LangGraph 工作流

## 今日目标

把第 1 天的本地顺序工作流升级成 LangGraph `StateGraph`，让项目真正具备 Agent Workflow 的技术展示点。

## 已完成内容

- 安装并锁定 `langgraph==1.2.5`。
- 新增 `WorkflowState`，作为工作流在节点之间传递的状态。
- 将工作流拆成两个图：
  - 规划图：`planner -> human_confirm`
  - 执行图：`data_analysis -> report_writer -> reviewer`
- 保留人工确认节点，用户确认后才进入执行图。
- 增加 Reviewer 后的条件路由，为后续失败重试打基础。
- 新增 `/api/workflow/graph` 接口，方便前端展示当前图结构。
- 前端新增 LangGraph 工作流图展示区域。
- 增加 API 测试和图节点结构测试。

## 为什么拆成两个图

办公自动化任务里，计划本身可能会影响后续分析方向。例如用户只想看区域销售，但 Planner 可能生成了过多步骤。如果系统直接执行，用户没有机会纠偏。

所以这里拆成两段：

```text
创建任务 -> 规划图 -> 等待人工确认
确认计划 -> 执行图 -> 生成报告
```

这个设计可以在面试中体现：

- Human-in-the-loop，人机协同。
- Agent 执行不是黑盒，而是可确认、可追踪。
- Workflow 状态可以暂停和恢复。

## 当前 LangGraph 节点

### Planning Graph

| 节点 | 作用 |
| --- | --- |
| planner | 根据用户目标生成执行计划 |
| human_confirm | 将任务状态设为等待确认 |

### Execution Graph

| 节点 | 作用 |
| --- | --- |
| data_analysis | 调用销售数据分析工具 |
| report_writer | 生成 Markdown 经营报告 |
| reviewer | 审核报告必要章节 |

## 新增接口

```text
GET /api/workflow/graph
```

返回示例：

```json
{
  "engine": "LangGraph StateGraph",
  "graphs": {
    "planning": ["planner", "human_confirm"],
    "execution": ["data_analysis", "report_writer", "reviewer"]
  },
  "human_confirm_node": "human_confirm"
}
```

## 今日验证

```text
python -m pytest -q
5 passed
```

## 第 3 天建议

- 接入 LLM Provider 适配层。
- Planner 和 Writer 先支持本地规则 + LLM 两种模式。
- 保持无 Key 回退，避免演示时因为 API Key 或网络失败中断。
