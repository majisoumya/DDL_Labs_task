"""Tests for Multi-Step Revenue Decline Investigation Graph and Variance Decomposition."""

from decimal import Decimal
import pytest
from app.agents.investigations import (
    CategoryContribution,
    CustomerActivityComparison,
    MetricDelta,
    ProductContribution,
    RevenueDeclineReport,
    analyze_category_contributions,
    analyze_customer_activity,
    analyze_product_contributions,
    calculate_metric_delta,
    investigate_revenue_decline,
    resolve_comparison_periods,
    safe_percentage_change,
)
from app.tools.registry import default_tool_registry


# -----------------------------------------------------------------------------
# 1. Period Resolution Unit Tests
# -----------------------------------------------------------------------------
def test_resolve_comparison_periods_full_month():
    """Verifies that full month period shifts back exactly one calendar month."""
    c_start, c_end, p_start, p_end = resolve_comparison_periods(
        current_start="2024-03-01",
        current_end="2024-03-31",
    )
    assert c_start == "2024-03-01"
    assert c_end == "2024-03-31"
    assert p_start == "2024-02-01"
    assert p_end == "2024-02-29"  # 2024 is a leap year!


def test_resolve_comparison_periods_explicit():
    """Verifies explicit prior dates are respected."""
    c_start, c_end, p_start, p_end = resolve_comparison_periods(
        current_start="2024-03-15",
        current_end="2024-03-31",
        previous_start="2024-03-01",
        previous_end="2024-03-14",
    )
    assert c_start == "2024-03-15"
    assert p_start == "2024-03-01"
    assert p_end == "2024-03-14"


def test_resolve_comparison_periods_partial_window():
    """Verifies arbitrary window shifts back by duration in days."""
    # 10 days: 2024-01-11 to 2024-01-20
    c_start, c_end, p_start, p_end = resolve_comparison_periods(
        current_start="2024-01-11",
        current_end="2024-01-20",
    )
    assert p_start == "2024-01-01"
    assert p_end == "2024-01-10"


# -----------------------------------------------------------------------------
# 2. Metric Delta & Safe Math Tests
# -----------------------------------------------------------------------------
def test_safe_percentage_change_normal():
    assert safe_percentage_change(120.0, 100.0) == 20.0
    assert safe_percentage_change(80.0, 100.0) == -20.0


def test_safe_percentage_change_zero_division():
    # Both zero -> 0.0
    assert safe_percentage_change(0.0, 0.0) == 0.0
    # From 0 to positive -> 100.0%
    assert safe_percentage_change(50.0, 0.0) == 100.0
    # From 0 to negative -> -100.0%
    assert safe_percentage_change(-50.0, 0.0) == -100.0


def test_calculate_metric_delta():
    delta = calculate_metric_delta(current_value=60.0, previous_value=1210.0)
    assert delta.current_value == 60.0
    assert delta.previous_value == 1210.0
    assert delta.absolute_change == -1150.0
    assert delta.percentage_change == -95.04
    assert delta.is_decline is True


# -----------------------------------------------------------------------------
# 3. Category & Product Contribution Analysis Tests
# -----------------------------------------------------------------------------
def test_analyze_category_contributions_waterfall():
    """Verifies category waterfall calculation and contribution share."""
    current_cats = [{"category": "Apparel", "revenue": 60.00}]
    previous_cats = [
        {"category": "Electronics", "revenue": 1050.00},
        {"category": "Apparel", "revenue": 160.00},
    ]
    total_delta = -1150.00

    contribs = analyze_category_contributions(current_cats, previous_cats, total_revenue_delta=total_delta)
    assert len(contribs) == 2

    # Electronics dropped from 1050 to 0 (-1050 drop)
    elec = next(c for c in contribs if c.category == "Electronics")
    assert elec.current_revenue == 0.0
    assert elec.previous_revenue == 1050.0
    assert elec.absolute_change == -1050.0
    assert elec.contribution_share == 91.3  # -1050 / -1150 = 91.30%
    assert elec.is_decline is True

    # Apparel dropped from 160 to 60 (-100 drop)
    app = next(c for c in contribs if c.category == "Apparel")
    assert app.current_revenue == 60.0
    assert app.previous_revenue == 160.0
    assert app.absolute_change == -100.0
    assert app.contribution_share == 8.7  # -100 / -1150 = 8.70%


