"""Controlled Sales Analytics Tools for InsightIQ AI."""

from __future__ import annotations

from typing import Any, Dict, List
from sqlalchemy.orm import Session

from app.services.analytics_service import get_dashboard_summary as svc_dashboard
from app.services.sales_service import (
    get_monthly_revenue as svc_monthly,
    get_revenue_by_category as svc_categories,
    get_revenue_by_product as svc_products,
    get_sales_growth as svc_growth,
    get_sales_metrics as svc_metrics,
)
from app.tools.registry import default_tool_registry
from app.tools.schemas import (
    DashboardSummaryInput,
    MonthlyRevenueInput,
    RevenueByCategoryInput,
    RevenueByProductInput,
    RevenueDeclineInput,
    SalesGrowthInput,
    SalesMetricsInput,
)


@default_tool_registry.register(
    name="get_sales_metrics",
    description="Calculates total revenue, eligible order count, and Average Order Value (AOV) for an optional date range. Excludes cancelled and returned orders per corporate policy.",
    input_schema=SalesMetricsInput,
)
def tool_get_sales_metrics(args: SalesMetricsInput, db: Session) -> Dict[str, Any]:
    return svc_metrics(db=db, start_date=args.start_date, end_date=args.end_date)


@default_tool_registry.register(
    name="get_monthly_revenue",
    description="Calculates monthly revenue trends and order counts aggregated by calendar month (YYYY-MM). Excludes cancelled and returned orders.",
    input_schema=MonthlyRevenueInput,
)
def tool_get_monthly_revenue(args: MonthlyRevenueInput, db: Session) -> List[Dict[str, Any]]:
    return svc_monthly(db=db, start_date=args.start_date, end_date=args.end_date)


@default_tool_registry.register(
    name="get_revenue_by_category",
    description="Aggregates sales revenue and market share percentages by product category (e.g. Electronics, Apparel).",
    input_schema=RevenueByCategoryInput,
)
def tool_get_revenue_by_category(args: RevenueByCategoryInput, db: Session) -> List[Dict[str, Any]]:
    return svc_categories(db=db, start_date=args.start_date, end_date=args.end_date)


@default_tool_registry.register(
    name="get_revenue_by_product",
    description="Ranks top individual product SKUs by gross revenue earned on eligible orders.",
    input_schema=RevenueByProductInput,
)
def tool_get_revenue_by_product(args: RevenueByProductInput, db: Session) -> List[Dict[str, Any]]:
    return svc_products(db=db, limit=args.limit, start_date=args.start_date, end_date=args.end_date)


@default_tool_registry.register(
    name="get_sales_growth",
    description="Calculates the percentage revenue growth and absolute delta between a current time period and a comparative previous period.",
    input_schema=SalesGrowthInput,
)
def tool_get_sales_growth(args: SalesGrowthInput, db: Session) -> Dict[str, Any]:
    return svc_growth(
        db=db,
        current_start=args.current_start,
        current_end=args.current_end,
        previous_start=args.previous_start,
        previous_end=args.previous_end,
    )


@default_tool_registry.register(
    name="get_dashboard_summary",
    description="Retrieves a consolidated high-level executive summary including overall sales KPIs, monthly trends, category breakdown, top products, and customer cohorts.",
    input_schema=DashboardSummaryInput,
)
def tool_get_dashboard_summary(args: DashboardSummaryInput, db: Session) -> Dict[str, Any]:
    return svc_dashboard(db=db, start_date=args.start_date, end_date=args.end_date)


@default_tool_registry.register(
    name="investigate_revenue_decline",
    description="Executes a multi-step diagnostic investigation of revenue change between two periods, analyzing category waterfall, product SKU drivers, customer cohort shifts, and data limitations.",
    input_schema=RevenueDeclineInput,
)
def tool_investigate_revenue_decline(args: RevenueDeclineInput, db: Session) -> Dict[str, Any]:
    from app.agents.investigations import investigate_revenue_decline
    report = investigate_revenue_decline(
        db=db,
        current_start=args.current_start,
        current_end=args.current_end,
        previous_start=args.previous_start,
        previous_end=args.previous_end,
    )
    return report.model_dump()


@default_tool_registry.register(
    name="detect_anomalies",
    description="Scans database metrics for statistical outliers, sharp revenue drops/surges, order volume collapses, and category/product contractions.",
    input_schema=SalesMetricsInput,
)
def tool_detect_anomalies(args: SalesMetricsInput, db: Session) -> List[Dict[str, Any]]:
    from app.services.anomaly_service import scan_all_anomalies
    anomalies = scan_all_anomalies(db=db, start_date=args.start_date, end_date=args.end_date)
    return [a.model_dump() for a in anomalies]


@default_tool_registry.register(
    name="generate_insights",
    description="Generates concise, evidence-backed business insights distinguishing factual observations from actionable executive recommendations.",
    input_schema=SalesMetricsInput,
)
def tool_generate_insights(args: SalesMetricsInput, db: Session) -> List[Dict[str, Any]]:
    from app.services.insight_service import generate_executive_insights
    insights = generate_executive_insights(db=db, start_date=args.start_date, end_date=args.end_date)
    return [i.model_dump() for i in insights]
