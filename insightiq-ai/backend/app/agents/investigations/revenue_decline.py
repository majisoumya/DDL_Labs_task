"""Multi-Step Revenue Decline Investigation Graph and Diagnostic Engine."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, TypedDict
from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.agents.investigations.comparison import (
    MetricDelta,
    calculate_metric_delta,
    resolve_comparison_periods,
)
from app.agents.investigations.contribution import (
    CategoryContribution,
    CustomerActivityComparison,
    ProductContribution,
    analyze_category_contributions,
    analyze_customer_activity,
    analyze_product_contributions,
)
from app.logging_config import get_logger
from app.services.customer_service import get_customer_metrics
from app.services.sales_service import (
    get_revenue_by_category,
    get_revenue_by_product,
    get_sales_metrics,
)

logger = get_logger("insightiq.investigations.revenue_decline")


# -----------------------------------------------------------------------------
# 1. Output Schemas
# -----------------------------------------------------------------------------
class PeriodSummary(BaseModel):
    """Aggregated sales performance metrics for a specific window."""
    start_date: str = Field(..., description="Window start date (YYYY-MM-DD)")
    end_date: str = Field(..., description="Window end date (YYYY-MM-DD)")
    revenue: float = Field(..., description="Total eligible sales revenue")
    orders: int = Field(..., description="Total eligible completed/pending orders count")
    aov: float = Field(..., description="Average Order Value (revenue / orders)")


class EvidenceDataPoint(BaseModel):
    """Deterministic verifiable calculation supporting the investigation."""
    metric: str
    value: Any
    period: str
    source: str


class RevenueDeclineReport(BaseModel):
    """Complete multi-faceted diagnostic investigation of revenue change."""
    summary: str = Field(..., description="Executive synthesis of the revenue change and key drivers")
    current_period: PeriodSummary = Field(..., description="Current evaluation period metrics")
    previous_period: PeriodSummary = Field(..., description="Baseline comparison period metrics")
    revenue_change: MetricDelta = Field(..., description="Variance in total gross sales revenue")
    order_change: MetricDelta = Field(..., description="Variance in order transaction volume")
    aov_change: MetricDelta = Field(..., description="Variance in Average Order Value")
    category_contributions: List[CategoryContribution] = Field(
        default_factory=list, description="Category-level variance decomposition"
    )
    product_contributions: List[ProductContribution] = Field(
        default_factory=list, description="SKU-level variance decomposition"
    )
    customer_activity: CustomerActivityComparison = Field(
        ..., description="Customer cohort acquisition and active buyer behavior"
    )
    evidence: List[EvidenceDataPoint] = Field(
        default_factory=list, description="Audit trail of exact calculated data points"
    )
    limitations: str = Field(
        ..., description="Methodological notes and unobserved factors (distinguishing correlation from causation)"
    )


# -----------------------------------------------------------------------------
# 2. LangGraph Typed State
# -----------------------------------------------------------------------------
class InvestigationState(TypedDict, total=False):
    """State threaded through the revenue decline investigation graph."""
    current_start: Optional[str]
    current_end: Optional[str]
    previous_start: Optional[str]
    previous_end: Optional[str]
    resolved_current_start: str
    resolved_current_end: str
    resolved_previous_start: str
    resolved_previous_end: str
    current_sales: Dict[str, Any]
    previous_sales: Dict[str, Any]
    revenue_delta: Dict[str, Any]
    order_delta: Dict[str, Any]
    aov_delta: Dict[str, Any]
    category_contributions: List[Dict[str, Any]]
    product_contributions: List[Dict[str, Any]]
    customer_comparison: Dict[str, Any]
    evidence: List[Dict[str, Any]]
    summary: str
    limitations: str
    final_report: Optional[Dict[str, Any]]
    error: Optional[str]
    db_session: Any


# -----------------------------------------------------------------------------
# 3. Investigation Graph Nodes
# -----------------------------------------------------------------------------
def resolve_periods_node(state: InvestigationState) -> InvestigationState:
    """Node 1: Resolves comparison timeframes and validates date bounds."""
    c_start, c_end, p_start, p_end = resolve_comparison_periods(
        current_start=state.get("current_start"),
        current_end=state.get("current_end"),
        previous_start=state.get("previous_start"),
        previous_end=state.get("previous_end"),
    )
    state["resolved_current_start"] = c_start
    state["resolved_current_end"] = c_end
    state["resolved_previous_start"] = p_start
    state["resolved_previous_end"] = p_end
    state["evidence"] = []
    logger.info("Resolved comparison periods: [%s to %s] vs [%s to %s]", c_start, c_end, p_start, p_end)
    return state


def calculate_sales_deltas_node(state: InvestigationState) -> InvestigationState:
    """Node 2: Queries database for both periods and computes revenue, order, and AOV deltas."""
    db: Session = state["db_session"]
    c_start, c_end = state["resolved_current_start"], state["resolved_current_end"]
    p_start, p_end = state["resolved_previous_start"], state["resolved_previous_end"]

    # 1. Fetch sales metrics for both periods
    curr_metrics = get_sales_metrics(db, start_date=c_start, end_date=c_end)
    prev_metrics = get_sales_metrics(db, start_date=p_start, end_date=p_end)

    c_rev = float(curr_metrics["total_revenue"])
    p_rev = float(prev_metrics["total_revenue"])
    c_ord = int(curr_metrics["total_orders"])
    p_ord = int(prev_metrics["total_orders"])
    c_aov = float(curr_metrics["aov"])
    p_aov = float(prev_metrics["aov"])

    state["current_sales"] = curr_metrics
    state["previous_sales"] = prev_metrics

    # 2. Compute deltas
    state["revenue_delta"] = calculate_metric_delta(c_rev, p_rev).model_dump()
    state["order_delta"] = calculate_metric_delta(c_ord, p_ord).model_dump()
    state["aov_delta"] = calculate_metric_delta(c_aov, p_aov).model_dump()

    # Record evidence points
    state["evidence"].append(EvidenceDataPoint(metric="Revenue", value=c_rev, period=f"{c_start} to {c_end}", source="get_sales_metrics").model_dump())
    state["evidence"].append(EvidenceDataPoint(metric="Revenue", value=p_rev, period=f"{p_start} to {p_end}", source="get_sales_metrics").model_dump())
    state["evidence"].append(EvidenceDataPoint(metric="Eligible Orders", value=c_ord, period=f"{c_start} to {c_end}", source="get_sales_metrics").model_dump())
    state["evidence"].append(EvidenceDataPoint(metric="Eligible Orders", value=p_ord, period=f"{p_start} to {p_end}", source="get_sales_metrics").model_dump())
    return state


def analyze_category_contributions_node(state: InvestigationState) -> InvestigationState:
    """Node 3: Performs category-level variance decomposition."""
    db: Session = state["db_session"]
    c_start, c_end = state["resolved_current_start"], state["resolved_current_end"]
    p_start, p_end = state["resolved_previous_start"], state["resolved_previous_end"]
    rev_delta = float(state["revenue_delta"]["absolute_change"])

    curr_cats = get_revenue_by_category(db, start_date=c_start, end_date=c_end)
    prev_cats = get_revenue_by_category(db, start_date=p_start, end_date=p_end)

    cat_contribs = analyze_category_contributions(curr_cats, prev_cats, total_revenue_delta=rev_delta)
    state["category_contributions"] = [c.model_dump() for c in cat_contribs]

    for c in cat_contribs:
        state["evidence"].append(
            EvidenceDataPoint(
                metric=f"Category Revenue: {c.category}",
                value=f"Curr: ${c.current_revenue}, Prev: ${c.previous_revenue}, Delta: ${c.absolute_change} ({c.contribution_share}%)",
                period="Comparison",
                source="get_revenue_by_category",
            ).model_dump()
        )
    return state


def analyze_product_contributions_node(state: InvestigationState) -> InvestigationState:
    """Node 4: Performs item-level SKU variance decomposition."""
    db: Session = state["db_session"]
    c_start, c_end = state["resolved_current_start"], state["resolved_current_end"]
    p_start, p_end = state["resolved_previous_start"], state["resolved_previous_end"]

    curr_prods = get_revenue_by_product(db, limit=50, start_date=c_start, end_date=c_end)
    prev_prods = get_revenue_by_product(db, limit=50, start_date=p_start, end_date=p_end)

    prod_contribs = analyze_product_contributions(curr_prods, prev_prods, limit=10)
    state["product_contributions"] = [p.model_dump() for p in prod_contribs]

    for p in prod_contribs[:3]:
        state["evidence"].append(
            EvidenceDataPoint(
                metric=f"Product Revenue: {p.product_name}",
                value=f"Delta: ${p.absolute_change} (Units Delta: {p.units_change})",
                period="Comparison",
                source="get_revenue_by_product",
            ).model_dump()
        )
    return state


def analyze_customer_activity_node(state: InvestigationState) -> InvestigationState:
    """Node 5: Measures customer acquisition, active buyer counts, and cohort shifts."""
    db: Session = state["db_session"]
    c_start, c_end = state["resolved_current_start"], state["resolved_current_end"]
    p_start, p_end = state["resolved_previous_start"], state["resolved_previous_end"]

    curr_cust = get_customer_metrics(db, start_date=c_start, end_date=c_end)
    prev_cust = get_customer_metrics(db, start_date=p_start, end_date=p_end)

    c_ord = int(state["order_delta"]["current_value"])
    p_ord = int(state["order_delta"]["previous_value"])

    cust_activity = analyze_customer_activity(curr_cust, prev_cust, current_orders=c_ord, previous_orders=p_ord)
    state["customer_comparison"] = cust_activity.model_dump()

    state["evidence"].append(
        EvidenceDataPoint(
            metric="Customer Cohorts",
            value=f"New: {cust_activity.current_new_customers} (prev {cust_activity.previous_new_customers}), Order delta: {cust_activity.buyer_delta}",
            period="Comparison",
            source="get_customer_metrics",
        ).model_dump()
    )
    return state


def synthesize_investigation_node(state: InvestigationState) -> InvestigationState:
    """Node 6: Synthesizes a factual, evidence-backed diagnostic report."""
    rev_delta = state["revenue_delta"]
    ord_delta = state["order_delta"]
    aov_delta = state["aov_delta"]
    cat_contribs = state["category_contributions"]
    prod_contribs = state["product_contributions"]
    cust_activity = state["customer_comparison"]

    abs_rev = rev_delta["absolute_change"]
    pct_rev = rev_delta["percentage_change"]
    pct_str = f"{pct_rev}%" if pct_rev is not None else "N/A"

    # Identify primary declining category
    declining_cats = [c for c in cat_contribs if c["is_decline"]]
    top_cat_note = ""
    if declining_cats:
        top_cat = declining_cats[0]
        top_cat_note = f" The decline was primarily concentrated in the '{top_cat['category']}' category, which contracted by ${abs(top_cat['absolute_change']):.2f} (accounting for {top_cat['contribution_share']}% of the total variance)."

    # Identify top declining product
    declining_prods = [p for p in prod_contribs if p["is_decline"]]
    top_prod_note = ""
    if declining_prods:
        top_p = declining_prods[0]
        top_prod_note = f" At the SKU level, '{top_p['product_name']}' experienced the largest dollar contraction (-${abs(top_p['absolute_change']):.2f})."

    formatted_abs_rev = f"-${abs(abs_rev):.2f}" if abs_rev < 0 else f"${abs_rev:.2f}"
    ord_val = ord_delta["absolute_change"]
    formatted_ord_change = f"{int(ord_val)}" if isinstance(ord_val, (int, float)) and float(ord_val).is_integer() else f"{ord_val}"
    aov_val = aov_delta["absolute_change"]
    formatted_aov_change = f"-${abs(aov_val):.2f}" if aov_val < 0 else f"${aov_val:.2f}"

    summary_text = (
        f"Revenue shifted from ${rev_delta['previous_value']:.2f} to ${rev_delta['current_value']:.2f}, "
        f"representing an absolute change of {formatted_abs_rev} ({pct_str}). "
        f"Order volume changed by {formatted_ord_change} orders, and Average Order Value shifted by {formatted_aov_change}."
        f"{top_cat_note}{top_prod_note}"
    )

    limitations_text = (
        "Methodological Note on Causation vs Correlation: The identified product and category shifts represent "
        "direct mathematical components of the revenue variance. However, root operational causes (such as website traffic, "
        "advertising spend, external market conditions, or out-of-stock events) are not captured in the transactional order database. "
        "Per corporate governance policy, cancelled and returned orders were excluded from earned revenue calculations."
    )

    report = RevenueDeclineReport(
        summary=summary_text,
        current_period=PeriodSummary(
            start_date=state["resolved_current_start"],
            end_date=state["resolved_current_end"],
            revenue=float(state["current_sales"]["total_revenue"]),
            orders=int(state["current_sales"]["total_orders"]),
            aov=float(state["current_sales"]["aov"]),
        ),
        previous_period=PeriodSummary(
            start_date=state["resolved_previous_start"],
            end_date=state["resolved_previous_end"],
            revenue=float(state["previous_sales"]["total_revenue"]),
            orders=int(state["previous_sales"]["total_orders"]),
            aov=float(state["previous_sales"]["aov"]),
        ),
        revenue_change=MetricDelta(**rev_delta),
        order_change=MetricDelta(**ord_delta),
        aov_change=MetricDelta(**aov_delta),
        category_contributions=[CategoryContribution(**c) for c in cat_contribs],
        product_contributions=[ProductContribution(**p) for p in prod_contribs],
        customer_activity=CustomerActivityComparison(**cust_activity),
        evidence=[EvidenceDataPoint(**e) for e in state["evidence"]],
        limitations=limitations_text,
    )

    state["final_report"] = report.model_dump()
    return state


# -----------------------------------------------------------------------------
# 4. StateGraph Assembly
# -----------------------------------------------------------------------------
def build_investigation_graph() -> StateGraph:
    """Assembles the LangGraph StateGraph for multi-step revenue decline investigation."""
    builder = StateGraph(InvestigationState)

    builder.add_node("resolve_periods", resolve_periods_node)
    builder.add_node("calculate_sales_deltas", calculate_sales_deltas_node)
    builder.add_node("analyze_category_contributions", analyze_category_contributions_node)
    builder.add_node("analyze_product_contributions", analyze_product_contributions_node)
    builder.add_node("analyze_customer_activity", analyze_customer_activity_node)
    builder.add_node("synthesize_investigation", synthesize_investigation_node)

    builder.add_edge(START, "resolve_periods")
    builder.add_edge("resolve_periods", "calculate_sales_deltas")
    builder.add_edge("calculate_sales_deltas", "analyze_category_contributions")
    builder.add_edge("analyze_category_contributions", "analyze_product_contributions")
    builder.add_edge("analyze_product_contributions", "analyze_customer_activity")
    builder.add_edge("analyze_customer_activity", "synthesize_investigation")
    builder.add_edge("synthesize_investigation", END)

    return builder


compiled_investigation_graph = build_investigation_graph().compile()


def investigate_revenue_decline(
    db: Session,
    current_start: Optional[str] = None,
    current_end: Optional[str] = None,
    previous_start: Optional[str] = None,
    previous_end: Optional[str] = None,
) -> RevenueDeclineReport:
    """Executes the complete revenue decline investigation workflow against the active database."""
    initial_state: InvestigationState = {
        "current_start": current_start,
        "current_end": current_end,
        "previous_start": previous_start,
        "previous_end": previous_end,
        "db_session": db,
    }

    final_state = compiled_investigation_graph.invoke(initial_state)
    report_dict = final_state["final_report"]
    return RevenueDeclineReport.model_validate(report_dict)
