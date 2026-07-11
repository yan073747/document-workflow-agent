from __future__ import annotations

import os
import shutil
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles

from app.core.models import ConfirmTaskResponse, CreateTaskResponse, TraceEvent
from app.db.repository import WorkflowRepository
from app.services.pdf_renderer import render_markdown_to_pdf
from app.services.workflow import OfficeWorkflow


DATABASE_PATH = os.getenv("DATABASE_PATH", "data/workflow.db")
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "data/uploads"))
FRONTEND_DIR = Path(__file__).resolve().parents[2] / "frontend"

repository = WorkflowRepository(DATABASE_PATH)
workflow = OfficeWorkflow(repository)

app = FastAPI(title="Multi Agent Office Workflow", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if FRONTEND_DIR.exists():
    app.mount("/app", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "multi-agent-office-workflow"}


@app.post("/api/tasks", response_model=CreateTaskResponse)
def create_task(objective: str = Form(...), file: UploadFile = File(...)) -> CreateTaskResponse:
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in {".csv", ".xlsx"}:
        raise HTTPException(status_code=400, detail="Only CSV and XLSX files are supported in the first version.")

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    task_id = str(uuid4())
    safe_name = f"{task_id}{suffix}"
    file_path = UPLOAD_DIR / safe_name
    with file_path.open("wb") as output:
        shutil.copyfileobj(file.file, output)

    task = repository.create_task(task_id, objective, str(file_path))
    task = workflow.run_planning(task.id)
    return CreateTaskResponse(task=task, trace=repository.get_trace(task.id))


@app.post("/api/tasks/{task_id}/confirm", response_model=ConfirmTaskResponse)
def confirm_task(task_id: str) -> ConfirmTaskResponse:
    try:
        task = workflow.continue_after_confirmation(task_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return ConfirmTaskResponse(task=task, trace=repository.get_trace(task.id))


@app.post("/api/tasks/{task_id}/retry", response_model=CreateTaskResponse)
def retry_task(task_id: str, file: UploadFile | None = File(default=None)) -> CreateTaskResponse:
    try:
        task = repository.get_task(task_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    if task.status != "failed":
        raise HTTPException(status_code=409, detail=f"Only failed tasks can be retried. Current status: {task.status}")

    replacement_path: str | None = None
    if file is not None and file.filename:
        suffix = Path(file.filename).suffix.lower()
        if suffix not in {".csv", ".xlsx"}:
            raise HTTPException(status_code=400, detail="Only CSV and XLSX files are supported in the first version.")
        UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        safe_name = f"{task_id}-retry-{uuid4().hex}{suffix}"
        file_path = UPLOAD_DIR / safe_name
        with file_path.open("wb") as output:
            shutil.copyfileobj(file.file, output)
        replacement_path = str(file_path)

    repository.add_trace(
        TraceEvent(
            task_id=task_id,
            node="retry",
            agent="Human Operator",
            status="started",
            input_summary="用户触发失败任务重试。",
            output_summary="已上传替换文件。" if replacement_path else "使用原始文件重新执行。",
        )
    )
    task = repository.reset_task_for_retry(task_id, replacement_path)
    task = workflow.run_planning(task.id)
    return CreateTaskResponse(task=task, trace=repository.get_trace(task.id))


@app.get("/api/tasks")
def list_tasks() -> dict[str, object]:
    return {"items": repository.list_task_summaries()}


@app.get("/api/workflow/graph")
def get_workflow_graph() -> dict[str, object]:
    return {
        "engine": "LangGraph StateGraph",
        "graphs": workflow.graph_node_names(),
        "human_confirm_node": "human_confirm",
        "llm_provider": workflow.provider_status(),
        "description": "Planning graph pauses at human confirmation. Execution graph runs after approval.",
    }


@app.get("/api/llm/status")
def get_llm_status() -> dict[str, object]:
    return workflow.provider_status()


@app.get("/api/tasks/{task_id}")
def get_task(task_id: str) -> dict[str, object]:
    try:
        task = repository.get_task(task_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"task": task, "trace": repository.get_trace(task_id)}


@app.get("/api/tasks/{task_id}/trace")
def get_trace(task_id: str) -> dict[str, object]:
    try:
        repository.get_task(task_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"items": repository.get_trace(task_id)}


def get_task_with_report(task_id: str):
    try:
        task = repository.get_task(task_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    if not task.report_markdown:
        raise HTTPException(status_code=404, detail="Report is not generated yet.")
    return task


@app.get("/api/tasks/{task_id}/report.md")
def get_report_markdown(task_id: str) -> Response:
    task = get_task_with_report(task_id)
    filename = f"sales-report-{task.id}.md"
    return Response(
        content=task.report_markdown,
        media_type="text/markdown; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@app.get("/api/tasks/{task_id}/report.pdf")
def get_report_pdf(task_id: str) -> Response:
    task = get_task_with_report(task_id)
    pdf_bytes = render_markdown_to_pdf(task.report_markdown)
    filename = f"sales-report-{task.id}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