def test_analyze_product_contributions_sku_ranking():
    """Verifies SKU ranking ranks the most severe dollar drops first."""
    current_prods = [{"product_id": 4, "product_name": "Classic Baseball Cap", "category": "Apparel", "revenue": 60.0, "units_sold": 3}]
    previous_prods = [
        {"product_id": 1, "product_name": "Pro Laptop 15", "category": "Electronics", "revenue": 1000.0, "units_sold": 1},
        {"product_id": 2, "product_name": "Wireless Mouse", "category": "Electronics", "revenue": 50.0, "units_sold": 1},
        {"product_id": 3, "product_name": "Premium Hoodie", "category": "Apparel", "revenue": 160.0, "units_sold": 2},
    ]

    prod_contribs = analyze_product_contributions(current_prods, previous_prods, limit=5)
    assert len(prod_contribs) == 4

    # Top drop: Laptop (-$1,000)
    top_drop = prod_contribs[0]
    assert top_drop.product_id == 1
    assert top_drop.product_name == "Pro Laptop 15"
    assert top_drop.absolute_change == -1000.0
    assert top_drop.units_change == -1
    assert top_drop.is_decline is True


# -----------------------------------------------------------------------------
# 4. End-to-End Revenue Decline Investigation on Known Dataset
# -----------------------------------------------------------------------------
def test_investigate_revenue_decline_march_vs_february(seeded_db_session):
    """Deterministic end-to-end investigation of March 2024 decline vs February 2024.

    Known Ground Truth from seeded_db_session:
    - February 2024 (O3 + O4):
        Revenue: $1,210.00 ($160 Hoodie + $1000 Laptop + $50 Mouse)
        Orders: 2 (O3, O4)
        AOV: $605.00
    - March 2024 (O5 cancelled, O6 returned, O7 pending):
        Revenue: $60.00 (3x Cap @ $20 = $60)
        Orders: 1 (O7)
        AOV: $60.00
    - Delta:
        Revenue Delta: -$1,150.00 (-95.04%)
        Order Delta: -1 (-50.0%)
        AOV Delta: -$545.00 (-90.08%)
        Primary Category Drop: Electronics (-$1,050.00, 91.3% share)
        Second Category Drop: Apparel (-$100.00, 8.7% share)
    """
    report: RevenueDeclineReport = investigate_revenue_decline(
        db=seeded_db_session,
        current_start="2024-03-01",
        current_end="2024-03-31",
        previous_start="2024-02-01",
        previous_end="2024-02-29",
    )

    assert isinstance(report, RevenueDeclineReport)

    # 1. Period Summaries
    assert report.current_period.revenue == 60.00
    assert report.current_period.orders == 1
    assert report.current_period.aov == 60.00

    assert report.previous_period.revenue == 1210.00
    assert report.previous_period.orders == 2
    assert report.previous_period.aov == 605.00

    # 2. Metric Deltas
    assert report.revenue_change.absolute_change == -1150.00
    assert report.revenue_change.percentage_change == -95.04
    assert report.revenue_change.is_decline is True

    assert report.order_change.absolute_change == -1
    assert report.order_change.percentage_change == -50.0
    assert report.order_change.is_decline is True

    assert report.aov_change.absolute_change == -545.00
    assert report.aov_change.percentage_change == -90.08

    # 3. Category Contributions (Waterfall)
    cat_map = {c.category: c for c in report.category_contributions}
    assert "Electronics" in cat_map
    assert cat_map["Electronics"].current_revenue == 0.00
    assert cat_map["Electronics"].previous_revenue == 1050.00
    assert cat_map["Electronics"].absolute_change == -1050.00
    assert cat_map["Electronics"].contribution_share == 91.3

    assert "Apparel" in cat_map
    assert cat_map["Apparel"].current_revenue == 60.00
    assert cat_map["Apparel"].previous_revenue == 160.00
    assert cat_map["Apparel"].absolute_change == -100.00
    assert cat_map["Apparel"].contribution_share == 8.7

    # 4. Product Contributions (SKU level)
    top_prod_drop = report.product_contributions[0]
    assert top_prod_drop.product_name == "Pro Laptop 15"
    assert top_prod_drop.absolute_change == -1000.00

    # 5. Customer Activity Observations
    assert len(report.customer_activity.observations) > 0
    assert report.customer_activity.buyer_delta == -1

    # 6. Audit Trail & Grounding Evidence
    assert len(report.evidence) >= 4
    metrics_cited = [e.metric for e in report.evidence]
    assert "Revenue" in metrics_cited

    # 7. Summary & Limitations
    assert "-$1150.00 (-95.04%)" in report.summary
    assert "Electronics" in report.summary
    assert "Pro Laptop 15" in report.summary
    assert "Causation vs Correlation" in report.limitations
    assert "cancelled and returned orders were excluded" in report.limitations


def test_tool_registry_executes_revenue_decline_tool(seeded_db_session):
    """Verifies the tool registry exposes and executes investigate_revenue_decline cleanly."""
    args = {
        "current_start": "2024-03-01",
        "current_end": "2024-03-31",
        "previous_start": "2024-02-01",
        "previous_end": "2024-02-29",
    }
    res = default_tool_registry.execute_tool("investigate_revenue_decline", args, db=seeded_db_session)
    assert res.success is True
    assert res.data["revenue_change"]["absolute_change"] == -1150.00
    assert res.data["category_contributions"][0]["category"] == "Electronics"
