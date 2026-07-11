from __future__ import annotations

import json
import re
from typing import Literal, TypedDict

from langgraph.graph import END, START, StateGraph

from app.core.models import PlanStep, SalesAnalysis, TaskRecord, TraceEvent
from app.db.repository import WorkflowRepository
from app.services.llm_provider import LLMClient, LLMUnavailableError
from app.services.report_renderer import build_report_prompt, render_markdown_report, review_report
from app.services.sales_analyzer import analyze_sales_file


class WorkflowState(TypedDict, total=False):
    task_id: str
    objective: str
    file_path: str
    plan: list[PlanStep]
    analysis: SalesAnalysis
    report_markdown: str
    review_passed: bool
    retry_count: int
    error_message: str


ReviewRoute = Literal["retry_report_writer", "finish"]


class OfficeWorkflow:
    """LangGraph-backed office workflow orchestration."""

    def __init__(
        self,
        repository: WorkflowRepository,
        llm_client: LLMClient | None = None,
        max_review_retries: int = 1,
    ) -> None:
        self.repository = repository
        self.llm_client = llm_client or LLMClient()
        self.max_review_retries = max_review_retries
        self.planning_graph = self._build_planning_graph()
        self.execution_graph = self._build_execution_graph()

    def run_planning(self, task_id: str) -> TaskRecord:
        task = self.repository.get_task(task_id)
        self.planning_graph.invoke(
            {
                "task_id": task.id,
                "objective": task.objective,
                "file_path": task.file_path,
            }
        )
        return self.repository.get_task(task_id)

    def continue_after_confirmation(self, task_id: str) -> TaskRecord:
        task = self.repository.get_task(task_id)
        if task.status != "waiting_human_confirm":
            raise ValueError(f"Task must be waiting_human_confirm, current status: {task.status}")

        try:
            self.execution_graph.invoke(
                {
                    "task_id": task.id,
                    "objective": task.objective,
                    "file_path": task.file_path,
                    "plan": task.plan,
                    "retry_count": 0,
                }
            )
        except Exception as exc:
            self.repository.add_trace(
                TraceEvent(
                    task_id=task_id,
                    node="workflow_error",
                    agent="System",
                    status="failed",
                    error_message=str(exc),
                    retry_count=1,
                )
            )
            return self.repository.update_task(task_id, status="failed")

        return self.repository.get_task(task_id)

    def graph_node_names(self) -> dict[str, list[str]]:
        return {
            "planning": ["planner", "human_confirm"],
            "execution": ["data_analysis", "report_writer", "reviewer"],
        }

    def provider_status(self) -> dict[str, object]:
        return self.llm_client.status()

    def _build_planning_graph(self):
        graph = StateGraph(WorkflowState)
        graph.add_node("planner", self._planner_node)
        graph.add_node("human_confirm", self._human_confirm_node)
        graph.add_edge(START, "planner")
        graph.add_edge("planner", "human_confirm")
        graph.add_edge("human_confirm", END)
        return graph.compile()

    def _build_execution_graph(self):
        graph = StateGraph(WorkflowState)
        graph.add_node("data_analysis", self._data_analysis_node)
        graph.add_node("report_writer", self._report_writer_node)
        graph.add_node("reviewer", self._reviewer_node)
        graph.add_edge(START, "data_analysis")
        graph.add_edge("data_analysis", "report_writer")
        graph.add_edge("report_writer", "reviewer")
        graph.add_conditional_edges(
            "reviewer",
            self._route_after_review,
            {
                "retry_report_writer": "report_writer",
                "finish": END,
            },
        )
        return graph.compile()

    def _planner_node(self, state: WorkflowState) -> WorkflowState:
        task_id = state["task_id"]
        task = self.repository.update_task(task_id, status="planning")
        self.repository.add_trace(
            TraceEvent(
                task_id=task_id,
                node="planner",
                agent="Planner Agent",
                status="started",
                input_summary=task.objective,
            )
        )

        plan, source = self._build_plan_with_provider(task.objective)
        self.repository.update_task(task_id, status="planning", plan=plan)
        self.repository.add_trace(
            TraceEvent(
                task_id=task_id,
                node="planner",
                agent="Planner Agent",
                status="completed",
                output_summary=f"已生成 {len(plan)} 个执行步骤。来源：{source}",
            )
        )
        return {"plan": plan}

    def _human_confirm_node(self, state: WorkflowState) -> WorkflowState:
        task_id = state["task_id"]
        self.repository.update_task(task_id, status="waiting_human_confirm", plan=state["plan"])
        self.repository.add_trace(
            TraceEvent(
                task_id=task_id,
                node="human_confirm",
                agent="Human Confirm Node",
                status="waiting",
                output_summary="执行计划已生成，等待用户确认后继续执行。",
            )
        )
        return state

    def _data_analysis_node(self, state: WorkflowState) -> WorkflowState:
        task_id = state["task_id"]
        task = self.repository.update_task(task_id, status="analyzing")
        self.repository.add_trace(
            TraceEvent(
                task_id=task_id,
                node="data_analysis",
                agent="Data Analyst Agent",
                status="started",
                input_summary=f"读取文件并统计销售指标：{task.file_path}",
            )
        )

        try:
            analysis = analyze_sales_file(task.file_path)
        except Exception as exc:
            self.repository.add_trace(
                TraceEvent(
                    task_id=task_id,
                    node="data_analysis",
                    agent="Data Analyst Agent",
                    status="failed",
                    error_message=str(exc),
                    retry_count=1,
                )
            )
            raise

        self.repository.update_task(task_id, status="analyzing", analysis=analysis)
        self.repository.add_trace(
            TraceEvent(
                task_id=task_id,
                node="data_analysis",
                agent="Data Analyst Agent",
                status="completed",
                output_summary=f"完成 {analysis.order_count} 笔订单分析，总销售额 {analysis.total_revenue:.2f} 元。",
            )
        )
        return {"analysis": analysis}

    def _report_writer_node(self, state: WorkflowState) -> WorkflowState:
        task_id = state["task_id"]
        task = self.repository.update_task(task_id, status="writing_report")
        analysis = state.get("analysis") or task.analysis
        if analysis is None:
            raise ValueError("Report writer requires sales analysis result.")

        retry_count = int(state.get("retry_count", 0))
        self.repository.add_trace(
            TraceEvent(
                task_id=task_id,
                node="report_writer",
                agent="Writer Agent",
                status="started",
                input_summary="根据销售统计结果生成 Markdown 经营报告。",
                retry_count=retry_count,
            )
        )
        report, source = self._render_report_with_provider(task.objective, analysis)
        self.repository.update_task(task_id, status="writing_report", report_markdown=report)
        self.repository.add_trace(
            TraceEvent(
                task_id=task_id,
                node="report_writer",
                agent="Writer Agent",
                status="completed",
                output_summary=f"Markdown 报告已生成。来源：{source}",
                retry_count=retry_count,
            )
        )
        return {"report_markdown": report, "retry_count": retry_count}

    def _reviewer_node(self, state: WorkflowState) -> WorkflowState:
        task_id = state["task_id"]
        task = self.repository.update_task(task_id, status="reviewing")
        report = state.get("report_markdown") or task.report_markdown
        retry_count = int(state.get("retry_count", 0))

        self.repository.add_trace(
            TraceEvent(
                task_id=task_id,
                node="reviewer",
                agent="Reviewer Agent",
                status="started",
                input_summary="检查报告是否包含核心指标、排行、洞察和经营建议。",
                retry_count=retry_count,
            )
        )
        passed, missing = review_report(report)
        if passed:
            self.repository.add_trace(
                TraceEvent(
                    task_id=task_id,
                    node="reviewer",
                    agent="Reviewer Agent",
                    status="completed",
                    output_summary="报告审核通过。",
                    retry_count=retry_count,
                )
            )
            self.repository.update_task(task_id, status="completed")
            return {"review_passed": True, "retry_count": retry_count}

        next_retry = retry_count + 1
        error_message = f"报告缺少必要章节：{', '.join(missing)}"
        self.repository.add_trace(
            TraceEvent(
                task_id=task_id,
                node="reviewer",
                agent="Reviewer Agent",
                status="failed",
                error_message=error_message,
                retry_count=next_retry,
            )
        )
        if next_retry > self.max_review_retries:
            self.repository.update_task(task_id, status="failed")
        return {
            "review_passed": False,
            "retry_count": next_retry,
            "error_message": error_message,
        }

    def _route_after_review(self, state: WorkflowState) -> ReviewRoute:
        if state.get("review_passed"):
            return "finish"
        if int(state.get("retry_count", 0)) <= self.max_review_retries:
            return "retry_report_writer"
        return "finish"

    def _build_plan_with_provider(self, objective: str) -> tuple[list[PlanStep], str]:
        try:
            result = self.llm_client.complete(
                system_prompt=(
                    "你是企业办公自动化工作流 Planner。"
                    "你必须只输出 JSON 数组，不要输出 Markdown。"
                ),
                user_prompt=build_planner_prompt(objective),
                temperature=0.1,
            )
            plan = parse_plan_json(result.text)
            return plan, f"LLM {result.provider}/{result.model}"
        except (LLMUnavailableError, ValueError, json.JSONDecodeError) as exc:
            return build_plan(objective), f"本地规则回退（{exc}）"

    def _render_report_with_provider(self, objective: str, analysis: SalesAnalysis) -> tuple[str, str]:
        try:
            result = self.llm_client.complete(
                system_prompt=(
                    "你是企业经营分析报告写作 Agent。"
                    "请输出中文 Markdown，不要编造输入数据之外的数字。"
                ),
                user_prompt=build_report_prompt(objective, analysis),
                temperature=0.3,
            )
            passed, missing = review_report(result.text)
            if not passed:
                raise ValueError(f"LLM report missing required sections: {', '.join(missing)}")
            return result.text, f"LLM {result.provider}/{result.model}"
        except (LLMUnavailableError, ValueError) as exc:
            return render_markdown_report(objective, analysis), f"本地规则回退（{exc}）"


