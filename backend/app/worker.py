from __future__ import annotations

import os

from celery import Celery

from app.core.config import WorkerSettings
from app.db.repository import WorkflowRepository
from app.services.workflow import OfficeWorkflow


settings = WorkerSettings.from_env()
database_path = os.getenv("DATABASE_PATH", "data/workflow.db")

celery_app = Celery(
    "document_workflow_agent",
    broker=settings.redis_url,
    backend=settings.redis_url,
)


@celery_app.task(name="document_workflow_agent.execute_workflow")
def execute_workflow_task(task_id: str) -> str:
    repository = WorkflowRepository(database_path)
    workflow = OfficeWorkflow(repository)
    task = workflow.continue_after_confirmation(task_id)
    return task.status
