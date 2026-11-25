"""Independent Verification Tests for Sales Analytics.

Validates:
1. Revenue calculation against independent manual figures and raw SQL.
2. Distinct order counting.
3. Average Order Value (AOV) and zero-division handling.
4. Monthly temporal aggregation.
5. Category revenue breakdown and percentage distribution.
6. Cancelled-order exclusion.
7. Returned/refunded order exclusion.
8. Empty dataset behavior.
9. Invalid date range handling.
10. Period-over-period sales growth calculations.
"""

from datetime import datetime
from decimal import Decimal
import pytest
from sqlalchemy import text

from app.services.sales_service import (
    get_monthly_revenue,
    get_revenue_by_category,
    get_revenue_by_product,
    get_sales_growth,
    get_sales_metrics,
)


def test_revenue_calculation_matches_independent_sql(seeded_db_session):
    """1. Verify total revenue for 2024 against manual calculation ($2,490.00) and raw SQL."""
    session = seeded_db_session
    start_2024 = datetime(2024, 1, 1)
    end_2024 = datetime(2024, 3, 31, 23, 59, 59)

    metrics = get_sales_metrics(session, start_date=start_2024, end_date=end_2024)

    # Independent Manual Ground Truth:
    # O1 ($1,100) + O2 ($120) + O3 ($160) + O4 ($1,050) + O7 ($60) = $2,490.00
    expected_revenue = Decimal("2490.00")
    assert metrics["total_revenue"] == expected_revenue

    # Independent Raw SQL Verification
    raw_sql = text("""
        SELECT COALESCE(SUM(oi.quantity * oi.unit_price), 0)
        FROM order_items oi
        JOIN orders o ON o.order_id = oi.order_id
        WHERE o.status NOT IN ('cancelled', 'returned')
          AND o.order_date >= :start_dt
          AND o.order_date <= :end_dt
    """)
    raw_revenue = session.execute(raw_sql, {"start_dt": start_2024, "end_dt": end_2024}).scalar()
    assert Decimal(str(raw_revenue)).quantize(Decimal("0.01")) == expected_revenue


def test_order_counting_matches_independent_sql(seeded_db_session):
    """2. Verify distinct eligible orders for 2024 (expected: 5 orders)."""
    session = seeded_db_session
    start_2024 = datetime(2024, 1, 1)
    end_2024 = datetime(2024, 3, 31, 23, 59, 59)

    metrics = get_sales_metrics(session, start_date=start_2024, end_date=end_2024)
    expected_orders = 5
    assert metrics["total_orders"] == expected_orders

    # Independent Raw SQL Verification
    raw_sql = text("""
        SELECT COUNT(DISTINCT o.order_id)
        FROM orders o
        WHERE o.status NOT IN ('cancelled', 'returned')
          AND o.order_date >= :start_dt
          AND o.order_date <= :end_dt
    """)
    raw_orders = session.execute(raw_sql, {"start_dt": start_2024, "end_dt": end_2024}).scalar()
    assert int(raw_orders) == expected_orders


def test_average_order_value_calculation(seeded_db_session):
    """3. Verify AOV = Revenue / Orders = $2,490.00 / 5 = $498.00."""
    session = seeded_db_session
    start_2024 = datetime(2024, 1, 1)
    end_2024 = datetime(2024, 3, 31, 23, 59, 59)

    metrics = get_sales_metrics(session, start_date=start_2024, end_date=end_2024)
    expected_aov = Decimal("498.00")
    assert metrics["aov"] == expected_aov


def test_cancelled_order_treatment(seeded_db_session):
    """11. Verify cancelled Order 5 ($1,000.00) is excluded from revenue and order count."""
    session = seeded_db_session
    # March 2024 has:
    # O5: cancelled ($1,000)
    # O6: returned ($80)
    # O7: pending ($60) - eligible
    march_metrics = get_sales_metrics(
        session,
        start_date=datetime(2024, 3, 1),
        end_date=datetime(2024, 3, 31, 23, 59, 59),
    )
    # Only O7 ($60) should count
    assert march_metrics["total_revenue"] == Decimal("60.00")
    assert march_metrics["total_orders"] == 1
    assert march_metrics["aov"] == Decimal("60.00")


