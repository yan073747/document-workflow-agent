from __future__ import annotations

from app.core.config import WorkerSettings
from app.core.models import TaskRecord, TraceEvent
from app.db.repository import WorkflowRepository
from app.services.workflow import OfficeWorkflow


class TaskRunner:
    def __init__(
        self,
        repository: WorkflowRepository,
        workflow: OfficeWorkflow,
        settings: WorkerSettings | None = None,
    ) -> None:
        self.repository = repository
        self.workflow = workflow
        self.settings = settings or WorkerSettings.from_env()

    def dispatch_execution(self, task_id: str) -> TaskRecord:
        if not self.settings.enable_celery:
            return self.workflow.continue_after_confirmation(task_id)

        task = self.repository.update_task(task_id, status="queued")
        self.repository.add_trace(
            TraceEvent(
                task_id=task_id,
                node="queue",
                agent="Task Runner",
                status="started",
                input_summary="用户确认计划后进入异步执行队列。",
                output_summary="已提交到 Celery worker。",
            )
        )
        from app.worker import execute_workflow_task

        execute_workflow_task.delay(task_id)
        return task
