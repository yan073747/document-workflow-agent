from pathlib import Path

from app.core.config import WorkerSettings
from app.db.repository import WorkflowRepository
from app.services.task_runner import TaskRunner
from app.services.workflow import OfficeWorkflow


SAMPLE_FILE = Path(__file__).resolve().parents[2] / "sample-data" / "sales_orders.csv"


def test_task_runner_uses_inline_fallback_when_celery_disabled(tmp_path: Path) -> None:
    repository = WorkflowRepository(tmp_path / "workflow.db")
    workflow = OfficeWorkflow(repository)
    runner = TaskRunner(repository, workflow, WorkerSettings(enable_celery=False))
    task = repository.create_task("task-inline", "分析销售数据并生成报告。", str(SAMPLE_FILE))
    planned = workflow.run_planning(task.id)

    completed = runner.dispatch_execution(planned.id)

    assert completed.status == "completed"
    assert completed.report_markdown
