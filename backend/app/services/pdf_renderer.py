from __future__ import annotations

from html import escape
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


FONT_NAME = "STSong-Light"


def render_markdown_to_pdf(markdown_text: str, title: str = "销售经营分析报告") -> bytes:
    pdfmetrics.registerFont(UnicodeCIDFont(FONT_NAME))
    buffer = BytesIO()
    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
        title=title,
    )
    story = build_story(markdown_text)
    document.build(story)
    return buffer.getvalue()


def build_story(markdown_text: str) -> list[object]:
    styles = build_styles()
    story: list[object] = []
    lines = markdown_text.splitlines()
    index = 0
    while index < len(lines):
        line = lines[index].strip()
        if not line:
            story.append(Spacer(1, 4))
            index += 1
            continue

        if line.startswith("|"):
            table_lines: list[str] = []
            while index < len(lines) and lines[index].strip().startswith("|"):
                table_lines.append(lines[index].strip())
                index += 1
            story.append(build_table(table_lines, styles["TableCell"]))
            story.append(Spacer(1, 8))
            continue

        if line.startswith("# "):
            story.append(Paragraph(escape(line[2:].strip()), styles["Heading1"]))
        elif line.startswith("## "):
            story.append(Paragraph(escape(line[3:].strip()), styles["Heading2"]))
        elif line.startswith("- "):
            story.append(Paragraph(f"• {escape(line[2:].strip())}", styles["Bullet"]))
        else:
            story.append(Paragraph(escape(line), styles["Body"]))
        index += 1

    return story


def build_styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "Heading1": ParagraphStyle(
            "ChineseHeading1",
            parent=base["Heading1"],
            fontName=FONT_NAME,
            fontSize=20,
            leading=28,
            spaceAfter=12,
        ),
        "Heading2": ParagraphStyle(
            "ChineseHeading2",
            parent=base["Heading2"],
            fontName=FONT_NAME,
            fontSize=14,
            leading=22,
            spaceBefore=8,
            spaceAfter=8,
        ),
        "Body": ParagraphStyle(
            "ChineseBody",
            parent=base["BodyText"],
            fontName=FONT_NAME,
            fontSize=10.5,
            leading=17,
            spaceAfter=6,
        ),
        "Bullet": ParagraphStyle(
            "ChineseBullet",
            parent=base["BodyText"],
            fontName=FONT_NAME,
            fontSize=10.5,
            leading=17,
            leftIndent=8,
            spaceAfter=5,
        ),
        "TableCell": ParagraphStyle(
            "ChineseTableCell",
            parent=base["BodyText"],
            fontName=FONT_NAME,
            fontSize=9.5,
            leading=14,
        ),
    }


def build_table(table_lines: list[str], cell_style: ParagraphStyle) -> Table:
    rows: list[list[Paragraph]] = []
    for line in table_lines:
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if cells and all(set(cell) <= {"-", ":"} for cell in cells):
            continue
        rows.append([Paragraph(escape(cell), cell_style) for cell in cells])

    table = Table(rows, hAlign="LEFT", repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (-1, -1), FONT_NAME),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EDF2F7")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#1A202C")),
                ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#CBD5E0")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    return table
