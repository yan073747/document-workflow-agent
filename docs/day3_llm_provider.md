# 第 3 天：接入 LLM Provider 适配层

## 今日目标

让 Planner Agent 和 Writer Agent 支持两种执行模式：

```text
远程 LLM 模式：DeepSeek / OpenAI 兼容接口
本地规则模式：无 Key、调用失败或格式错误时自动回退
```

这样项目既能体现真实大模型接入能力，也能保证面试演示稳定。

## 已完成内容

- 新增 `core/config.py`，集中读取 LLM 环境变量。
- 新增 `services/llm_provider.py`，封装 OpenAI 兼容 `/chat/completions` 调用。
- Planner Agent 支持优先调用 LLM 输出 JSON 执行计划。
- Writer Agent 支持优先调用 LLM 输出 Markdown 经营报告。
- Planner JSON 解析失败时自动回退本地规则计划。
- Writer 报告缺少必要章节时自动回退本地 Markdown 模板。
- 新增 `/api/llm/status` 接口。
- `/api/workflow/graph` 增加当前 LLM Provider 状态。
- 前端顶部增加当前模型状态展示。
- 测试覆盖无 Key 回退、Fake LLM 调用、Provider 状态接口和完整任务流程。

## 环境变量

默认本地模式：

```env
LLM_PROVIDER=local
LLM_API_KEY=
LLM_BASE_URL=
LLM_MODEL=
LLM_TIMEOUT_SECONDS=30
```

DeepSeek：

```env
LLM_PROVIDER=deepseek
LLM_API_KEY=你的 Key
LLM_BASE_URL=https://api.deepseek.com
LLM_MODEL=deepseek-chat
```

OpenAI：

```env
LLM_PROVIDER=openai
LLM_API_KEY=你的 Key
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL=gpt-4o-mini
```

其他 OpenAI 兼容接口：

```env
LLM_PROVIDER=openai-compatible
LLM_API_KEY=你的 Key
LLM_BASE_URL=https://你的服务地址/v1
LLM_MODEL=模型名称
```

## Planner 双模式

Planner 会先尝试让 LLM 输出 JSON 数组：

```json
[
  {
    "agent": "Data Analyst Agent",
    "action": "读取销售文件并统计核心指标。",
    "expected_output": "总销售额、订单数、区域排行和品类排行。"
  }
]
```

如果出现这些情况，会回退到本地固定三步计划：

- 未配置 API Key。
- 网络请求失败。
- 模型输出不是 JSON。
- JSON 缺少 `action` 或 `expected_output`。

## Writer 双模式

Writer 会先尝试让 LLM 根据销售统计结果生成 Markdown 报告。

报告必须包含：

- 核心指标
- 区域销售排行
- 品类销售排行
- 经营建议

如果模型输出缺少必要章节，Reviewer 会认为不合格，Writer 会回退到本地模板。

## 今日验证

```text
python -m pytest -q
9 passed
```

## 面试讲解要点

可以这样讲：

> 我没有把模型调用散落在各个 Agent 里，而是抽了一层 LLM Provider Adapter。这样 Planner 和 Writer 都可以复用同一套 OpenAI 兼容调用逻辑。为了保证演示稳定，我做了本地规则回退：没配 Key、网络失败、模型返回格式不对，都不会让任务中断，而是继续用本地规则完成工作流，并且在 Trace 里记录来源。

## 第 4 天建议

- 增加 PDF 导出。
- 增加报告下载接口。
- 在前端增加报告复制和下载按钮。
- 准备功能截图清单。
