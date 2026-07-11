# 第 1 天设计说明

## 今日目标

先把项目从占位目录变成可继续开发的工程骨架，明确第一版 MVP 的业务闭环。

第一版只做一个场景：

```text
上传销售 Excel -> 多 Agent 协作分析 -> 生成经营报告
```

暂时不做多行业、多文件类型和复杂权限系统，避免项目一开始失控。

## MVP 范围

### 用户输入

- 一个销售 CSV 或 Excel 文件。
- 一段自然语言任务目标。

示例：

```text
分析销售数据，找出重点区域、热销品类和经营建议，生成一份经营报告。
```

### 系统输出

- 任务状态。
- Agent 执行链路。
- 工具调用结果。
- Markdown 经营报告。

## Agent 角色

| Agent | 职责 |
| --- | --- |
| Planner Agent | 理解用户目标，拆解执行计划 |
| Data Analyst Agent | 调用数据分析工具，统计销售指标 |
| Writer Agent | 根据分析结果生成 Markdown 报告 |
| Reviewer Agent | 检查报告是否包含关键结论和建议 |

## 任务状态

| 状态 | 含义 |
| --- | --- |
| created | 任务已创建 |
| planning | 正在拆解任务 |
| waiting_human_confirm | 等待用户确认计划 |
| analyzing | 正在分析数据 |
| writing_report | 正在生成报告 |
| reviewing | 正在审核报告 |
| completed | 已完成 |
| failed | 执行失败 |

## 数据字段

销售数据第一版字段：

```text
order_id
date
region
salesperson
product
category
quantity
unit_price
total_amount
customer_type
```

这些字段足够支撑：

- 总销售额
- 订单数量
- 区域销售排行
- 品类销售排行
- 客户类型占比
- 销售建议

## 第一版技术策略

第一版先做稳定闭环：

- 用 FastAPI 提供接口。
- 用 SQLite 保存任务和执行步骤。
- 用 pandas 分析销售数据。
- 用本地规则生成计划和报告。
- 预留 LangGraph 和 LLM 接入点。

这样做的好处是：即使没有 API Key，也能完整演示 Agent 工作流。

## 后续演进

第 2 天重点：

- 完成任务 API。
- 完成 SQLite 表结构。
- 完成销售数据分析工具。
- 跑通创建任务、确认计划、执行工作流、查看报告。

第 3 天重点：

- 接入 LangGraph。
- 将当前本地工作流迁移为 `StateGraph` 节点。
- 增加失败重试和节点级 Trace。
