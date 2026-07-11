from app.services.pdf_renderer import render_markdown_to_pdf


def test_render_markdown_to_pdf_returns_pdf_bytes() -> None:
    markdown = """# 销售经营分析报告

## 核心指标

| 指标 | 数值 |
| --- | ---: |
| 总销售额 | 1000 元 |

## 经营建议

- 继续跟进重点客户。
"""

    pdf_bytes = render_markdown_to_pdf(markdown)

    assert pdf_bytes.startswith(b"%PDF")
    assert len(pdf_bytes) > 1000