def build_planner_prompt(objective: str) -> str:
    return f"""请把用户的办公任务拆成 3 到 5 个可执行步骤。

用户目标：
{objective}

输出格式必须是 JSON 数组，每一项包含：
- agent: 执行角色名称
- action: 要做什么
- expected_output: 该步骤应该产出什么

示例：
[
  {{
    "agent": "Data Analyst Agent",
    "action": "读取销售文件并统计核心指标。",
    "expected_output": "总销售额、订单数、区域排行和品类排行。"
  }}
]
"""


def parse_plan_json(text: str) -> list[PlanStep]:
    payload = extract_json_payload(text)
    data = json.loads(payload)
    if not isinstance(data, list) or not data:
        raise ValueError("Planner JSON must be a non-empty array.")

    plan: list[PlanStep] = []
    for index, item in enumerate(data, start=1):
        if not isinstance(item, dict):
            raise ValueError("Each planner item must be an object.")
        plan.append(
            PlanStep(
                order=index,
                agent=str(item.get("agent", "")).strip() or "Workflow Agent",
                action=str(item.get("action", "")).strip(),
                expected_output=str(item.get("expected_output", "")).strip(),
            )
        )

    if any(not step.action or not step.expected_output for step in plan):
        raise ValueError("Planner JSON items require action and expected_output.")
    return plan


def extract_json_payload(text: str) -> str:
    stripped = text.strip()
    fenced = re.search(r"```(?:json)?\s*(.*?)```", stripped, flags=re.DOTALL | re.IGNORECASE)
    if fenced:
        return fenced.group(1).strip()
    return stripped


def build_plan(objective: str) -> list[PlanStep]:
    return [
        PlanStep(
            order=1,
            agent="Data Analyst Agent",
            action="读取上传的销售文件，校验字段并统计销售指标。",
            expected_output="总销售额、订单数、区域排行、品类排行和客户类型占比。",
        ),
        PlanStep(
            order=2,
            agent="Writer Agent",
            action="根据分析结果生成结构化 Markdown 经营报告。",
            expected_output="包含核心指标、关键洞察和经营建议的报告。",
        ),
        PlanStep(
            order=3,
            agent="Reviewer Agent",
            action="检查报告是否覆盖用户目标和必要章节。",
            expected_output="审核通过或给出需要重试的原因。",
        ),
    ]
