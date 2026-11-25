"""FastAPI Router for AI Business Analyst Conversational Intelligence."""

from __future__ import annotations

from datetime import datetime, timezone
import time
from typing import Any, Dict, List
import uuid
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.agents.graph import run_analyst_workflow
from app.database.session import get_db
from app.logging_config import get_logger
from app.schemas.analyst import (
    AnalystChatRequest,
    AnalystChatResponse,
    ExecutionHistoryItem,
    ToolExecutionSummary,
)

logger = get_logger("insightiq.api.analyst")

analyst_router = APIRouter(prefix="/analyst", tags=["AI Business Analyst"])

DEFAULT_SUGGESTIONS = [
  "What is our total revenue?",
  "Show monthly revenue.",
  "Which products generate the most revenue?",
  "Who are our repeat customers?",
  "Why did revenue decline last month?",
  "Compare revenue by category.",
]

# In-memory execution audit log buffer (retaining most recent 50 entries)
EXECUTION_HISTORY_LOG: List[ExecutionHistoryItem] = []


@analyst_router.get(
    "/suggestions",
    response_model=List[str],
    summary="Get Suggested Business Analyst Inquiries",
    description="Returns starter questions covering key sales, product, and customer analytics domains.",
)
def get_suggested_questions() -> List[str]:
    """Returns curated starter business questions."""
    return DEFAULT_SUGGESTIONS


@analyst_router.post(
    "/chat",
    response_model=AnalystChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Ask AI Business Analyst Natural Language Question",
    description="Orchestrates LangGraph AI Analyst workflow, executes approved database tools, and returns evidence-backed responses.",
)
def chat_with_analyst(
    req: AnalystChatRequest,
    db: Session = Depends(get_db),
) -> AnalystChatResponse:
    """Processes conversational business query and returns grounded findings."""
    logger.info("Received analyst chat inquiry: '%s'", req.question)

    history = [m.model_dump() for m in req.chat_history]
    state = run_analyst_workflow(
        question=req.question,
        db=db,
        chat_history=history,
    )

    final_resp: Dict[str, Any] = state.get("final_response") or {}

    # Extract and sanitize tool executions (prevent leaking connection strings / sensitive params)
    raw_executions = state.get("tool_executions", [])
    sanitized_tools: List[ToolExecutionSummary] = []
    for te in raw_executions:
        args = te.get("arguments", {})
        clean_args = {k: v for k, v in args.items() if not str(k).lower().startswith("db")}
        sanitized_tools.append(
            ToolExecutionSummary(
                tool_name=te.get("tool_name", "unknown_tool"),
                arguments=clean_args,
                success=te.get("success", False),
                error=te.get("error"),
                execution_time_ms=te.get("execution_time_ms", 0.0),
            )
        )

    # Sanitize execution traces
    raw_traces = state.get("execution_trace", [])
    sanitized_traces: List[Dict[str, Any]] = []
    for tr in raw_traces:
        sanitized_traces.append({
            "node": tr.get("node"),
            "duration_ms": tr.get("duration_ms"),
            "timestamp": tr.get("timestamp"),
        })

    response = AnalystChatResponse(
        question=req.question,
        summary=final_resp.get("summary") or "Analytical inquiry completed.",
        insights=final_resp.get("insights") or [],
        metrics_referenced=final_resp.get("metrics_referenced") or [],
        chart_spec=final_resp.get("chart_spec"),
        tool_executions=sanitized_tools,
        execution_trace=sanitized_traces,
        suggested_follow_ups=final_resp.get("suggested_follow_ups") or [
            "What is our total revenue?",
            "Show monthly revenue.",
            "Which products generate the most revenue?",
        ],
        data_limitations_noted=final_resp.get("data_limitations_noted"),
        needs_clarification=state.get("is_clarification", False),
        clarification_question=state.get("clarification_question"),
        model_used=final_resp.get("model_used") or "InsightIQ LangGraph",
    )

    # Record to in-memory execution audit history
    total_duration = sum(te.execution_time_ms for te in sanitized_tools)
    history_record = ExecutionHistoryItem(
        id=str(uuid.uuid4())[:8],
        timestamp=datetime.now(timezone.utc).isoformat(),
        question=req.question,
        duration_ms=round(total_duration, 1),
        tools_count=len(sanitized_tools),
        tools_executed=[t.tool_name for t in sanitized_tools],
        has_chart=response.chart_spec is not None,
        success=not bool(state.get("error")),
    )
    EXECUTION_HISTORY_LOG.insert(0, history_record)
    if len(EXECUTION_HISTORY_LOG) > 50:
        EXECUTION_HISTORY_LOG.pop()

    return response


@analyst_router.get(
    "/history",
    response_model=List[ExecutionHistoryItem],
    summary="Get Analytics Execution Audit History",
    description="Returns recent analyst questions, tools invoked, and execution latencies.",
)
def get_execution_history() -> List[ExecutionHistoryItem]:
    """Returns chronologically ordered audit log of analyst executions."""
    return EXECUTION_HISTORY_LOG


@analyst_router.delete(
    "/history",
    status_code=status.HTTP_200_OK,
    summary="Clear Analytics Execution Audit History",
    description="Clears in-memory audit logs of analyst query executions.",
)
def clear_execution_history() -> Dict[str, str]:
    """Clears all audit logs."""
    EXECUTION_HISTORY_LOG.clear()
    return {"status": "cleared", "message": "Execution history cleared successfully."}
