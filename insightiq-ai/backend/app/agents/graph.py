"""LangGraph StateGraph Compilation and Workflow Orchestrator for InsightIQ AI Analyst."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from langgraph.graph import END, START, StateGraph
from sqlalchemy.orm import Session

from app.agents.nodes import (
    execute_tools_node,
    generate_answer_node,
    handle_error_node,
    select_tools_node,
    understand_question_node,
    validate_results_node,
)
from app.agents.routing import (
    MAX_AGENT_STEPS,
    route_after_generation,
    route_after_selection,
    route_after_understanding,
    route_after_validation,
)
from app.agents.state import AgentState
from app.logging_config import get_logger

logger = get_logger("insightiq.agents.graph")


def build_analyst_graph() -> StateGraph:
    """Builds the controlled AI Analyst workflow graph."""
    builder = StateGraph(AgentState)

    # 1. Register Nodes
    builder.add_node("understand_question", understand_question_node)
    builder.add_node("select_tools", select_tools_node)
    builder.add_node("execute_tools", execute_tools_node)
    builder.add_node("validate_results", validate_results_node)
    builder.add_node("generate_answer", generate_answer_node)
    builder.add_node("handle_error", handle_error_node)

    # 2. Add Transitions & Edges
    builder.add_edge(START, "understand_question")

    builder.add_conditional_edges(
        "understand_question",
        route_after_understanding,
        {
            "handle_error": "handle_error",
            "generate_answer": "generate_answer",
            "select_tools": "select_tools",
        },
    )

    builder.add_conditional_edges(
        "select_tools",
        route_after_selection,
        {
            "handle_error": "handle_error",
            "generate_answer": "generate_answer",
            "execute_tools": "execute_tools",
        },
    )

    builder.add_edge("execute_tools", "validate_results")

    builder.add_conditional_edges(
        "validate_results",
        route_after_validation,
        {
            "handle_error": "handle_error",
            "generate_answer": "generate_answer",
        },
    )

    builder.add_conditional_edges(
        "generate_answer",
        route_after_generation,
        {
            "handle_error": "handle_error",
            END: END,
        },
    )

    builder.add_edge("handle_error", END)

    return builder


# Compile the graph
analyst_graph = build_analyst_graph().compile()


def run_analyst_workflow(
    question: str,
    db: Optional[Session] = None,
    chat_history: Optional[List[Dict[str, str]]] = None,
    max_steps: int = MAX_AGENT_STEPS,
) -> AgentState:
    """Convenience runner executing the compiled LangGraph workflow from start to finish."""
    logger.info("Starting LangGraph workflow for query: '%s'", question)

    initial_state: AgentState = {
        "question": question,
        "chat_history": chat_history or [],
        "step_count": 0,
        "max_steps": max_steps,
        "execution_trace": [],
        "tool_executions": [],
        "validated_evidence": {},
        "validation_errors": [],
        "plan": [],
        "is_clarification": False,
        "clarification_question": None,
        "error": None,
        "db_session": db,
    }

    final_state = analyst_graph.invoke(initial_state)
    logger.info("LangGraph workflow finished. Steps executed: %d", len(final_state.get("execution_trace", [])))
    return final_state
