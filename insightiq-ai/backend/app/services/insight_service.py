"""Evidence-Backed Business Insights Generation Service for InsightIQ AI."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.logging_config import get_logger
from app.services.anomaly_service import (
    AnomalySeverity,
    DetectedAnomaly,
    EvidenceLevel,
    scan_all_anomalies,
)
from app.services.customer_service import get_customer_metrics
from app.services.product_service import get_top_selling_products
from app.services.sales_service import (
    get_monthly_revenue,
    get_revenue_by_category,
    get_sales_metrics,
)

logger = get_logger("insightiq.services.insights")


# -----------------------------------------------------------------------------
# 1. Structured Insight Model
# -----------------------------------------------------------------------------
class BusinessInsight(BaseModel):
    """Structured executive business intelligence insight with strict evidence grounding."""
    insight_id: str = Field(..., description="Unique deterministic identifier")
    title: str = Field(..., description="Concise insight title")
    description: str = Field(..., description="Executive narrative synthesis")
    observation: str = Field(
        ..., description="Factual, verifiable statement of what occurred in the database metrics"
    )
    recommendation: Optional[str] = Field(
        None, description="Actionable executive recommendation, separated from factual observation"
    )
    metric: str = Field(..., description="Primary metric under consideration")
    actual_value: Union[float, int, str] = Field(..., description="Deterministic calculated value")
    comparison_value: Optional[Union[float, int, str]] = Field(
        None, description="Comparative baseline or historical benchmark value"
    )
    evidence: str = Field(..., description="Audit statement linking insight to exact data source")
    severity: str = Field(
        default="info", description="Priority level: info, positive, warning, or critical"
    )
    evidence_level: str = Field(
        default=EvidenceLevel.DIRECT_DATABASE_METRIC.value,
        description="Defined methodology: DIRECT_DATABASE_METRIC, THRESHOLD_BREACH, or STATISTICAL_VARIANCE",
    )


# -----------------------------------------------------------------------------
# 2. Insight Generation Engine
# -----------------------------------------------------------------------------
def _map_severity_to_str(sev: AnomalySeverity) -> str:
    """Translates internal AnomalySeverity to standardized insight severity string."""
    if sev in (AnomalySeverity.CRITICAL,):
        return "critical"
    elif sev in (AnomalySeverity.HIGH,):
        return "warning"
    elif sev in (AnomalySeverity.MEDIUM,):
        return "warning"
    return "info"


def generate_executive_insights(
    db: Session,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> List[BusinessInsight]:
    """Generates a comprehensive suite of grounded insights combining anomalies, sales, categories, and customers."""
    logger.info("Generating executive insights for [%s to %s]", start_date, end_date)
    insights: List[BusinessInsight] = []

    # 1. Execute deterministic database aggregations
    sales_kpis = get_sales_metrics(db, start_date=start_date, end_date=end_date)
    monthly_data = get_monthly_revenue(db, start_date=start_date, end_date=end_date)
    category_data = get_revenue_by_category(db, start_date=start_date, end_date=end_date)
    customer_kpis = get_customer_metrics(db, start_date=start_date, end_date=end_date)
    top_products = get_top_selling_products(db, limit=5, start_date=start_date, end_date=end_date)

    tot_rev = float(sales_kpis["total_revenue"])
    tot_ord = int(sales_kpis["total_orders"])
    aov = float(sales_kpis["aov"])

    # 2. Ingest & Transform Detected Anomalies into High-Priority Insights
    anomalies: List[DetectedAnomaly] = scan_all_anomalies(db, start_date=start_date, end_date=end_date)
    for idx, anom in enumerate(anomalies[:4]):  # Surface top anomalies
        rec: Optional[str] = None
        if "revenue" in anom.anomaly_type.value:
            rec = "Investigate supply chain fulfillment and launch targeted customer re-engagement incentives."
        elif "order" in anom.anomaly_type.value:
            rec = "Audit top marketing conversion funnels and checkout friction points."
        elif "zero_sales" in anom.anomaly_type.value:
            rec = f"Review catalog availability, inventory stockouts, or pricing changes for {anom.entity}."

        insights.append(
            BusinessInsight(
                insight_id=f"anomaly_insight_{idx + 1}",
                title=anom.title,
                description=anom.explanation,
                observation=f"Observed {anom.metric_name} of {anom.current_value} vs baseline {anom.baseline_value} (delta: {anom.absolute_change}).",
                recommendation=rec,
                metric=anom.metric_name,
                actual_value=anom.current_value,
                comparison_value=anom.baseline_value,
                evidence=f"Detected via {anom.evidence_level.value} on {anom.time_period}.",
                severity=_map_severity_to_str(anom.severity),
                evidence_level=anom.evidence_level.value,
            )
        )

    # 3. Overall Sales Performance Insight
    if tot_ord > 0:
        insights.append(
            BusinessInsight(
                insight_id="sales_performance_kpi",
                title="Cumulative Revenue Performance",
                description=f"Generated ${tot_rev:,.2f} across {tot_ord} eligible completed and pending transactions.",
                observation=f"Average Order Value stands at ${aov:.2f} across {tot_ord} orders.",
                recommendation="Focus marketing on high-AOV bundles to maximize transaction revenue yields." if aov > 0 else None,
                metric="Total Revenue",
                actual_value=tot_rev,
                comparison_value=None,
                evidence="Calculated via get_sales_metrics excluding cancelled and returned orders.",
                severity="positive" if tot_rev > 0 else "info",
                evidence_level=EvidenceLevel.DIRECT_DATABASE_METRIC.value,
            )
        )

    # 4. Category Market Share & Concentration Insight
    if category_data:
        top_cat = category_data[0]
        cat_share = float(top_cat.get("percentage_of_total", 0.0))
        cat_rev = float(top_cat.get("revenue", 0.0))
        cat_name = top_cat.get("category", "Unknown")

        concentration_risk = cat_share >= 60.0
        insights.append(
            BusinessInsight(
                insight_id="category_concentration_kpi",
                title=f"Category Concentration: {cat_name}",
                description=f"'{cat_name}' represents the largest revenue driver, generating ${cat_rev:,.2f} ({cat_share}% of sales).",
                observation=f"The top category accounts for {cat_share}% of total sales volume.",
                recommendation="Diversify marketing and product expansion across secondary categories to reduce portfolio concentration risk." if concentration_risk else "Maintain promotional momentum in primary category.",
                metric=f"{cat_name} Revenue Share",
                actual_value=f"{cat_share}%",
                comparison_value=None,
                evidence="Calculated via get_revenue_by_category.",
                severity="warning" if concentration_risk else "info",
                evidence_level=EvidenceLevel.DIRECT_DATABASE_METRIC.value,
            )
        )

    # 5. Customer Retention & Churn Insight
    tot_cust = int(customer_kpis.get("total_customers", 0))
    repeat_cust = int(customer_kpis.get("repeat_customers", 0))
    inactive_cust = int(customer_kpis.get("inactive_customers", 0))

    if tot_cust > 0:
        repeat_rate = round((repeat_cust / tot_cust) * 100.0, 1)
        insights.append(
            BusinessInsight(
                insight_id="customer_cohort_retention",
                title="Customer Retention & Activity",
                description=f"Registered base of {tot_cust} customers includes {repeat_cust} repeat buyers ({repeat_rate}% repeat rate) and {inactive_cust} inactive accounts.",
                observation=f"Repeat buyer rate is {repeat_rate}% ({repeat_cust}/{tot_cust}); {inactive_cust} accounts are inactive.",
                recommendation="Deploy automated win-back email sequences targeting inactive customer segments." if inactive_cust > 0 else "Nurture repeat buyer loyalty programs.",
                metric="Repeat Customer Rate",
                actual_value=f"{repeat_rate}%",
                comparison_value=f"{tot_cust} total customers",
                evidence="Calculated via get_customer_metrics.",
                severity="warning" if inactive_cust > repeat_cust else "info",
                evidence_level=EvidenceLevel.DIRECT_DATABASE_METRIC.value,
            )
        )

    # 6. Product SKU Leadership Insight
    if top_products:
        lead_p = top_products[0]
        p_name = lead_p.get("product_name")
        p_units = int(lead_p.get("units_sold", 0))
        p_rev = float(lead_p.get("revenue", 0.0))

        insights.append(
            BusinessInsight(
                insight_id="product_leadership_sku",
                title=f"Leading Product SKU: {p_name}",
                description=f"'{p_name}' leads unit sales with {p_units} units sold, generating ${p_rev:,.2f}.",
                observation=f"Top selling product '{p_name}' accounts for {p_units} units and ${p_rev:.2f} revenue.",
                recommendation=f"Ensure optimal supplier lead times and warehouse stock for '{p_name}' to prevent stockouts.",
                metric=f"{p_name} Units Sold",
                actual_value=p_units,
                comparison_value=None,
                evidence="Calculated via get_top_selling_products.",
                severity="info",
                evidence_level=EvidenceLevel.DIRECT_DATABASE_METRIC.value,
            )
        )

    logger.info("Generated %d grounded business insights.", len(insights))
    return insights
