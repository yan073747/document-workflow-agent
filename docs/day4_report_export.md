# 第 4 天：报告下载和 PDF 导出

## 今日目标

让系统不仅能在页面里展示报告，还能导出办公成果文件：

```text
Markdown 报告下载
PDF 报告下载
```

这一步让项目更像真实办公自动化系统，而不是只停留在 Demo 页面。

## 已完成内容

- 新增 `services/pdf_renderer.py`。
- 使用 ReportLab 将 Markdown 报告转换成 PDF。
- 支持中文标题、正文、列表和表格。
- `GET /api/tasks/{task_id}/report.md` 返回 Markdown 下载。
- `GET /api/tasks/{task_id}/report.pdf` 返回 PDF 下载。
- 前端报告区域新增“下载 MD”和“下载 PDF”按钮。
- 任务未完成前下载按钮禁用，报告生成后自动启用。
- 修复前端页面中的中文乱码。
- 测试覆盖 PDF 文件头、响应类型和下载响应头。

## 新增接口

```text
GET /api/tasks/{task_id}/report.md
```

返回：

```text
Content-Type: text/markdown; charset=utf-8
Content-Disposition: attachment; filename="sales-report-{task_id}.md"
```

```text
GET /api/tasks/{task_id}/report.pdf
```

返回：

```text
Content-Type: application/pdf
Content-Disposition: attachment; filename="sales-report-{task_id}.pdf"
```

## 实现说明

PDF 导出不是简单把页面截图保存，而是在后端把 Markdown 报告转换成 PDF：

- `#` 转一级标题。
- `##` 转二级标题。
- `-` 转列表项。
- Markdown 表格转 PDF 表格。
- 普通文本转段落。

这样导出的 PDF 更适合作为真实办公交付文件。

## 今日验证

```text
python -m pytest -q
10 passed
```

## 面试讲解要点

可以这样讲：

> 我把 Agent 生成的报告继续做成可下载成果物。系统不仅保存 Markdown，还提供 PDF 导出接口。PDF 在后端由 ReportLab 生成，支持中文、表格和列表。这样从用户上传文件到最终下载报告，形成了完整业务闭环。

## 第 5 天建议

- 做截图清单。
- 优化前端视觉和 Trace 展示。
- 增加任务历史列表详情入口。
- 准备 README 展示图和简历项目描述。
