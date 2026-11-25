"""LangGraph Workflow Nodes for InsightIQ AI Analyst."""

from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from app.agents.state import AgentState, ExecutionTraceStep
from app.llm import get_llm_service
from app.llm.schemas import (
    AnalysisDomain,
    AnalystInsight,
    AnalystResponse,
    EvidenceGrounding,
    InsightSeverity,
    MetricType,
    UserQueryIntent,
)
from app.logging_config import get_logger
from app.schemas.charts import ChartMetadata, ChartSpec
from app.services.chart_service import _serialize_decimals, generate_chart_from_query
from app.tools.registry import default_tool_registry

logger = get_logger("insightiq.agents.nodes")


def _record_trace(state: AgentState, node: str, duration_ms: float, details: Dict[str, Any]) -> None:
    """Helper to record a timestamped step in the workflow execution trace."""
    if "execution_trace" not in state or state["execution_trace"] is None:
        state["execution_trace"] = []

    trace_step = ExecutionTraceStep(
        node=node,
        timestamp=datetime.now(timezone.utc).isoformat(),
        duration_ms=round(duration_ms, 2),
        details=details,
    )
    state["execution_trace"].append(trace_step.model_dump())


# -----------------------------------------------------------------------------
# 1. Question Understanding Node
# -----------------------------------------------------------------------------
def understand_question_node(state: AgentState) -> AgentState:
    """Parses natural-language question, extracts temporal & entity filters, and detects ambiguity."""
    start_time = time.perf_counter()
    logger.info("Executing [understand_question_node] for: '%s'", state.get("question"))

    state["step_count"] = state.get("step_count", 0) + 1
    llm_service = get_llm_service()

    try:
        intent: UserQueryIntent = llm_service.parse_user_intent(
            state["question"],
            chat_history=state.get("chat_history"),
        )
        state["intent"] = intent.model_dump()

        if intent.is_ambiguous:
            state["is_clarification"] = True
            state["clarification_question"] = intent.clarification_needed or (
                "Could you please specify the timeframe (e.g., Q1 2024) or target metric?"
            )
        else:
            state["is_clarification"] = False
            state["clarification_question"] = None

    except Exception as exc:
        logger.error("Error in understand_question_node: %s", exc, exc_info=True)
        state["error"] = f"Failed to understand query intent: {exc}"

    duration_ms = (time.perf_counter() - start_time) * 1000.0
    _record_trace(
        state,
        node="understand_question",
        duration_ms=duration_ms,
        details={"intent": state.get("intent"), "is_clarification": state.get("is_clarification")},
    )
    return state


# -----------------------------------------------------------------------------
# 2. Tool Selection Node
# -----------------------------------------------------------------------------
def select_tools_node(state: AgentState) -> AgentState:
    """Formulates a deterministic plan of approved tool calls based on user intent."""
    start_time = time.perf_counter()
    logger.info("Executing [select_tools_node]")

    if state.get("is_clarification") or state.get("error"):
        state["plan"] = []
        duration_ms = (time.perf_counter() - start_time) * 1000.0
        _record_trace(state, node="select_tools", duration_ms=duration_ms, details={"plan": []})
        return state

    intent_dict = state.get("intent", {})
    domain = intent_dict.get("domain")
    metric = intent_dict.get("primary_metric")
    timeframe = intent_dict.get("timeframe") or {}
    entity_filters = intent_dict.get("entity_filters") or {}
    suggested = intent_dict.get("suggested_tools") or []
    q_lower = state.get("question", "").lower()

    # Extract clean start_date and end_date arguments
    args: Dict[str, Any] = {}
    if timeframe.get("start_date"):
        args["start_date"] = timeframe["start_date"]
    if timeframe.get("end_date"):
        args["end_date"] = timeframe["end_date"]

    limit_arg = entity_filters.get("limit") or 10
    plan: List[Dict[str, Any]] = []

    # 1. Diagnostic / Multi-Step Queries (e.g. revenue drop or cross-domain analysis)
    if "investigate_revenue_decline" in suggested or domain == AnalysisDomain.CROSS_DOMAIN.value or metric == MetricType.DIAGNOSTIC_DECLINE.value:
        plan.append({
            "tool_name": "investigate_revenue_decline",
            "arguments": args.copy(),
            "rationale": "Perform period-over-period waterfall analysis isolating category and SKU drivers",
        })
        plan.append({
            "tool_name": "get_monthly_revenue",
            "arguments": args.copy(),
            "rationale": "Verify monthly revenue trend and identify exact decline point",
        })
        plan.append({
            "tool_name": "get_revenue_by_category",
            "arguments": args.copy(),
            "rationale": "Identify which product categories drove the revenue contraction",
        })
        plan.append({
            "tool_name": "get_low_performing_products",
            "arguments": {**args.copy(), "limit": 10},
            "rationale": "Isolate specific zero-sales or underperforming SKUs",
        })

    # 2. Low-performing Products
    elif "get_low_performing_products" in suggested or metric == MetricType.LOW_PERFORMING_PRODUCTS.value:
        plan.append({"tool_name": "get_low_performing_products", "arguments": {**args.copy(), "limit": limit_arg}})

    # 3. Top Products
    elif "get_top_products" in suggested or (domain == AnalysisDomain.PRODUCTS.value and metric == MetricType.TOP_PRODUCTS.value):
        plan.append({"tool_name": "get_top_products", "arguments": {**args.copy(), "limit": limit_arg}})

    # 4. Top Customers
    elif "get_top_customers" in suggested or (domain == AnalysisDomain.CUSTOMERS.value and any(w in q_lower for w in ["top", "spend", "vip", "biggest", "who"])):
        plan.append({"tool_name": "get_top_customers", "arguments": {**args.copy(), "limit": limit_arg}})

    # 5. Customer Order Frequency
    elif "get_customer_order_frequency" in suggested or metric == MetricType.ORDER_FREQUENCY.value or any(w in q_lower for w in ["frequency", "how often", "distribution", "bracket"]):
        plan.append({"tool_name": "get_customer_order_frequency", "arguments": args.copy()})

    # 6. Sales Growth
    elif "get_sales_growth" in suggested or metric == MetricType.GROWTH.value or "growth" in q_lower:
        curr_start = args.get("start_date") or "2024-02-01"
        curr_end = args.get("end_date") or "2024-02-29"
        plan.append({
            "tool_name": "get_sales_growth",
            "arguments": {
                "current_start": curr_start,
                "current_end": curr_end,
                "previous_start": "2024-01-01",
                "previous_end": "2024-01-31",
            },
        })

    # 7. Customer Metrics
    elif "get_customer_metrics" in suggested or domain == AnalysisDomain.CUSTOMERS.value:
        plan.append({"tool_name": "get_customer_metrics", "arguments": args.copy()})

    # 8. Monthly Revenue
    elif "get_monthly_revenue" in suggested or metric == MetricType.MONTHLY_TREND.value:
        plan.append({"tool_name": "get_monthly_revenue", "arguments": args.copy()})

    # 9. Revenue by Category
    elif "get_revenue_by_category" in suggested or metric == MetricType.CATEGORY_BREAKDOWN.value:
        plan.append({"tool_name": "get_revenue_by_category", "arguments": args.copy()})

    # 10. Sales Metrics
    elif "get_sales_metrics" in suggested or (domain == AnalysisDomain.SALES.value and metric == MetricType.REVENUE.value):
        plan.append({"tool_name": "get_sales_metrics", "arguments": args.copy()})

    # 11. Consolidated Dashboard Summary / Fallback
    else:
        plan.append({"tool_name": "get_dashboard_summary", "arguments": args.copy()})

    state["plan"] = plan
    duration_ms = (time.perf_counter() - start_time) * 1000.0
    _record_trace(state, node="select_tools", duration_ms=duration_ms, details={"planned_tools": [p["tool_name"] for p in plan]})
    return state


# -----------------------------------------------------------------------------
# 3. Tool Execution Node
# -----------------------------------------------------------------------------
def execute_tools_node(state: AgentState) -> AgentState:
    """Executes the approved tool plan in sequence using the ToolRegistry."""
    start_time = time.perf_counter()
    logger.info("Executing [execute_tools_node]")

    if "tool_executions" not in state or state["tool_executions"] is None:
        state["tool_executions"] = []

    plan = state.get("plan", [])
    db: Optional[Session] = state.get("db_session")

    for item in plan:
        tool_name = item["tool_name"]
        arguments = item.get("arguments", {})

        result = default_tool_registry.execute_tool(tool_name, arguments, db=db)
        state["tool_executions"].append(result.model_dump())

    duration_ms = (time.perf_counter() - start_time) * 1000.0
    _record_trace(
        state,
        node="execute_tools",
        duration_ms=duration_ms,
        details={"executed_count": len(plan)},
    )
    return state


