"""Unit and Integration Tests for Anomaly Detection and Business Insights Services."""

import pytest
from app.services.anomaly_service import (
    AnomalySeverity,
    AnomalyType,
    DetectedAnomaly,
    EvidenceLevel,
    calculate_z_scores,
    detect_category_anomalies,
    detect_monthly_revenue_anomalies,
    detect_order_volume_anomalies,
    detect_product_anomalies,
    scan_all_anomalies,
)
from app.services.insight_service import (
    BusinessInsight,
    generate_executive_insights,
)
from app.tools.registry import default_tool_registry


# -----------------------------------------------------------------------------
# 1. Statistical Outlier & Z-Score Tests
# -----------------------------------------------------------------------------
def test_calculate_z_scores_insufficient_samples():
    """Series with fewer than 3 samples must return None for Z-scores."""
    assert calculate_z_scores([]) == []
    assert calculate_z_scores([100.0, 200.0]) == [None, None]


def test_calculate_z_scores_zero_variance():
    """Series with identical values must return 0.0 Z-scores without division by zero."""
    res = calculate_z_scores([500.0, 500.0, 500.0])
    assert res == [0.0, 0.0, 0.0]


def test_calculate_z_scores_valid_series():
    """Series with variance produces expected positive and negative Z-scores."""
    series = [100.0, 100.0, 400.0]  # Mean: 200, Std: 173.2
    scores = calculate_z_scores(series)
    assert len(scores) == 3
    assert scores[0] < 0  # Below mean
    assert scores[2] > 1.0  # Above mean


# -----------------------------------------------------------------------------
# 2. Monthly Revenue & Order Volume Anomaly Detection Tests
# -----------------------------------------------------------------------------
def test_detect_monthly_revenue_severe_contraction():
    """Detects > 50% month-over-month revenue collapse as CRITICAL severity."""
    monthly_data = [
        {"month": "2024-01", "revenue": 1220.00, "order_count": 2},
        {"month": "2024-02", "revenue": 1210.00, "order_count": 2},
        {"month": "2024-03", "revenue": 60.00, "order_count": 1},  # -95.04% collapse
    ]
    anomalies = detect_monthly_revenue_anomalies(monthly_data)
    assert len(anomalies) == 1
    anom = anomalies[0]
    assert anom.anomaly_type == AnomalyType.REVENUE_DROP
    assert anom.severity == AnomalySeverity.CRITICAL
    assert anom.percentage_change == -95.04
    assert anom.time_period == "2024-03"
    assert anom.evidence_level in (EvidenceLevel.STATISTICAL_VARIANCE, EvidenceLevel.THRESHOLD_BREACH)


def test_detect_monthly_revenue_surge():
    """Detects > 30% month-over-month revenue increase as a positive surge."""
    monthly_data = [
        {"month": "2024-01", "revenue": 1000.00, "order_count": 5},
        {"month": "2024-02", "revenue": 1600.00, "order_count": 8},  # +60% surge
    ]
    anomalies = detect_monthly_revenue_anomalies(monthly_data)
    assert len(anomalies) == 1
    assert anomalies[0].anomaly_type == AnomalyType.REVENUE_SURGE
    assert anomalies[0].percentage_change == 60.0


def test_detect_order_volume_anomalies():
    """Detects sharp drop in completed transaction order volumes."""
    monthly_data = [
        {"month": "2024-01", "revenue": 1000.00, "order_count": 10},
        {"month": "2024-02", "revenue": 950.00, "order_count": 4},  # -60% orders drop
    ]
    anomalies = detect_order_volume_anomalies(monthly_data)
    assert len(anomalies) == 1
    assert anomalies[0].anomaly_type == AnomalyType.ORDER_DROP
    assert anomalies[0].current_value == 4.0
    assert anomalies[0].baseline_value == 10.0


# -----------------------------------------------------------------------------
# 3. Category & Product Anomaly Detection Tests
# -----------------------------------------------------------------------------
def test_detect_category_collapse_to_zero():
    """Detects category revenue dropping to zero as CRITICAL anomaly."""
    curr_cats = [{"category": "Apparel", "revenue": 60.00}]
    prev_cats = [
        {"category": "Electronics", "revenue": 1050.00},
        {"category": "Apparel", "revenue": 160.00},
    ]
    anomalies = detect_category_anomalies(curr_cats, prev_cats)
    assert len(anomalies) >= 1
    elec_anom = next(a for a in anomalies if a.entity == "Electronics")
    assert elec_anom.anomaly_type == AnomalyType.CATEGORY_CONTRACTION
    assert elec_anom.severity == AnomalySeverity.CRITICAL
    assert elec_anom.current_value == 0.0
    assert elec_anom.percentage_change == -100.0


