from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


TaskStatus = Literal[
    "created",
    "planning",
    "queued",
    "waiting_human_confirm",
    "analyzing",
    "writing_report",
    "reviewing",
    "completed",
    "failed",
]

TraceStatus = Literal["started", "completed", "failed", "waiting"]


class PlanStep(BaseModel):
    order: int
    agent: str
    action: str
    expected_output: str


class TraceEvent(BaseModel):
    id: int | None = None
    task_id: str
    node: str
    agent: str
    status: TraceStatus
    input_summary: str = ""
    output_summary: str = ""
    error_message: str = ""
    retry_count: int = 0
    created_at: datetime | None = None


class SalesMetricItem(BaseModel):
    name: str
    revenue: float
    quantity: int


class SalesAnalysis(BaseModel):
    total_revenue: float
    order_count: int
    total_quantity: int
    average_order_value: float
    top_regions: list[SalesMetricItem]
    top_categories: list[SalesMetricItem]
    monthly_trend: list[SalesMetricItem] = Field(default_factory=list)
    region_ranking: list[SalesMetricItem] = Field(default_factory=list)
    category_ranking: list[SalesMetricItem] = Field(default_factory=list)
    salesperson_ranking: list[SalesMetricItem] = Field(default_factory=list)
    customer_mix: dict[str, float]
    insights: list[str]


class TaskRecord(BaseModel):
    id: str
    owner_id: str = ""
    objective: str
    file_path: str
    status: TaskStatus
    plan: list[PlanStep] = Field(default_factory=list)
    analysis: SalesAnalysis | None = None
    report_markdown: str = ""
    created_at: datetime
    updated_at: datetime


class TaskSummary(BaseModel):
    id: str
    owner_id: str = ""
    objective: str
    status: TaskStatus
    has_report: bool
    plan_step_count: int
    trace_count: int
    created_at: datetime
    updated_at: datetime


class CreateTaskResponse(BaseModel):
    task: TaskRecord
    trace: list[TraceEvent]


class ConfirmTaskResponse(BaseModel):
    task: TaskRecord
    trace: list[TraceEvent]


class ErrorResponse(BaseModel):
    detail: str
    context: dict[str, Any] = Field(default_factory=dict)


class UserRecord(BaseModel):
    id: str
    email: str
    password_hash: str
    created_at: datetime


class UserPublic(BaseModel):
    id: str
    email: str


class LoginRequest(BaseModel):
    email: str
    password: str


class RegisterRequest(BaseModel):
    email: str
    password: str


class AuthTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserPublic
