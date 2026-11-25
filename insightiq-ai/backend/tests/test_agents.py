"""Unit and Workflow Integration Tests for LangGraph AI Analyst Graph."""

from unittest.mock import MagicMock, patch
import pytest
from langgraph.graph import END

from app.agents.graph import analyst_graph, run_analyst_workflow
from app.agents.nodes import (
    execute_tools_node,
    generate_answer_node,
    handle_error_node,
    select_tools_node,
    understand_question_node,
    validate_results_node,
)
from app.agents.routing import (
    route_after_generation,
    route_after_selection,
    route_after_understanding,
    route_after_validation,
)
from app.agents.state import AgentState
from app.llm.schemas import (
    AnalysisDomain,
    AnalystInsight,
    AnalystResponse,
    EvidenceGrounding,
    InsightSeverity,
    MetricType,
    UserQueryIntent,
)


# -----------------------------------------------------------------------------
# 1. Routing Logic Unit Tests
# -----------------------------------------------------------------------------
def test_route_after_understanding():
    """Tests routing transitions based on intent and ambiguity."""
    # Standard query -> select_tools
    state1: AgentState = {"error": None, "is_clarification": False}
    assert route_after_understanding(state1) == "select_tools"

    # Ambiguous query -> generate_answer (clarification)
    state2: AgentState = {"error": None, "is_clarification": True}
    assert route_after_understanding(state2) == "generate_answer"

    # Error present -> handle_error
    state3: AgentState = {"error": "LLM failed"}
    assert route_after_understanding(state3) == "handle_error"


def test_route_after_selection():
    """Tests routing based on planned tool availability."""
    # Plan has tools -> execute_tools
    state1: AgentState = {"error": None, "plan": [{"tool_name": "get_sales_metrics"}]}
    assert route_after_selection(state1) == "execute_tools"

    # Plan is empty -> generate_answer
    state2: AgentState = {"error": None, "plan": []}
    assert route_after_selection(state2) == "generate_answer"

    # Error -> handle_error
    state3: AgentState = {"error": "Planning crashed"}
    assert route_after_selection(state3) == "handle_error"


def test_route_after_validation_and_loop_prevention():
    """Tests routing after tool validation including infinite loop protection."""
    # Normal success -> generate_answer
    state1: AgentState = {"error": None, "step_count": 1, "max_steps": 5}
    assert route_after_validation(state1) == "generate_answer"

    # Fatal error -> handle_error
    state2: AgentState = {"error": "All tools failed", "step_count": 1, "max_steps": 5}
    assert route_after_validation(state2) == "handle_error"

    # Loop prevention limit exceeded -> handle_error
    state3: AgentState = {"error": None, "step_count": 5, "max_steps": 5}
    next_node = route_after_validation(state3)
    assert next_node == "handle_error"
    assert "Maximum execution limit" in state3["error"]


def test_route_after_generation():
    """Tests completion edge transition."""
    # Successful response -> END
    state1: AgentState = {"error": None, "final_response": {"summary": "Done"}}
    assert route_after_generation(state1) == END

    # Generation failed without response -> handle_error
    state2: AgentState = {"error": "Synthesis error", "final_response": None}
    assert route_after_generation(state2) == "handle_error"


# -----------------------------------------------------------------------------
# 2. Individual Node Execution Unit Tests
# -----------------------------------------------------------------------------
def test_understand_question_node_standard():
    """Verifies question understanding node extracts intent and records trace."""
    mock_intent = UserQueryIntent(
        original_question="What is total revenue in Q1 2024?",
        domain=AnalysisDomain.SALES,
        primary_metric=MetricType.REVENUE,
        timeframe={"start_date": "2024-01-01", "end_date": "2024-03-31"},
        is_ambiguous=False,
    )

    with patch("app.agents.nodes.get_llm_service") as mock_get_svc:
        mock_svc = MagicMock()
        mock_svc.parse_user_intent.return_value = mock_intent
        mock_get_svc.return_value = mock_svc

        state: AgentState = {
            "question": "What is total revenue in Q1 2024?",
            "execution_trace": [],
        }
        updated = understand_question_node(state)

        assert updated["is_clarification"] is False
        assert updated["intent"]["domain"] == "sales"
        assert len(updated["execution_trace"]) == 1
        assert updated["execution_trace"][0]["node"] == "understand_question"


def test_understand_question_node_ambiguous():
    """Verifies ambiguous question flags clarification in state."""
    mock_intent = UserQueryIntent(
        original_question="How are sales?",
        domain=AnalysisDomain.SALES,
        primary_metric=MetricType.REVENUE,
        is_ambiguous=True,
        clarification_needed="Please specify the timeframe.",
    )

    with patch("app.agents.nodes.get_llm_service") as mock_get_svc:
        mock_svc = MagicMock()
        mock_svc.parse_user_intent.return_value = mock_intent
        mock_get_svc.return_value = mock_svc

        state: AgentState = {"question": "How are sales?", "execution_trace": []}
        updated = understand_question_node(state)

        assert updated["is_clarification"] is True
        assert "timeframe" in updated["clarification_question"]


def test_select_tools_node_multi_step():
    """Verifies multi-step diagnostic planning for cross-domain inquiries."""
    state: AgentState = {
        "question": "Why did sales drop in March 2024?",
        "intent": {
            "domain": "cross_domain",
            "primary_metric": "diagnostic_decline",
            "timeframe": {"start_date": "2024-03-01", "end_date": "2024-03-31"},
        },
        "is_clarification": False,
        "execution_trace": [],
    }

    updated = select_tools_node(state)
    planned_tools = [p["tool_name"] for p in updated["plan"]]

    # Must plan multi-tool diagnostic sequence
    assert "get_monthly_revenue" in planned_tools
    assert "get_revenue_by_category" in planned_tools
    assert "get_low_performing_products" in planned_tools


def test_execute_and_validate_tools_nodes(seeded_db_session):
    """Verifies tools execution and evidence validation against ground-truth DB."""
    state: AgentState = {
        "plan": [
            {"tool_name": "get_sales_metrics", "arguments": {"start_date": "2024-01-01", "end_date": "2024-03-31"}},
            {"tool_name": "get_monthly_revenue", "arguments": {"start_date": "2024-01-01", "end_date": "2024-03-31"}},
        ],
        "db_session": seeded_db_session,
        "tool_executions": [],
        "execution_trace": [],
    }

    # Execute
    after_exec = execute_tools_node(state)
    assert len(after_exec["tool_executions"]) == 2
    assert after_exec["tool_executions"][0]["success"] is True

    # Validate
    after_val = validate_results_node(after_exec)
    assert "get_sales_metrics" in after_val["validated_evidence"]
    assert after_val["validated_evidence"]["get_sales_metrics"]["total_revenue"] == 2490.00
    assert len(after_val["validation_errors"]) == 0


def test_validate_tools_node_catches_all_failures():
    """Verifies that all tool failures trigger a fatal error state."""
    state: AgentState = {
        "tool_executions": [
            {"tool_name": "bad_tool_1", "success": False, "error": "Crash 1", "data": None},
            {"tool_name": "bad_tool_2", "success": False, "error": "Crash 2", "data": None},
        ],
        "validated_evidence": {},
        "validation_errors": [],
        "execution_trace": [],
    }
    updated = validate_results_node(state)
    assert updated["error"] is not None
    assert "All planned analytics queries failed" in updated["error"]


def test_handle_error_node_produces_honest_response():
    """Verifies error handling produces a transparent response with no fabricated data."""
    state: AgentState = {
        "question": "What is revenue?",
        "error": "Database connection refused at 10.0.0.1",
        "execution_trace": [],
    }
    updated = handle_error_node(state)
    res = updated["final_response"]
    assert res is not None
    assert "could not complete" in res["summary"]
    assert "Database connection refused" in res["insights"][0]["finding"]
    assert "No numerical results were generated or fabricated" in res["data_limitations_noted"]


# -----------------------------------------------------------------------------
# 3. End-to-End Workflow Execution Tests
# -----------------------------------------------------------------------------
def test_e2e_workflow_single_tool(seeded_db_session):
    """End-to-end integration test of the full LangGraph workflow for a single metric query."""
    mock_intent = UserQueryIntent(
        original_question="What is total revenue in Q1 2024?",
        domain=AnalysisDomain.SALES,
        primary_metric=MetricType.REVENUE,
        timeframe={"start_date": "2024-01-01", "end_date": "2024-03-31"},
        is_ambiguous=False,
    )

    mock_analyst_response = AnalystResponse(
        question="What is total revenue in Q1 2024?",
        summary="Total revenue for Q1 2024 reached $2,490.00 across 5 eligible orders.",
        insights=[
            AnalystInsight(
                title="Q1 Revenue",
                finding="Revenue totaled $2,490.00 across 5 completed and pending orders.",
                evidence=[
                    EvidenceGrounding(
                        metric_name="Total Revenue",
                        exact_value=2490.00,
                        source="get_sales_metrics",
                    )
                ],
                severity=InsightSeverity.POSITIVE,
            )
        ],
        metrics_referenced=[],
        needs_clarification=False,
    )

    with patch("app.agents.nodes.get_llm_service") as mock_get_svc:
        mock_svc = MagicMock()
        mock_svc.parse_user_intent.return_value = mock_intent
        mock_svc.synthesize_grounded_response.return_value = mock_analyst_response
        mock_get_svc.return_value = mock_svc

        final_state = run_analyst_workflow(
            question="What is total revenue in Q1 2024?",
            db=seeded_db_session,
        )

        assert final_state["final_response"] is not None
        assert final_state["final_response"]["summary"].startswith("Total revenue for Q1 2024 reached $2,490.00")
        assert len(final_state["tool_executions"]) == 1
        assert final_state["tool_executions"][0]["data"]["total_revenue"] == 2490.00

        # Verify execution trace contains all planned nodes
        node_names = [step["node"] for step in final_state["execution_trace"]]
        assert "understand_question" in node_names
        assert "select_tools" in node_names
        assert "execute_tools" in node_names
        assert "validate_results" in node_names
        assert "generate_answer" in node_names


def test_e2e_workflow_ambiguous_routes_to_clarification():
    """End-to-end integration test verifying ambiguous query skips tools and asks for clarification."""
    mock_intent = UserQueryIntent(
        original_question="How are sales?",
        domain=AnalysisDomain.SALES,
        primary_metric=MetricType.REVENUE,
        is_ambiguous=True,
        clarification_needed="Please specify which quarter you want to analyze.",
    )

    with patch("app.agents.nodes.get_llm_service") as mock_get_svc:
        mock_svc = MagicMock()
        mock_svc.parse_user_intent.return_value = mock_intent
        mock_svc.create_clarification_response.return_value = AnalystResponse(
            question="How are sales?",
            summary="Clarification required.",
            insights=[],
            needs_clarification=True,
            clarification_question="Please specify which quarter you want to analyze.",
        )
        mock_get_svc.return_value = mock_svc

        final_state = run_analyst_workflow(question="How are sales?")

        assert final_state["is_clarification"] is True
        assert final_state["final_response"]["needs_clarification"] is True
        # Verify tool execution was bypassed
        assert len(final_state["tool_executions"]) == 0
        node_names = [step["node"] for step in final_state["execution_trace"]]
        assert "execute_tools" not in node_names
        assert "generate_answer" in node_names


def test_e2e_workflow_preserves_conversation_context():
    """Verifies that existing conversation history is retained in the workflow state."""
    history = [
        {"role": "user", "content": "Hello InsightIQ"},
        {"role": "assistant", "content": "Hello! I am your AI Business Analyst."},
    ]

    mock_intent = UserQueryIntent(
        original_question="Hi again",
        domain=AnalysisDomain.GENERAL,
        primary_metric=MetricType.UNKNOWN,
        is_ambiguous=True,
        clarification_needed="How can I assist your business today?",
    )

    with patch("app.agents.nodes.get_llm_service") as mock_get_svc:
        mock_svc = MagicMock()
        mock_svc.parse_user_intent.return_value = mock_intent
        mock_svc.create_clarification_response.return_value = AnalystResponse(
            question="Hi again",
            summary="Greetings.",
            insights=[],
            needs_clarification=True,
        )
        mock_get_svc.return_value = mock_svc

        final_state = run_analyst_workflow(question="Hi again", chat_history=history)
        assert len(final_state["chat_history"]) == 2
        assert final_state["chat_history"][0]["content"] == "Hello InsightIQ"