# -----------------------------------------------------------------------------
# 4. Result Validation Node
# -----------------------------------------------------------------------------
def validate_results_node(state: AgentState) -> AgentState:
    """Inspects tool execution outputs, validates data integrity, and aggregates evidence."""
    start_time = time.perf_counter()
    logger.info("Executing [validate_results_node]")

    if "validated_evidence" not in state or state["validated_evidence"] is None:
        state["validated_evidence"] = {}
    if "validation_errors" not in state or state["validation_errors"] is None:
        state["validation_errors"] = []

    tool_executions = state.get("tool_executions", [])
    successful_count = 0

    for res in tool_executions:
        tool_name = res.get("tool_name")
        success = res.get("success", False)
        error = res.get("error")
        data = res.get("data")

        if not success:
            state["validation_errors"].append(f"Tool '{tool_name}' failed: {error}")
        else:
            successful_count += 1
            state["validated_evidence"][tool_name] = data

    # If all planned tools failed, set fatal error state
    if tool_executions and successful_count == 0:
        state["error"] = "All planned analytics queries failed: " + "; ".join(state["validation_errors"])

    duration_ms = (time.perf_counter() - start_time) * 1000.0
    _record_trace(
        state,
        node="validate_results",
        duration_ms=duration_ms,
        details={
            "successful_count": successful_count,
            "failed_count": len(tool_executions) - successful_count,
            "validation_errors": state["validation_errors"],
        },
    )
    return state


