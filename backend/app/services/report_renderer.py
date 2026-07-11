from __future__ import annotations

from app.core.models import SalesAnalysis


def render_markdown_report(objective: str, analysis: SalesAnalysis) -> str:
    region_rows = "\n".join(
        f"| {item.name} | {item.revenue:.2f} | {item.quantity} |" for item in analysis.top_regions
    )
    category_rows = "\n".join(
        f"| {item.name} | {item.revenue:.2f} | {item.quantity} |" for item in analysis.top_categories
    )
    customer_rows = "\n".join(
        f"| {name} | {ratio:.2f}% |" for name, ratio in analysis.customer_mix.items()
    )
    insight_rows = "\n".join(f"- {item}" for item in analysis.insights)

    return f"""# 销售经营分析报告

## 任务目标

{objective}

## 核心指标

| 指标 | 数值 |
| --- | ---: |
| 总销售额 | {analysis.total_revenue:.2f} 元 |
| 订单数 | {analysis.order_count} |
| 销售件数 | {analysis.total_quantity} |
| 平均客单价 | {analysis.average_order_value:.2f} 元 |

## 区域销售排行

| 区域 | 销售额 | 销售件数 |
| --- | ---: | ---: |
{region_rows}

## 品类销售排行

| 品类 | 销售额 | 销售件数 |
| --- | ---: | ---: |
{category_rows}

## 客户类型占比

| 客户类型 | 销售额占比 |
| --- | ---: |
{customer_rows}

## 关键洞察

{insight_rows}

## 经营建议

- 优先投入销售额最高的区域，复盘该区域的销售打法并复制到其他区域。
- 对热销品类增加库存和营销资源，避免旺季缺货影响转化。
- 对客单价较高的企业客户设计组合套餐，提高复购和批量采购机会。
- 每周固定生成同口径报告，跟踪区域、品类和客户类型的变化趋势。
"""


def build_report_prompt(objective: str, analysis: SalesAnalysis) -> str:
    return f"""请根据下面的销售分析结果，生成一份中文 Markdown 经营分析报告。

要求：
1. 必须包含这些二级标题：任务目标、核心指标、区域销售排行、品类销售排行、客户类型占比、关键洞察、经营建议。
2. 报告要适合给业务负责人阅读，结论明确，不要写空泛套话。
3. 保留关键数字，建议用 Markdown 表格展示核心指标。

任务目标：
{objective}

分析结果 JSON：
{analysis.model_dump_json()}
"""


def review_report(report_markdown: str) -> tuple[bool, list[str]]:
    required_phrases = ["核心指标", "区域销售排行", "品类销售排行", "经营建议"]
    missing = [phrase for phrase in required_phrases if phrase not in report_markdown]
    return len(missing) == 0, missing
