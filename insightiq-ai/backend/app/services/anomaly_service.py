"""Statistical and Threshold-Based Anomaly Detection Service for Retail Business Intelligence."""

from __future__ import annotations

import math
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.logging_config import get_logger
from app.services.product_service import get_highest_revenue_products
from app.services.sales_service import (
    get_monthly_revenue,
    get_revenue_by_category,
)

logger = get_logger("insightiq.services.anomaly")


# -----------------------------------------------------------------------------
# 1. Anomaly Enums and Data Models
# -----------------------------------------------------------------------------
class AnomalyType(str, Enum):
    """Categorization of detected business anomalies."""
    REVENUE_DROP = "revenue_drop"
    REVENUE_SURGE = "revenue_surge"
    ORDER_DROP = "order_drop"
    ORDER_SURGE = "order_surge"
    CATEGORY_CONTRACTION = "category_contraction"
    PRODUCT_DROP = "product_drop"
    ZERO_SALES_OUTLIER = "zero_sales_outlier"


class AnomalySeverity(str, Enum):
    """Business impact priority levels."""
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class EvidenceLevel(str, Enum):
    """Deterministic, mathematically defined indicator of evidence backing an anomaly."""
    DIRECT_DATABASE_METRIC = "DIRECT_DATABASE_METRIC"  # Verified raw database aggregation
    THRESHOLD_BREACH = "THRESHOLD_BREACH"              # Breached documented business rule threshold
    STATISTICAL_VARIANCE = "STATISTICAL_VARIANCE"      # Outside 2.0+ standard deviations (Z-score)


class DetectedAnomaly(BaseModel):
    """Structured representation of an identified business anomaly."""
    anomaly_id: str = Field(..., description="Unique deterministic identifier for the anomaly")
    anomaly_type: AnomalyType = Field(..., description="Nature of the variance")
    title: str = Field(..., description="Concise anomaly title")
    metric_name: str = Field(..., description="Affected business metric (e.g. Revenue, Order Count)")
    current_value: float = Field(..., description="Actual value observed in the evaluation period")
    baseline_value: float = Field(..., description="Reference value in the preceding baseline period")
    absolute_change: float = Field(..., description="Absolute dollar or count variance (current - baseline)")
    percentage_change: Optional[float] = Field(None, description="Percentage variance relative to baseline")
    z_score: Optional[float] = Field(None, description="Statistical Z-score across series if N >= 3")
    severity: AnomalySeverity = Field(..., description="Impact severity classification")
    evidence_level: EvidenceLevel = Field(..., description="Defined methodology backing the detection")
    explanation: str = Field(..., description="Human-readable explanation citing exact figures")
    entity: Optional[str] = Field(None, description="Category name, product SKU, or timeframe entity")
    time_period: str = Field(..., description="Time period during which the anomaly manifested")


# -----------------------------------------------------------------------------
# 2. Statistical Helper Functions
# -----------------------------------------------------------------------------
def calculate_z_scores(values: List[float]) -> List[Optional[float]]:
    """Computes Z-scores for a numerical series if length >= 3."""
    n = len(values)
    if n < 3:
        return [None] * n

    mean = sum(values) / n
    variance = sum((x - mean) ** 2 for x in values) / (n - 1)
    std = math.sqrt(variance)

    if std == 0.0:
        return [0.0] * n

    return [round((x - mean) / std, 2) for x in values]


# -----------------------------------------------------------------------------
# 3. Domain Detection Functions
# -----------------------------------------------------------------------------
def detect_monthly_revenue_anomalies(
    monthly_data: List[Dict[str, Any]],
    drop_threshold_pct: float = 20.0,
    surge_threshold_pct: float = 30.0,
) -> List[DetectedAnomaly]:
    """Scans monthly revenue sequence for large MoM contractions or surges."""
    anomalies: List[DetectedAnomaly] = []
    if len(monthly_data) < 2:
        return anomalies

    revenues = [float(m["revenue"]) for m in monthly_data]
    z_scores = calculate_z_scores(revenues)

    for i in range(1, len(monthly_data)):
        curr_m = monthly_data[i]
        prev_m = monthly_data[i - 1]

        c_rev = float(curr_m["revenue"])
        p_rev = float(prev_m["revenue"])
        abs_change = round(c_rev - p_rev, 2)
        month_label = curr_m["month"]
        z = z_scores[i]

        if p_rev > 0:
            pct_change = round(((c_rev - p_rev) / p_rev) * 100.0, 2)
        else:
            pct_change = 100.0 if c_rev > 0 else 0.0

        # Contraction check
        if pct_change <= -drop_threshold_pct:
            sev = AnomalySeverity.CRITICAL if pct_change <= -50.0 else AnomalySeverity.HIGH
            ev_level = EvidenceLevel.STATISTICAL_VARIANCE if (z is not None and z <= -1.5) else EvidenceLevel.THRESHOLD_BREACH

            anomalies.append(
                DetectedAnomaly(
                    anomaly_id=f"rev_drop_{month_label}",
                    anomaly_type=AnomalyType.REVENUE_DROP,
                    title=f"Severe Revenue Contraction in {month_label}",
                    metric_name="Monthly Revenue",
                    current_value=c_rev,
                    baseline_value=p_rev,
                    absolute_change=abs_change,
                    percentage_change=pct_change,
                    z_score=z,
                    severity=sev,
                    evidence_level=ev_level,
                    explanation=(
                        f"Monthly revenue in {month_label} dropped by ${abs(abs_change):.2f} "
                        f"({pct_change}%) compared to ${p_rev:.2f} in {prev_m['month']}."
                    ),
                    entity=month_label,
                    time_period=month_label,
                )
            )

        # Surge check
        elif pct_change >= surge_threshold_pct:
            anomalies.append(
                DetectedAnomaly(
                    anomaly_id=f"rev_surge_{month_label}",
                    anomaly_type=AnomalyType.REVENUE_SURGE,
                    title=f"Significant Revenue Growth in {month_label}",
                    metric_name="Monthly Revenue",
                    current_value=c_rev,
                    baseline_value=p_rev,
                    absolute_change=abs_change,
                    percentage_change=pct_change,
                    z_score=z,
                    severity=AnomalySeverity.MEDIUM,
                    evidence_level=EvidenceLevel.THRESHOLD_BREACH,
                    explanation=(
                        f"Monthly revenue surged by ${abs_change:.2f} (+{pct_change}%) "
                        f"reaching ${c_rev:.2f} in {month_label}."
                    ),
                    entity=month_label,
                    time_period=month_label,
                )
            )

    return anomalies


