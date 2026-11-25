"""Conditional Edge Routing and Guardrails for LangGraph Workflow."""

from __future__ import annotations

from typing import Literal
from langgraph.graph import END
from app.agents.state import AgentState
from app.logging_config import get_logger

logger = get_logger("insightiq.agents.routing")

MAX_AGENT_STEPS = 5


def route_after_understanding(state: AgentState) -> Literal["handle_error", "generate_answer", "select_tools"]:
    """Determines next node after question understanding."""
    if state.get("error"):
        logger.warning("Routing to [handle_error] due to understanding error")
        return "handle_error"

    if state.get("is_clarification"):
        logger.info("Query requires clarification; routing directly to [generate_answer]")
        return "generate_answer"

    return "select_tools"


def route_after_selection(state: AgentState) -> Literal["handle_error", "generate_answer", "execute_tools"]:
    """Determines next node after tool selection."""
    if state.get("error"):
        return "handle_error"

    plan = state.get("plan", [])
    if not plan:
        logger.info("No tools planned for query; routing directly to [generate_answer]")
        return "generate_answer"

    return "execute_tools"


def route_after_validation(state: AgentState) -> Literal["handle_error", "generate_answer"]:
    """Determines next node after tool result validation with loop prevention."""
    step_count = state.get("step_count", 0)
    max_steps = state.get("max_steps", MAX_AGENT_STEPS)

    # 1. Enforce maximum execution limit / Infinite loop protection
    if step_count >= max_steps:
        logger.error("Execution limit exceeded (step_count=%d >= max_steps=%d)", step_count, max_steps)
        state["error"] = f"Workflow aborted: Maximum execution limit of {max_steps} steps exceeded."
        return "handle_error"

    # 2. Check for fatal execution errors
    if state.get("error"):
        logger.warning("Routing to [handle_error] due to validation error: %s", state.get("error"))
        return "handle_error"

    return "generate_answer"


def route_after_generation(state: AgentState) -> Literal["handle_error", "__end__"]:
    """Determines whether answer generation succeeded or requires error handling."""
    if state.get("error") and not state.get("final_response"):
        return "handle_error"
    return END
