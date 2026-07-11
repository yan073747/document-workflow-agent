# 简历项目描述

## 项目名称

多 Agent 自动化办公工作流平台

## 一句话介绍

基于 FastAPI 和 LangGraph 开发的企业办公自动化 Agent Workflow 平台，支持销售数据上传、任务拆解、多 Agent 协作、人工确认、Trace 可观测、失败重试和 Markdown/PDF 报告导出。

## 简历精简版

**多 Agent 自动化办公工作流平台 | FastAPI + LangGraph + SQLite**

- 独立开发办公自动化 Agent Workflow 项目，支持销售 Excel/CSV 上传、任务拆解、人工确认、多 Agent 协作执行和报告生成。
- 使用 LangGraph 将流程拆分为 Planner、Data Analyst、Writer、Reviewer 等节点，前端可展示工作流图和 Agent Trace。
- 封装 LLM Provider 适配层，支持 DeepSeek / OpenAI 兼容接口，并实现无 Key 本地规则回退，保证演示稳定。
- 使用 SQLite 保存任务、执行计划、Trace 日志和报告结果，支持历史任务复盘、失败 Trace、失败任务重试和 Markdown/PDF 下载。

## 简历详细版

**多 Agent 自动化办公工作流平台 | Python / FastAPI / LangGraph / SQLite / LLM Provider**

- 面向企业办公自动化场景，设计并实现一个可执行销售数据分析任务的多 Agent 工作流平台，用户上传销售数据并输入目标后，系统自动拆解任务、执行分析、生成经营报告并支持文件下载。
- 使用 LangGraph `StateGraph` 构建工作流，将任务拆分为 `planner -> human_confirm` 规划图和 `data_analysis -> report_writer -> reviewer` 执行图，体现 Human-in-the-loop 和任务状态可恢复能力。
- 设计 Planner Agent、Data Analyst Agent、Writer Agent、Reviewer Agent 分工协作链路，Data Analyst 调用 CSV/XLSX 数据分析工具，Writer 生成 Markdown 报告，Reviewer 审核报告完整性。
- 封装 OpenAI 兼容 LLM Provider 适配层，支持 DeepSeek / OpenAI / 自定义兼容服务，同时提供本地规则回退，解决无 API Key、网络失败、模型输出格式异常导致的演示中断问题。
- 使用 SQLite 持久化任务状态、执行计划、分析结果、报告和 Trace 日志，前端支持任务历史、状态筛选、详情复盘、失败 Trace 查看、失败任务重试和 Markdown/PDF 报告下载。
- 为错误数据场景设计失败样例，缺失字段会触发 Data Analyst 节点失败并记录错误 Trace，用户可上传修复文件重新执行，形成成功闭环和异常恢复闭环。

## Boss 直聘 / 项目经历版

我做了一个“多 Agent 自动化办公工作流平台”，主要模拟企业数字员工处理办公任务的过程。用户上传销售 CSV/Excel 后，系统会先由 Planner Agent 拆解任务，进入人工确认节点；确认后由 Data Analyst Agent 调用数据分析工具，Writer Agent 生成经营报告，Reviewer Agent 审核报告质量。项目使用 FastAPI + LangGraph + SQLite 实现，前端可以展示 LangGraph 工作流图、Agent Trace、任务历史、失败重试和 Markdown/PDF 报告下载。为了保证演示稳定，我还做了 LLM Provider 适配层，支持 DeepSeek/OpenAI 兼容接口，没有 Key 时会自动回退到本地规则。

## 面试自我介绍版

这个项目我想展示的不是简单调用一次大模型，而是一个完整的 Agent Workflow 系统。它的业务场景是办公自动化，用户上传销售数据并输入“分析数据并生成经营报告”后，系统会创建任务，先由 Planner Agent 拆解计划，再经过人工确认，然后 Data Analyst、Writer、Reviewer 多个 Agent 协作完成分析、写报告和审核。

技术上我用 FastAPI 做后端 API，SQLite 保存任务和 Trace，LangGraph 负责任务编排。工作流被拆成两个图：一个是规划图，负责 Planner 和人工确认；另一个是执行图，负责数据分析、报告生成和审核。项目还封装了 LLM Provider 层，可以接 DeepSeek 或 OpenAI 兼容模型，同时保留本地规则回退，避免没有 Key 或网络异常时演示失败。

工程上我重点做了可观测性和稳定性：每个 Agent 节点都会记录 Trace，包括状态、输入摘要、输出摘要、错误信息和重试次数。系统支持历史任务复盘、失败任务重试，以及 Markdown/PDF 报告下载，所以它不是一个临时 Demo，而是一个有完整业务闭环的办公工作流平台。

## 技术关键词

```text
Python
FastAPI
LangGraph
StateGraph
Multi-Agent
Agent Workflow
Tool Calling
Human-in-the-loop
Trace Observability
LLM Provider
DeepSeek
OpenAI Compatible API
SQLite
Markdown/PDF Export
Failure Retry
```

## 面试可强调的亮点

1. **不是单轮 Prompt**  
   项目有任务创建、拆解、确认、执行、审核、导出和复盘完整链路。

2. **真实使用 LangGraph**  
   工作流拆成规划图和执行图，不是普通函数顺序调用。

3. **多 Agent 分工明确**  
   Planner 负责拆解，Data Analyst 负责工具调用，Writer 负责报告，Reviewer 负责质量审核。

4. **可观测性强**  
   每个节点都有 Trace，能看到状态、输入、输出、错误和重试次数。

5. **演示稳定**  
   LLM 调用失败或没有 API Key 时自动回退到本地规则。

6. **异常闭环完整**  
   错误数据会触发失败 Trace，用户可以上传修复文件重试。

7. **有办公成果物**  
   最终可以下载 Markdown 和 PDF 报告。