def detect_order_volume_anomalies(
    monthly_data: List[Dict[str, Any]],
    drop_threshold_pct: float = 25.0,
) -> List[DetectedAnomaly]:
    """Identifies sharp drops in completed transaction order volumes."""
    anomalies: List[DetectedAnomaly] = []
    if len(monthly_data) < 2:
        return anomalies

    order_counts = [float(m["order_count"]) for m in monthly_data]
    z_scores = calculate_z_scores(order_counts)

    for i in range(1, len(monthly_data)):
        curr_m = monthly_data[i]
        prev_m = monthly_data[i - 1]

        c_ord = int(curr_m["order_count"])
        p_ord = int(prev_m["order_count"])
        abs_change = c_ord - p_ord
        month_label = curr_m["month"]
        z = z_scores[i]

        if p_ord > 0:
            pct_change = round(((c_ord - p_ord) / p_ord) * 100.0, 2)
        else:
            pct_change = 100.0 if c_ord > 0 else 0.0

        if pct_change <= -drop_threshold_pct:
            sev = AnomalySeverity.CRITICAL if pct_change <= -50.0 else AnomalySeverity.HIGH
            anomalies.append(
                DetectedAnomaly(
                    anomaly_id=f"ord_drop_{month_label}",
                    anomaly_type=AnomalyType.ORDER_DROP,
                    title=f"Order Volume Decline in {month_label}",
                    metric_name="Order Count",
                    current_value=float(c_ord),
                    baseline_value=float(p_ord),
                    absolute_change=float(abs_change),
                    percentage_change=pct_change,
                    z_score=z,
                    severity=sev,
                    evidence_level=EvidenceLevel.THRESHOLD_BREACH,
                    explanation=(
                        f"Eligible order volume contracted from {p_ord} to {c_ord} "
                        f"orders in {month_label} ({pct_change}% change)."
                    ),
                    entity=month_label,
                    time_period=month_label,
                )
            )

    return anomalies


def detect_category_anomalies(
    current_categories: List[Dict[str, Any]],
    previous_categories: List[Dict[str, Any]],
    time_period_label: str = "Comparison Window",
    contraction_threshold_pct: float = 25.0,
) -> List[DetectedAnomaly]:
    """Identifies categories experiencing severe revenue drops or complete disappearance."""
    anomalies: List[DetectedAnomaly] = []
    curr_map = {c["category"]: float(c["revenue"]) for c in current_categories}
    prev_map = {c["category"]: float(c["revenue"]) for c in previous_categories}

    for cat, prev_rev in prev_map.items():
        curr_rev = curr_map.get(cat, 0.0)
        abs_change = round(curr_rev - prev_rev, 2)

        if prev_rev > 0:
            pct_change = round(((curr_rev - prev_rev) / prev_rev) * 100.0, 2)
        else:
            pct_change = 0.0

        if pct_change <= -contraction_threshold_pct:
            sev = AnomalySeverity.CRITICAL if curr_rev == 0.0 else AnomalySeverity.HIGH
            anomalies.append(
                DetectedAnomaly(
                    anomaly_id=f"cat_drop_{cat}",
                    anomaly_type=AnomalyType.CATEGORY_CONTRACTION,
                    title=f"Category Revenue Drop: {cat}",
                    metric_name=f"{cat} Revenue",
                    current_value=curr_rev,
                    baseline_value=prev_rev,
                    absolute_change=abs_change,
                    percentage_change=pct_change,
                    z_score=None,
                    severity=sev,
                    evidence_level=EvidenceLevel.THRESHOLD_BREACH,
                    explanation=(
                        f"Category '{cat}' revenue declined by ${abs(abs_change):.2f} "
                        f"({pct_change}%) from ${prev_rev:.2f} to ${curr_rev:.2f}."
                    ),
                    entity=cat,
                    time_period=time_period_label,
                )
            )

    return anomalies