def test_refund_treatment(seeded_db_session):
    """12. Verify returned/refunded Order 6 ($80.00) is excluded from revenue and order count."""
    session = seeded_db_session
    # Query exact date window around Order 6 (2024-03-10)
    o6_metrics = get_sales_metrics(
        session,
        start_date=datetime(2024, 3, 10, 0, 0),
        end_date=datetime(2024, 3, 10, 23, 59),
    )
    assert o6_metrics["total_revenue"] == Decimal("0.00")
    assert o6_metrics["total_orders"] == 0
    assert o6_metrics["aov"] == Decimal("0.00")


def test_monthly_aggregation_matches_ground_truth(seeded_db_session):
    """4. Verify monthly breakdown for 2024 (Jan: $1,220, Feb: $1,210, Mar: $60)."""
    session = seeded_db_session
    start_2024 = datetime(2024, 1, 1)
    end_2024 = datetime(2024, 3, 31, 23, 59, 59)

    monthly = get_monthly_revenue(session, start_date=start_2024, end_date=end_2024)
    assert len(monthly) == 3

    # Jan 2024
    assert monthly[0]["month"] == "2024-01"
    assert monthly[0]["revenue"] == Decimal("1220.00")
    assert monthly[0]["order_count"] == 2
    assert monthly[0]["units_sold"] == 6

    # Feb 2024
    assert monthly[1]["month"] == "2024-02"
    assert monthly[1]["revenue"] == Decimal("1210.00")
    assert monthly[1]["order_count"] == 2
    assert monthly[1]["units_sold"] == 4

    # Mar 2024
    assert monthly[2]["month"] == "2024-03"
    assert monthly[2]["revenue"] == Decimal("60.00")
    assert monthly[2]["order_count"] == 1
    assert monthly[2]["units_sold"] == 3


def test_category_revenue_and_percentages(seeded_db_session):
    """5. Verify category revenue: Electronics ($2,150, 86.35%) and Apparel ($340, 13.65%)."""
    session = seeded_db_session
    start_2024 = datetime(2024, 1, 1)
    end_2024 = datetime(2024, 3, 31, 23, 59, 59)

    categories = get_revenue_by_category(session, start_date=start_2024, end_date=end_2024)
    assert len(categories) == 2

    assert categories[0]["category"] == "Electronics"
    assert categories[0]["revenue"] == Decimal("2150.00")
    assert categories[0]["percentage"] == pytest.approx(86.35, rel=1e-2)

    assert categories[1]["category"] == "Apparel"
    assert categories[1]["revenue"] == Decimal("340.00")
    assert categories[1]["percentage"] == pytest.approx(13.65, rel=1e-2)


def test_empty_dataset_handling(empty_db_session):
    """13 & 15. Verify empty dataset handles zero-division cleanly."""
    session = empty_db_session
    metrics = get_sales_metrics(session)

    assert metrics["total_revenue"] == Decimal("0.00")
    assert metrics["total_orders"] == 0
    assert metrics["aov"] == Decimal("0.00")

    assert get_monthly_revenue(session) == []
    assert get_revenue_by_category(session) == []
    assert get_revenue_by_product(session) == []


def test_invalid_date_ranges(seeded_db_session):
    """14. Verify inverted date range (start > end) yields 0 results safely without exceptions."""
    session = seeded_db_session
    inverted_metrics = get_sales_metrics(
        session,
        start_date=datetime(2024, 12, 31),
        end_date=datetime(2024, 1, 1),
    )
    assert inverted_metrics["total_revenue"] == Decimal("0.00")
    assert inverted_metrics["total_orders"] == 0
    assert inverted_metrics["aov"] == Decimal("0.00")


def test_sales_growth_calculation(seeded_db_session):
    """10. Verify sales growth between Jan 2024 ($1,220) and Feb 2024 ($1,210)."""
    session = seeded_db_session
    growth = get_sales_growth(
        session,
        current_start=datetime(2024, 2, 1),
        current_end=datetime(2024, 2, 29),
        previous_start=datetime(2024, 1, 1),
        previous_end=datetime(2024, 1, 31),
    )
    # Revenue decreased by ($1,210 - $1,220) / $1,220 = -0.82%
    assert growth["revenue_growth_pct"] == pytest.approx(-0.82, rel=1e-2)
    assert growth["orders_growth_pct"] == 0.0  # 2 orders in both months
    # AOV changed from $610 ($1220/2) to $605 ($1210/2) = -0.82%
    assert growth["aov_growth_pct"] == pytest.approx(-0.82, rel=1e-2)
