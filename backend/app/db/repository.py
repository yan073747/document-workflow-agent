from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Iterable

from app.core.config import AuthSettings
from app.core.models import PlanStep, SalesAnalysis, TaskRecord, TaskStatus, TaskSummary, TraceEvent, UserRecord
from app.services.auth import hash_password, new_user_id, normalize_email


def utc_now_text() -> str:
    return datetime.now(UTC).replace(tzinfo=None).isoformat(timespec="seconds")


class WorkflowRepository:
    def __init__(self, database_path: str | Path = "data/workflow.db") -> None:
        self.database_path = Path(database_path)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self.init_db()

    def connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        return connection

    def init_db(self) -> None:
        with self.connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                  id TEXT PRIMARY KEY,
                  email TEXT NOT NULL UNIQUE,
                  password_hash TEXT NOT NULL,
                  created_at TEXT NOT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS tasks (
                  id TEXT PRIMARY KEY,
                  objective TEXT NOT NULL,
                  file_path TEXT NOT NULL,
                  status TEXT NOT NULL,
                  plan_json TEXT NOT NULL DEFAULT '[]',
                  analysis_json TEXT,
                  report_markdown TEXT NOT NULL DEFAULT '',
                  created_at TEXT NOT NULL,
                  updated_at TEXT NOT NULL
                )
                """
            )
            task_columns = {
                row["name"] for row in connection.execute("PRAGMA table_info(tasks)").fetchall()
            }
            if "owner_id" not in task_columns:
                connection.execute("ALTER TABLE tasks ADD COLUMN owner_id TEXT NOT NULL DEFAULT ''")
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS trace_events (
                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                  task_id TEXT NOT NULL,
                  node TEXT NOT NULL,
                  agent TEXT NOT NULL,
                  status TEXT NOT NULL,
                  input_summary TEXT NOT NULL DEFAULT '',
                  output_summary TEXT NOT NULL DEFAULT '',
                  error_message TEXT NOT NULL DEFAULT '',
                  retry_count INTEGER NOT NULL DEFAULT 0,
                  created_at TEXT NOT NULL,
                  FOREIGN KEY(task_id) REFERENCES tasks(id)
                )
                """
            )
        demo_user = self.ensure_demo_user()
        with self.connect() as connection:
            connection.execute(
                "UPDATE tasks SET owner_id = ? WHERE owner_id = ''",
                (demo_user.id,),
            )

    def ensure_demo_user(self) -> UserRecord:
        settings = AuthSettings.from_env()
        existing = self.get_user_by_email(settings.demo_email)
        if existing:
            return existing
        return self.create_user(settings.demo_email, settings.demo_password)

    def create_user(self, email: str, password: str) -> UserRecord:
        now = utc_now_text()
        user_id = new_user_id()
        normalized_email = normalize_email(email)
        with self.connect() as connection:
            connection.execute(
                """
                INSERT INTO users (id, email, password_hash, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (user_id, normalized_email, hash_password(password), now),
            )
        return self.get_user(user_id)

    def get_user(self, user_id: str) -> UserRecord:
        with self.connect() as connection:
            row = connection.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        if row is None:
            raise KeyError(f"User not found: {user_id}")
        return self._row_to_user(row)

    def get_user_by_email(self, email: str) -> UserRecord | None:
        with self.connect() as connection:
            row = connection.execute(
                "SELECT * FROM users WHERE email = ?",
                (normalize_email(email),),
            ).fetchone()
        return self._row_to_user(row) if row else None

    def create_task(self, task_id: str, objective: str, file_path: str, owner_id: str | None = None) -> TaskRecord:
        now = utc_now_text()
        task_owner_id = owner_id or self.ensure_demo_user().id
        with self.connect() as connection:
            connection.execute(
                """
                INSERT INTO tasks (
                  id, owner_id, objective, file_path, status, plan_json, report_markdown, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (task_id, task_owner_id, objective, file_path, "created", "[]", "", now, now),
            )
        return self.get_task(task_id)

    def update_task(
        self,
        task_id: str,
        *,
        status: TaskStatus | None = None,
        plan: Iterable[PlanStep] | None = None,
        analysis: SalesAnalysis | None = None,
        report_markdown: str | None = None,
    ) -> TaskRecord:
        task = self.get_task(task_id)
        next_status = status or task.status
        next_plan = list(plan) if plan is not None else task.plan
        next_analysis = analysis if analysis is not None else task.analysis
        next_report = report_markdown if report_markdown is not None else task.report_markdown
        now = utc_now_text()

        with self.connect() as connection:
            connection.execute(
                """
                UPDATE tasks
                SET status = ?, plan_json = ?, analysis_json = ?, report_markdown = ?, updated_at = ?
                WHERE id = ?
                """,
                (
                    next_status,
                    json.dumps([step.model_dump() for step in next_plan], ensure_ascii=False),
                    next_analysis.model_dump_json() if next_analysis else None,
                    next_report,
                    now,
                    task_id,
                ),
            )
        return self.get_task(task_id)

    def reset_task_for_retry(self, task_id: str, file_path: str | None = None) -> TaskRecord:
        task = self.get_task(task_id)
        now = utc_now_text()
        next_file_path = file_path or task.file_path
        with self.connect() as connection:
            connection.execute(
                """
                UPDATE tasks
                SET status = ?, file_path = ?, plan_json = ?, analysis_json = ?, report_markdown = ?, updated_at = ?
                WHERE id = ?
                """,
                ("created", next_file_path, "[]", None, "", now, task_id),
            )
        return self.get_task(task_id)

    def get_task(self, task_id: str) -> TaskRecord:
        with self.connect() as connection:
            row = connection.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
        if row is None:
            raise KeyError(f"Task not found: {task_id}")
        return self._row_to_task(row)

    def list_tasks(self) -> list[TaskRecord]:
        with self.connect() as connection:
            rows = connection.execute("SELECT * FROM tasks ORDER BY created_at DESC").fetchall()
        return [self._row_to_task(row) for row in rows]

    def list_task_summaries(self) -> list[TaskSummary]:
        with self.connect() as connection:
            rows = connection.execute(
                """
                SELECT
                  tasks.*,
                  COUNT(trace_events.id) AS trace_count
                FROM tasks
                LEFT JOIN trace_events ON trace_events.task_id = tasks.id
                GROUP BY tasks.id
                ORDER BY tasks.created_at DESC
                """
            ).fetchall()
        return [self._row_to_summary(row) for row in rows]

    def list_task_summaries_for_user(self, owner_id: str) -> list[TaskSummary]:
        with self.connect() as connection:
            rows = connection.execute(
                """
                SELECT
                  tasks.*,
                  COUNT(trace_events.id) AS trace_count
                FROM tasks
                LEFT JOIN trace_events ON trace_events.task_id = tasks.id
                WHERE tasks.owner_id = ?
                GROUP BY tasks.id
                ORDER BY tasks.created_at DESC
                """,
                (owner_id,),
            ).fetchall()
        return [self._row_to_summary(row) for row in rows]

    def add_trace(self, event: TraceEvent) -> TraceEvent:
        created_at = event.created_at.isoformat(timespec="seconds") if event.created_at else utc_now_text()
        with self.connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO trace_events (
                  task_id, node, agent, status, input_summary, output_summary,
                  error_message, retry_count, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event.task_id,
                    event.node,
                    event.agent,
                    event.status,
                    event.input_summary,
                    event.output_summary,
                    event.error_message,
                    event.retry_count,
                    created_at,
                ),
            )
            event_id = int(cursor.lastrowid)
        return event.model_copy(update={"id": event_id, "created_at": datetime.fromisoformat(created_at)})

    def get_trace(self, task_id: str) -> list[TraceEvent]:
        with self.connect() as connection:
            rows = connection.execute(
                "SELECT * FROM trace_events WHERE task_id = ? ORDER BY id ASC",
                (task_id,),
            ).fetchall()
        return [self._row_to_trace(row) for row in rows]

    def _row_to_task(self, row: sqlite3.Row) -> TaskRecord:
        plan_data = json.loads(row["plan_json"] or "[]")
        analysis_data = json.loads(row["analysis_json"]) if row["analysis_json"] else None
        return TaskRecord(
            id=row["id"],
            owner_id=row["owner_id"],
            objective=row["objective"],
            file_path=row["file_path"],
            status=row["status"],
            plan=[PlanStep(**item) for item in plan_data],
            analysis=SalesAnalysis(**analysis_data) if analysis_data else None,
            report_markdown=row["report_markdown"] or "",
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )

    def _row_to_summary(self, row: sqlite3.Row) -> TaskSummary:
        plan_data = json.loads(row["plan_json"] or "[]")
        return TaskSummary(
            id=row["id"],
            owner_id=row["owner_id"],
            objective=row["objective"],
            status=row["status"],
            has_report=bool(row["report_markdown"]),
            plan_step_count=len(plan_data),
            trace_count=int(row["trace_count"]),
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )

    def _row_to_trace(self, row: sqlite3.Row) -> TraceEvent:
        return TraceEvent(
            id=row["id"],
            task_id=row["task_id"],
            node=row["node"],
            agent=row["agent"],
            status=row["status"],
            input_summary=row["input_summary"],
            output_summary=row["output_summary"],
            error_message=row["error_message"],
            retry_count=row["retry_count"],
            created_at=datetime.fromisoformat(row["created_at"]),
        )

    def _row_to_user(self, row: sqlite3.Row) -> UserRecord:
        return UserRecord(
            id=row["id"],
            email=row["email"],
            password_hash=row["password_hash"],
            created_at=datetime.fromisoformat(row["created_at"]),
        )