def detect_product_anomalies(
    current_products: List[Dict[str, Any]],
    previous_products: List[Dict[str, Any]],
    time_period_label: str = "Comparison Window",
    drop_threshold_pct: float = 30.0,
) -> List[DetectedAnomaly]:
    """Identifies products whose sales collapsed or dropped to zero."""
    anomalies: List[DetectedAnomaly] = []
    curr_map = {p["product_id"]: p for p in current_products}
    prev_map = {p["product_id"]: p for p in previous_products}

    for pid, prev_p in prev_map.items():
        p_rev = float(prev_p.get("revenue", 0.0))
        p_name = prev_p.get("product_name", f"Product #{pid}")
        curr_p = curr_map.get(pid, {})
        c_rev = float(curr_p.get("revenue", 0.0))
        abs_change = round(c_rev - p_rev, 2)

        # Significant baseline product with zero sales in current
        if p_rev >= 100.0 and c_rev == 0.0:
            anomalies.append(
                DetectedAnomaly(
                    anomaly_id=f"prod_zero_{pid}",
                    anomaly_type=AnomalyType.ZERO_SALES_OUTLIER,
                    title=f"Zero Sales Collapse: {p_name}",
                    metric_name=f"{p_name} Revenue",
                    current_value=0.0,
                    baseline_value=p_rev,
                    absolute_change=abs_change,
                    percentage_change=-100.0,
                    z_score=None,
                    severity=AnomalySeverity.HIGH,
                    evidence_level=EvidenceLevel.DIRECT_DATABASE_METRIC,
                    explanation=(
                        f"'{p_name}' generated $0.00 revenue after achieving "
                        f"${p_rev:.2f} in the previous period."
                    ),
                    entity=p_name,
                    time_period=time_period_label,
                )
            )
        elif p_rev > 0:
            pct_change = round(((c_rev - p_rev) / p_rev) * 100.0, 2)
            if pct_change <= -drop_threshold_pct and abs_change <= -100.0:
                anomalies.append(
                    DetectedAnomaly(
                        anomaly_id=f"prod_drop_{pid}",
                        anomaly_type=AnomalyType.PRODUCT_DROP,
                        title=f"Significant SKU Drop: {p_name}",
                        metric_name=f"{p_name} Revenue",
                        current_value=c_rev,
                        baseline_value=p_rev,
                        absolute_change=abs_change,
                        percentage_change=pct_change,
                        z_score=None,
                        severity=AnomalySeverity.MEDIUM,
                        evidence_level=EvidenceLevel.THRESHOLD_BREACH,
                        explanation=f"'{p_name}' revenue dropped by ${abs(abs_change):.2f} ({pct_change}%).",
                        entity=p_name,
                        time_period=time_period_label,
                    )
                )

    return anomalies


def scan_all_anomalies(
    db: Session,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> List[DetectedAnomaly]:
    """Comprehensive multi-dimensional anomaly audit across monthly trends, categories, and products."""
    logger.info("Scanning for business anomalies between [%s] and [%s]", start_date, end_date)
    all_anomalies: List[DetectedAnomaly] = []

    # 1. Monthly revenue and order volume anomalies
    monthly = get_monthly_revenue(db, start_date=start_date, end_date=end_date)
    all_anomalies.extend(detect_monthly_revenue_anomalies(monthly))
    all_anomalies.extend(detect_order_volume_anomalies(monthly))

    # 2. Sequential period category and product anomalies if >= 2 months available
    if len(monthly) >= 2:
        m_curr = monthly[-1]["month"]
        m_prev = monthly[-2]["month"]
        # Approximate bounds for each month
        curr_start = f"{m_curr}-01"
        prev_start = f"{m_prev}-01"

        c_cats = get_revenue_by_category(db, start_date=curr_start)
        p_cats = get_revenue_by_category(db, start_date=prev_start, end_date=curr_start)
        all_anomalies.extend(detect_category_anomalies(c_cats, p_cats, time_period_label=f"{m_curr} vs {m_prev}"))

        c_prods = get_highest_revenue_products(db, limit=30, start_date=curr_start)
        p_prods = get_highest_revenue_products(db, limit=30, start_date=prev_start, end_date=curr_start)
        all_anomalies.extend(detect_product_anomalies(c_prods, p_prods, time_period_label=f"{m_curr} vs {m_prev}"))

    # Sort anomalies: CRITICAL first, then HIGH, MEDIUM, LOW
    severity_order = {
        AnomalySeverity.CRITICAL: 0,
        AnomalySeverity.HIGH: 1,
        AnomalySeverity.MEDIUM: 2,
        AnomalySeverity.LOW: 3,
        AnomalySeverity.INFO: 4,
    }
    all_anomalies.sort(key=lambda a: severity_order.get(a.severity, 99))
    logger.info("Anomaly scan complete. Found %d anomalies.", len(all_anomalies))
    return all_anomalies