# -----------------------------------------------------------------------------
# 5. Answer Generation Node
# -----------------------------------------------------------------------------
def generate_answer_node(state: AgentState) -> AgentState:
    """Generates a structured, evidence-grounded response using the LLM Service."""
    start_time = time.perf_counter()
    logger.info("Executing [generate_answer_node]")

    llm_service = get_llm_service()

    # Case 1: Clarification required
    if state.get("is_clarification"):
        response = llm_service.create_clarification_response(
            question=state["question"],
            clarification_prompt=state.get("clarification_question") or "Please provide more details.",
        )
        state["final_response"] = response.model_dump()
        duration_ms = (time.perf_counter() - start_time) * 1000.0
        _record_trace(state, node="generate_answer", duration_ms=duration_ms, details={"status": "clarification"})
        return state

    # Case 2: Evidence synthesis
    evidence = state.get("validated_evidence", {})
    try:
        response = llm_service.synthesize_grounded_response(
            user_question=state["question"],
            evidence_data=evidence,
            chat_history=state.get("chat_history"),
        )
        resp_dict = response.model_dump()

        # Dynamic Chart Generation if requested or appropriate for evidence
        intent_info = state.get("intent", {})
        q_lower = state.get("question", "").lower()
        wants_chart = intent_info.get("requires_chart") or any(
            w in q_lower for w in ["chart", "plot", "graph", "visualize", "trend"]
        )

        if wants_chart:
            try:
                # 1. Monthly revenue trend
                if "get_monthly_revenue" in evidence and evidence["get_monthly_revenue"]:
                    clean_data = _serialize_decimals(evidence["get_monthly_revenue"])
                    p_type = intent_info.get("preferred_chart_type") or "line"
                    if p_type not in ("line", "area", "bar"):
                        p_type = "line"
                    cs = ChartSpec(
                        chart_type=p_type,
                        title="Monthly Revenue Trend",
                        x_key="month",
                        y_key="revenue",
                        y_keys=["revenue", "units_sold"],
                        data=clean_data,
                        metadata=ChartMetadata(
                            x_label="Month", y_label="Revenue ($)", unit="$", source_tool="get_monthly_revenue"
                        ),
                    )
                    resp_dict["chart_spec"] = cs.model_dump()

                # 2. Revenue by category
                elif "get_revenue_by_category" in evidence and evidence["get_revenue_by_category"]:
                    clean_data = _serialize_decimals(evidence["get_revenue_by_category"])
                    p_type = intent_info.get("preferred_chart_type") or "pie"
                    if p_type not in ("pie", "bar"):
                        p_type = "pie"
                    cs = ChartSpec(
                        chart_type=p_type,
                        title="Revenue by Category",
                        x_key="category",
                        y_key="revenue",
                        data=clean_data,
                        metadata=ChartMetadata(
                            x_label="Category", y_label="Revenue ($)", unit="$", source_tool="get_revenue_by_category"
                        ),
                    )
                    resp_dict["chart_spec"] = cs.model_dump()

                # 3. Top products
                elif ("get_top_products" in evidence and evidence["get_top_products"]) or ("get_revenue_by_product" in evidence and evidence["get_revenue_by_product"]):
                    raw_prods = evidence.get("get_top_products") or evidence.get("get_revenue_by_product") or []
                    clean_data = _serialize_decimals(raw_prods)
                    p_type = intent_info.get("preferred_chart_type") or "bar"
                    if p_type not in ("bar", "line"):
                        p_type = "bar"
                    y_key = "revenue" if "revenue" in clean_data[0] else "units_sold"
                    cs = ChartSpec(
                        chart_type=p_type,
                        title="Top Products by Performance",
                        x_key="product_name",
                        y_key=y_key,
                        data=clean_data,
                        metadata=ChartMetadata(
                            x_label="Product Name", y_label="Revenue ($)" if y_key == "revenue" else "Units", unit="$" if y_key == "revenue" else "units", source_tool="get_top_products"
                        ),
                    )
                    resp_dict["chart_spec"] = cs.model_dump()

                # 4. Top customers
                elif "get_top_customers" in evidence and evidence["get_top_customers"]:
                    clean_data = _serialize_decimals(evidence["get_top_customers"])
                    cs = ChartSpec(
                        chart_type="bar",
                        title="Top Customers by Total Spend",
                        x_key="name",
                        y_key="total_spend",
                        data=clean_data,
                        metadata=ChartMetadata(
                            x_label="Customer Name", y_label="Total Spend ($)", unit="$", source_tool="get_top_customers"
                        ),
                    )
                    resp_dict["chart_spec"] = cs.model_dump()

                # 5. Low performing products
                elif "get_low_performing_products" in evidence and evidence["get_low_performing_products"]:
                    clean_data = _serialize_decimals(evidence["get_low_performing_products"])
                    cs = ChartSpec(
                        chart_type="bar",
                        title="Low Performing Products",
                        x_key="product_name",
                        y_key="revenue",
                        data=clean_data,
                        metadata=ChartMetadata(
                            x_label="Product Name", y_label="Revenue ($)", unit="$", source_tool="get_low_performing_products"
                        ),
                    )
                    resp_dict["chart_spec"] = cs.model_dump()

                # 6. Fallback: try generating from database session if available
                elif state.get("db_session"):
                    cs = generate_chart_from_query(db=state["db_session"], query=state["question"])
                    resp_dict["chart_spec"] = cs.model_dump()

            except Exception as chart_err:
                logger.warning("Could not automatically generate chart spec: %s", chart_err)

        # Contextual suggested follow-ups
        metric_val = intent_info.get("primary_metric")
        domain_val = intent_info.get("domain")
        follow_ups = []
        if metric_val == MetricType.DIAGNOSTIC_DECLINE.value or "why" in q_lower:
            follow_ups = [
                "Which specific products drove the revenue decline?",
                "How did repeat customer orders change during this period?",
                "Show monthly revenue trend as a chart.",
            ]
        elif domain_val == AnalysisDomain.CUSTOMERS.value:
            follow_ups = [
                "Who are our top customers by total spend?",
                "What is our customer retention and repeat buyer rate?",
                "What is the average order value across active buyers?",
            ]
        elif domain_val == AnalysisDomain.PRODUCTS.value:
            follow_ups = [
                "Which products generate the most revenue?",
                "Show low-performing or zero-sales products.",
                "Compare revenue by category.",
            ]
        elif domain_val == AnalysisDomain.SALES.value:
            follow_ups = [
                "Show monthly revenue as a chart.",
                "Compare revenue by category.",
                "Who are our repeat customers?",
            ]
        else:
            follow_ups = [
                "What is our total revenue?",
                "Show monthly revenue.",
                "Which products generate the most revenue?",
            ]
        resp_dict["suggested_follow_ups"] = follow_ups

        state["final_response"] = resp_dict
    except Exception as exc:
        logger.error("Error synthesizing grounded response: %s", exc, exc_info=True)
        state["error"] = f"Failed to synthesize grounded response: {exc}"

    duration_ms = (time.perf_counter() - start_time) * 1000.0
    _record_trace(state, node="generate_answer", duration_ms=duration_ms, details={"status": "complete"})
    return state


# -----------------------------------------------------------------------------
# 6. Error Handling Node
# -----------------------------------------------------------------------------
def handle_error_node(state: AgentState) -> AgentState:
    """Produces a transparent, honest error response when execution cannot proceed."""
    start_time = time.perf_counter()
    logger.warning("Executing [handle_error_node] with error: %s", state.get("error"))

    err_msg = state.get("error") or "An unexpected workflow execution error occurred."

    response = AnalystResponse(
        question=state.get("question", "Unknown"),
        summary="InsightIQ AI could not complete this analytical inquiry due to an execution failure.",
        insights=[
            AnalystInsight(
                title="Query Execution Failure",
                finding=err_msg,
                evidence=[],
                severity=InsightSeverity.CRITICAL,
                actionable_recommendation="Verify database connectivity or adjust your query timeframe.",
            )
        ],
        metrics_referenced=[],
        needs_clarification=False,
        data_limitations_noted="No numerical results were generated or fabricated.",
    )

    state["final_response"] = response.model_dump()
    duration_ms = (time.perf_counter() - start_time) * 1000.0
    _record_trace(state, node="handle_error", duration_ms=duration_ms, details={"error": err_msg})
    return state
