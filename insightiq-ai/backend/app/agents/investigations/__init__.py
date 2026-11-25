"""Multi-Step Revenue Decline Investigation Package for InsightIQ AI."""

from __future__ import annotations

from app.agents.investigations.comparison import (
    MetricDelta,
    calculate_metric_delta,
    resolve_comparison_periods,
    safe_percentage_change,
)
from app.agents.investigations.contribution import (
    CategoryContribution,
    CustomerActivityComparison,
    ProductContribution,
    analyze_category_contributions,
    analyze_customer_activity,
    analyze_product_contributions,
)
from app.agents.investigations.revenue_decline import (
    EvidenceDataPoint,
    InvestigationState,
    PeriodSummary,
    RevenueDeclineReport,
    build_investigation_graph,
    compiled_investigation_graph,
    investigate_revenue_decline,
)

__all__ = [
    "PeriodSummary",
    "MetricDelta",
    "EvidenceDataPoint",
    "CategoryContribution",
    "ProductContribution",
    "CustomerActivityComparison",
    "RevenueDeclineReport",
    "InvestigationState",
    "build_investigation_graph",
    "compiled_investigation_graph",
    "investigate_revenue_decline",
    "calculate_metric_delta",
    "resolve_comparison_periods",
    "safe_percentage_change",
    "analyze_category_contributions",
    "analyze_product_contributions",
    "analyze_customer_activity",
]
