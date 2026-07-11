# 第 7 天：失败任务样例、错误 Trace 和重试能力

## 今日目标

给项目补上异常处理闭环：

```text
错误数据 -> 节点失败 -> Trace 定位错误 -> 上传修复文件 -> 重试恢复
```

这一步用于展示稳定性、可观测性和恢复能力。

## 已完成内容

- 新增错误样例文件：

```text
sample-data/sales_orders_missing_total_amount.csv
```

- 该文件缺少 `total_amount` 字段，会触发 Data Analyst Agent 校验失败。
- Data Analyst 节点失败时会写入节点级 Trace：
  - `node=data_analysis`
  - `agent=Data Analyst Agent`
  - `status=failed`
  - `error_message` 包含缺失字段原因
  - `retry_count=1`
- 新增重试接口：

```text
POST /api/tasks/{task_id}/retry
```

- 只允许失败任务重试。
- 支持使用原文件重试。
- 支持上传修复后的 CSV/XLSX 替换原文件后重试。
- 重试不会删除旧 Trace，而是追加 `retry` 节点和新的执行 Trace。
- 前端失败任务详情中新增重试区域。

## 演示流程

### 1. 创建失败任务

上传错误文件：

```text
sample-data/sales_orders_missing_total_amount.csv
```

点击：

```text
创建任务并生成计划 -> 确认计划并继续执行
```

预期结果：

- 任务状态变成 `failed`。
- 历史任务中该任务显示失败。
- Agent Trace 出现 `data_analysis failed`。
- 错误信息包含 `total_amount` 字段缺失。

### 2. 修复后重试

选中失败任务，在重试区域上传正常文件：

```text
sample-data/sales_orders.csv
```

点击：

```text
重新执行失败任务
```

预期结果：

- 任务重新进入 `waiting_human_confirm`。
- Trace 追加 `retry` 节点。
- 再点击“确认计划并继续执行”后，任务完成。
- 报告和 PDF 下载按钮恢复可用。

## 接口说明

```text
POST /api/tasks/{task_id}/retry
```

请求：

- `multipart/form-data`
- `file` 可选

行为：

- 如果任务不是 `failed`，返回 `409`。
- 如果上传了新文件，会替换任务文件。
- 如果不上传文件，会使用原始文件重试。
- 重试后任务重新生成计划，并等待人工确认。

## 今日验证

```text
python -m pytest -q
12 passed
```

## 面试讲解要点

可以这样讲：

> 我专门做了一个缺字段的错误 CSV 来演示异常流程。Data Analyst Agent 在字段校验时失败，系统不会直接崩溃，而是把失败节点、错误原因和 retry_count 写入 Trace。用户可以上传修复后的文件重试，系统会保留旧 Trace 并追加新的重试链路，方便复盘整个恢复过程。

## 下一步建议

- 准备最终版 README。
- 写简历项目描述。
- 写面试讲解稿。
- 按截图清单补齐实际截图。
