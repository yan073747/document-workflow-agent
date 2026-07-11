from pathlib import Path

from app.core.config import LLMSettings
from app.db.repository import WorkflowRepository
from app.services.llm_provider import LLMResult
from app.services.sales_analyzer import analyze_sales_file
from app.services.workflow import OfficeWorkflow, parse_plan_json


SAMPLE_FILE = Path(__file__).resolve().parents[2] / "sample-data" / "sales_orders.csv"


class FakeLLMClient:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def status(self) -> dict[str, object]:
        return {
            "provider": "fake",
            "model": "fake-model",
            "base_url": "",
            "enabled": True,
            "fallback_reason": "test fake model",
        }

    def complete(self, *, system_prompt: str, user_prompt: str, temperature: float = 0.2) -> LLMResult:
        self.calls.append(system_prompt)
        if "Planner" in system_prompt:
            return LLMResult(
                provider="fake",
                model="fake-model",
                text='[{"agent":"Data Analyst Agent","action":"统计销售指标","expected_output":"销售指标摘要"}]',
            )
        return LLMResult(
            provider="fake",
            model="fake-model",
            text=(
                "# 销售经营分析报告\n\n"
                "## 核心指标\n\n"
                "## 区域销售排行\n\n"
                "## 品类销售排行\n\n"
                "## 经营建议\n\n"
                "- 保持重点区域投入。"
            ),
        )


def test_sales_analyzer_returns_core_metrics() -> None:
    analysis = analyze_sales_file(SAMPLE_FILE)

    assert analysis.order_count == 15
    assert analysis.total_revenue > 0
    assert analysis.top_regions
    assert analysis.top_categories
    assert sum(analysis.customer_mix.values()) > 99


def test_workflow_runs_from_plan_to_completed_with_local_fallback(tmp_path: Path) -> None:
    repository = WorkflowRepository(tmp_path / "workflow.db")
    workflow = OfficeWorkflow(repository)
    task = repository.create_task(
        "task-1",
        "分析销售数据，找出重点区域、热销品类和经营建议，生成一份经营报告。",
        str(SAMPLE_FILE),
    )

    planned = workflow.run_planning(task.id)
    assert planned.status == "waiting_human_confirm"
    assert len(planned.plan) == 3

    completed = workflow.continue_after_confirmation(task.id)
    trace = repository.get_trace(task.id)

    assert completed.status == "completed"
    assert completed.analysis is not None
    assert completed.report_markdown.startswith("# ")
    assert any("本地规则回退" in event.output_summary for event in trace)


def test_workflow_uses_llm_client_when_available(tmp_path: Path) -> None:
    repository = WorkflowRepository(tmp_path / "workflow.db")
    fake_llm = FakeLLMClient()
    workflow = OfficeWorkflow(repository, llm_client=fake_llm)
    task = repository.create_task("task-llm", "分析销售数据并生成报告。", str(SAMPLE_FILE))

    planned = workflow.run_planning(task.id)
    completed = workflow.continue_after_confirmation(task.id)
    trace = repository.get_trace(task.id)

    assert len(fake_llm.calls) == 2
    assert len(planned.plan) == 1
    assert completed.status == "completed"
    assert any("LLM fake/fake-model" in event.output_summary for event in trace)


def test_workflow_exposes_langgraph_node_names(tmp_path: Path) -> None:
    repository = WorkflowRepository(tmp_path / "workflow.db")
    workflow = OfficeWorkflow(repository)

    nodes = workflow.graph_node_names()

    assert nodes["planning"] == ["planner", "human_confirm"]
    assert nodes["execution"] == ["data_analysis", "report_writer", "reviewer"]


def test_parse_plan_json_accepts_code_fence() -> None:
    plan = parse_plan_json(
        """```json
        [{"agent":"Planner","action":"拆解任务","expected_output":"执行计划"}]
        ```"""
    )

    assert plan[0].order == 1
    assert plan[0].action == "拆解任务"


def test_llm_settings_no_key_status_uses_fallback() -> None:
    settings = LLMSettings(provider="deepseek", api_key="")

    assert settings.is_enabled is False
    assert "未配置" in str(settings.status()["fallback_reason"])
