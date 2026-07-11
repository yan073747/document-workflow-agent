from pathlib import Path

from app.services.sales_analyzer import analyze_sales_file


SAMPLE_DIR = Path(__file__).resolve().parents[2] / "sample-data"
CSV_SAMPLE = SAMPLE_DIR / "sales_orders.csv"
XLSX_SAMPLE = SAMPLE_DIR / "sales_orders.xlsx"


def test_sales_analyzer_builds_chart_ready_rankings() -> None:
    analysis = analyze_sales_file(CSV_SAMPLE)

    assert analysis.monthly_trend[0].name == "2026-06"
    assert analysis.monthly_trend[0].revenue == analysis.total_revenue
    assert analysis.monthly_trend[0].quantity == analysis.total_quantity

    assert analysis.salesperson_ranking[0].name == "王磊"
    assert analysis.salesperson_ranking[0].revenue == 9119
    assert analysis.region_ranking[0].name == "华东"
    assert analysis.category_ranking[0].name == "厨房电器"


def test_sales_analyzer_loads_real_xlsx_sample() -> None:
    analysis = analyze_sales_file(XLSX_SAMPLE)

    assert analysis.order_count == 15
    assert analysis.total_revenue == 41341
    assert analysis.salesperson_ranking
