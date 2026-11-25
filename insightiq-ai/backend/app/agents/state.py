"""Typed State and Execution Tracing Schemas for the LangGraph AI Analyst Workflow."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, TypedDict
from pydantic import BaseModel, Field


class ExecutionTraceStep(BaseModel):
    """Detailed record of a single step in the agent workflow."""
    node: str = Field(..., description="Name of the executed workflow node")
    timestamp: str = Field(..., description="ISO 8601 UTC timestamp")
    duration_ms: float = Field(..., description="Node execution latency in milliseconds")
    details: Dict[str, Any] = Field(default_factory=dict, description="Diagnostic payload or node actions")


class AgentState(TypedDict, total=False):
    """Typed state dictionary threaded across all LangGraph nodes."""
    question: str
    chat_history: List[Dict[str, str]]
    intent: Optional[Dict[str, Any]]
    plan: List[Dict[str, Any]]
    tool_executions: List[Dict[str, Any]]
    validated_evidence: Dict[str, Any]
    validation_errors: List[str]
    final_response: Optional[Dict[str, Any]]
    error: Optional[str]
    step_count: int
    max_steps: int
    execution_trace: List[Dict[str, Any]]
    is_clarification: bool
    clarification_question: Optional[str]
    db_session: Optional[Any]
