"""Pydantic Schemas for AI Business Analyst Chat API."""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field, field_validator

from app.llm.schemas import AnalystInsight, EvidenceGrounding


class ChatHistoryMessage(BaseModel):
    """Historical message in an analyst conversational session."""
    role: Literal["user", "assistant"] = Field(..., description="Message author role")
    content: str = Field(..., description="Text content of the message")


class AnalystChatRequest(BaseModel):
    """User inquiry payload sent to the autonomous AI Business Analyst."""
    question: str = Field(..., min_length=1, max_length=1000, description="Natural language business inquiry")
    chat_history: List[ChatHistoryMessage] = Field(
        default_factory=list, description="Prior conversation context for continuity"
    )

    @field_validator("question")
    @classmethod
    def validate_question(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Question cannot be empty or whitespace only.")
        return v.strip()


class ToolExecutionSummary(BaseModel):
    """Sanitized record of an analytics tool invocation without sensitive database credentials."""
    tool_name: str = Field(..., description="Name of the analytics tool executed")
    arguments: Dict[str, Any] = Field(default_factory=dict, description="Validated input parameters")
    success: bool = Field(..., description="Whether tool execution completed cleanly")
    error: Optional[str] = Field(None, description="Safe error message if tool failed")
    execution_time_ms: float = Field(..., description="Duration of tool execution in milliseconds")


class AnalystChatResponse(BaseModel):
    """Complete structured response from the AI Business Analyst."""
    question: str = Field(..., description="Original user prompt")
    summary: str = Field(..., description="Grounded executive summary derived strictly from data evidence")
    insights: List[AnalystInsight] = Field(
        default_factory=list, description="Structured business findings, observations, and recommendations"
    )
    metrics_referenced: List[EvidenceGrounding] = Field(
        default_factory=list, description="Audited database metric values backing the answer"
    )
    chart_spec: Optional[Dict[str, Any]] = Field(
        None, description="Validated Recharts-compatible chart specification if requested or relevant"
    )
    tool_executions: List[ToolExecutionSummary] = Field(
        default_factory=list, description="Sanitized list of tools executed to formulate response"
    )
    execution_trace: List[Dict[str, Any]] = Field(
        default_factory=list, description="Audit trace of LangGraph agent workflow steps"
    )
    suggested_follow_ups: List[str] = Field(
        default_factory=list, description="Relevant contextual follow-up business questions"
    )
    data_limitations_noted: Optional[str] = Field(
        None, description="Documented governance policies applied (e.g. refund/cancellation exclusions)"
    )
    needs_clarification: bool = Field(False, description="True if query was ambiguous and requires user refinement")
    clarification_question: Optional[str] = Field(None, description="Clarification prompt for user")
    model_used: str = Field(default="", description="Underlying model or orchestration engine used")


class ExecutionHistoryItem(BaseModel):
    """Historical audit record of an analyst query execution."""
    id: str = Field(..., description="Unique record identifier")
    timestamp: str = Field(..., description="Execution timestamp (ISO format)")
    question: str = Field(..., description="Inquiry prompt")
    duration_ms: float = Field(..., description="Total execution duration in ms")
    tools_count: int = Field(..., description="Number of analytics tools invoked")
    tools_executed: List[str] = Field(default_factory=list, description="Names of tools invoked")
    has_chart: bool = Field(False, description="Whether response contains dynamic chart")
    success: bool = Field(True, description="Whether query completed cleanly")
