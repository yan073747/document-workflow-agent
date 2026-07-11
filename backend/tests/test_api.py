from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app


SAMPLE_FILE = Path(__file__).resolve().parents[2] / "sample-data" / "sales_orders.csv"
BAD_SAMPLE_FILE = Path(__file__).resolve().parents[2] / "sample-data" / "sales_orders_missing_total_amount.csv"


def test_create_confirm_and_read_report() -> None:
    client = TestClient(app)

    with SAMPLE_FILE.open("rb") as file:
        create_response = client.post(
            "/api/tasks",
            data={"objective": "分析销售数据并生成经营报告。"},
            files={"file": ("sales_orders.csv", file, "text/csv")},
        )

    assert create_response.status_code == 200
    task_id = create_response.json()["task"]["id"]
    assert create_response.json()["task"]["status"] == "waiting_human_confirm"

    confirm_response = client.post(f"/api/tasks/{task_id}/confirm")
    assert confirm_response.status_code == 200
    assert confirm_response.json()["task"]["status"] == "completed"

    report_response = client.get(f"/api/tasks/{task_id}/report.md")
    assert report_response.status_code == 200
    assert report_response.text.startswith("# ")
    assert report_response.headers["content-type"].startswith("text/markdown")
    assert "sales-report" in report_response.headers["content-disposition"]

    pdf_response = client.get(f"/api/tasks/{task_id}/report.pdf")
    assert pdf_response.status_code == 200
    assert pdf_response.headers["content-type"] == "application/pdf"
    assert "sales-report" in pdf_response.headers["content-disposition"]
    assert pdf_response.content.startswith(b"%PDF")
    assert len(pdf_response.content) > 1000

    list_response = client.get("/api/tasks")
    assert list_response.status_code == 200
    items = list_response.json()["items"]
    summary = next(item for item in items if item["id"] == task_id)
    assert summary["status"] == "completed"
    assert summary["has_report"] is True
    assert summary["plan_step_count"] >= 1
    assert summary["trace_count"] >= 1

    detail_response = client.get(f"/api/tasks/{task_id}")
    assert detail_response.status_code == 200
    detail = detail_response.json()
    assert detail["task"]["id"] == task_id
    assert detail["trace"]


def test_workflow_graph_endpoint() -> None:
    client = TestClient(app)

    response = client.get("/api/workflow/graph")

    assert response.status_code == 200
    payload = response.json()
    assert payload["engine"] == "LangGraph StateGraph"
    assert payload["graphs"]["planning"] == ["planner", "human_confirm"]
    assert payload["graphs"]["execution"] == ["data_analysis", "report_writer", "reviewer"]
    assert "llm_provider" in payload


def test_llm_status_endpoint() -> None:
    client = TestClient(app)

    response = client.get("/api/llm/status")

    assert response.status_code == 200
    payload = response.json()
    assert payload["provider"]
    assert "enabled" in payload


def test_failed_task_can_retry_with_replacement_file() -> None:
    client = TestClient(app)

    with BAD_SAMPLE_FILE.open("rb") as file:
        create_response = client.post(
            "/api/tasks",
            data={"objective": "分析销售数据并生成经营报告。"},
            files={"file": ("bad_sales.csv", file, "text/csv")},
        )

    assert create_response.status_code == 200
    task_id = create_response.json()["task"]["id"]

    failed_response = client.post(f"/api/tasks/{task_id}/confirm")
    assert failed_response.status_code == 200
    assert failed_response.json()["task"]["status"] == "failed"
    failed_trace = failed_response.json()["trace"]
    assert any(event["node"] == "data_analysis" and event["status"] == "failed" for event in failed_trace)
    assert any("total_amount" in event["error_message"] for event in failed_trace)

    with SAMPLE_FILE.open("rb") as file:
        retry_response = client.post(
            f"/api/tasks/{task_id}/retry",
            files={"file": ("sales_orders.csv", file, "text/csv")},
        )

    assert retry_response.status_code == 200
    assert retry_response.json()["task"]["status"] == "waiting_human_confirm"
    assert any(event["node"] == "retry" for event in retry_response.json()["trace"])

    completed_response = client.post(f"/api/tasks/{task_id}/confirm")
    assert completed_response.status_code == 200
    assert completed_response.json()["task"]["status"] == "completed"


def test_retry_only_accepts_failed_tasks() -> None:
    client = TestClient(app)

    with SAMPLE_FILE.open("rb") as file:
        create_response = client.post(
            "/api/tasks",
            data={"objective": "分析销售数据并生成经营报告。"},
            files={"file": ("sales_orders.csv", file, "text/csv")},
        )

    task_id = create_response.json()["task"]["id"]
    retry_response = client.post(f"/api/tasks/{task_id}/retry")

    assert retry_response.status_code == 409