def test_detect_product_zero_sales_outlier():
    """Flags high-revenue SKU that collapsed to zero sales."""
    curr_prods = [{"product_id": 4, "product_name": "Cap", "revenue": 60.0}]
    prev_prods = [
        {"product_id": 1, "product_name": "Pro Laptop 15", "revenue": 1000.0},
        {"product_id": 4, "product_name": "Cap", "revenue": 40.0},
    ]
    anomalies = detect_product_anomalies(curr_prods, prev_prods)
    assert len(anomalies) == 1
    assert anomalies[0].anomaly_type == AnomalyType.ZERO_SALES_OUTLIER
    assert anomalies[0].entity == "Pro Laptop 15"
    assert anomalies[0].current_value == 0.0


# -----------------------------------------------------------------------------
# 4. End-to-End Anomaly Scan against Ground Truth Database
# -----------------------------------------------------------------------------
def test_scan_all_anomalies_finds_march_drop(seeded_db_session):
    """Executes multi-dimensional scan over deterministic dataset identifying March drop."""
    anomalies = scan_all_anomalies(seeded_db_session, start_date="2024-01-01", end_date="2024-03-31")
    assert len(anomalies) >= 2

    # Verify March revenue drop is present
    types = [a.anomaly_type for a in anomalies]
    assert AnomalyType.REVENUE_DROP in types
    assert AnomalyType.ORDER_DROP in types

    top_anom = anomalies[0]
    assert top_anom.severity in (AnomalySeverity.CRITICAL, AnomalySeverity.HIGH)
    assert top_anom.current_value < top_anom.baseline_value


# -----------------------------------------------------------------------------
# 5. Executive Insights Service & Evidence Grounding Tests
# -----------------------------------------------------------------------------
def test_generate_executive_insights(seeded_db_session):
    """Verifies insight generation produces strictly grounded observations and separated recommendations."""
    insights = generate_executive_insights(
        seeded_db_session, start_date="2024-01-01", end_date="2024-03-31"
    )
    assert len(insights) >= 3

    for insight in insights:
        assert isinstance(insight, BusinessInsight)
        assert len(insight.title) > 3
        assert len(insight.description) > 10
        # Factual observation MUST be present and distinct
        assert len(insight.observation) > 5
        # Recommendation must be distinct from observation if present
        if insight.recommendation:
            assert insight.recommendation != insight.observation
        # Grounding metrics and evidence must be populated
        assert insight.actual_value is not None
        assert len(insight.evidence) > 5
        assert insight.evidence_level in [e.value for e in EvidenceLevel]
        assert insight.severity in ("info", "positive", "warning", "critical")

    # Verify Category Concentration insight exists
    titles = [i.title for i in insights]
    assert any("Category Concentration" in t for t in titles)
    assert any("Customer Retention" in t for t in titles)


# -----------------------------------------------------------------------------
# 6. Tool Registry Invocation Tests
# -----------------------------------------------------------------------------
def test_tool_detect_anomalies(seeded_db_session):
    """Tests detect_anomalies registered tool execution."""
    res = default_tool_registry.execute_tool(
        "detect_anomalies", {"start_date": "2024-01-01", "end_date": "2024-03-31"}, db=seeded_db_session
    )
    assert res.success is True
    assert isinstance(res.data, list)
    assert len(res.data) >= 1
    assert "anomaly_type" in res.data[0]


def test_tool_generate_insights(seeded_db_session):
    """Tests generate_insights registered tool execution."""
    res = default_tool_registry.execute_tool(
        "generate_insights", {"start_date": "2024-01-01", "end_date": "2024-03-31"}, db=seeded_db_session
    )
    assert res.success is True
    assert isinstance(res.data, list)
    assert len(res.data) >= 3
    assert "observation" in res.data[0]
    assert "recommendation" in res.data[0]
