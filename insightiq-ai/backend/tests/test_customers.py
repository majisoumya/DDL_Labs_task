"""Independent Verification Tests for Customer Analytics.

Validates:
1. Total customer counting.
2. Customer ranking by spend with independent raw SQL verification.
3. Repeat customer identification (accounting for excluded returns/cancellations).
4. New customer identification based on first purchase timestamp.
5. Inactive customer detection using inactivity thresholds.
6. Order frequency distribution.
7. Empty dataset and boundary conditions.
"""

from datetime import datetime
from decimal import Decimal
import pytest
from sqlalchemy import text

from app.services.customer_service import (
    get_customer_metrics,
    get_customer_order_frequency,
    get_top_customers,
)


def test_customer_ranking_matches_independent_sql(seeded_db_session):
    """7. Verify customer rankings and spend against manual calculation and independent raw SQL."""
    session = seeded_db_session
    start_2024 = datetime(2024, 1, 1)
    end_2024 = datetime(2024, 3, 31, 23, 59, 59)

    top_customers = get_top_customers(session, limit=5, start_date=start_2024, end_date=end_2024)
    # Expected order:
    # 1. Alice (C1): O1 ($1,100) + O3 ($160) = $1,260.00
    # 2. Charlie (C3): O4 ($1,050) = $1,050.00
    # 3. Bob (C2): O2 ($120.00) (O6 returned is excluded) = $120.00
    # 4. David (C4): O7 ($60.00) (O5 cancelled is excluded) = $60.00
    assert len(top_customers) == 4

    assert top_customers[0]["customer_id"] == 1
    assert top_customers[0]["name"] == "Alice Smith"
    assert top_customers[0]["total_spend"] == Decimal("1260.00")
    assert top_customers[0]["order_count"] == 2

    assert top_customers[1]["customer_id"] == 3
    assert top_customers[1]["name"] == "Charlie Brown"
    assert top_customers[1]["total_spend"] == Decimal("1050.00")
    assert top_customers[1]["order_count"] == 1

    assert top_customers[2]["customer_id"] == 2
    assert top_customers[2]["name"] == "Bob Jones"
    assert top_customers[2]["total_spend"] == Decimal("120.00")
    assert top_customers[2]["order_count"] == 1

    assert top_customers[3]["customer_id"] == 4
    assert top_customers[3]["name"] == "David Miller"
    assert top_customers[3]["total_spend"] == Decimal("60.00")
    assert top_customers[3]["order_count"] == 1

    # Raw SQL Verification for Alice
    raw_sql = text("""
        SELECT SUM(oi.quantity * oi.unit_price)
        FROM order_items oi
        JOIN orders o ON o.order_id = oi.order_id
        WHERE o.customer_id = 1
          AND o.status NOT IN ('cancelled', 'returned')
          AND o.order_date >= :start_dt AND o.order_date <= :end_dt
    """)
    raw_alice_spend = session.execute(raw_sql, {"start_dt": start_2024, "end_dt": end_2024}).scalar()
    assert Decimal(str(raw_alice_spend)).quantize(Decimal("0.01")) == Decimal("1260.00")


def test_repeat_customers_calculation(seeded_db_session):
    """8. Verify repeat customer logic strictly excludes returned and cancelled orders."""
    session = seeded_db_session
    start_2024 = datetime(2024, 1, 1)
    end_2024 = datetime(2024, 3, 31, 23, 59, 59)

    metrics = get_customer_metrics(session, start_date=start_2024, end_date=end_2024)
    # Alice: 2 eligible orders (O1, O3) -> REPEAT
    # Bob: 1 eligible (O2), 1 returned (O6) -> NOT repeat
    # David: 1 cancelled (O5), 1 pending (O7) -> NOT repeat
    # Charlie: 1 eligible (O4) -> NOT repeat
    # Eve: 0 orders in 2024 -> NOT repeat
    assert metrics["repeat_customers"] == 1


def test_new_customers_calculation(seeded_db_session):
    """9. Verify new customer calculation based on first eligible order timestamp."""
    session = seeded_db_session

    # Jan 2024: Alice (Jan 10) and Bob (Jan 20) placed their first orders
    jan_metrics = get_customer_metrics(
        session,
        start_date=datetime(2024, 1, 1),
        end_date=datetime(2024, 1, 31, 23, 59, 59),
    )
    assert jan_metrics["new_customers"] == 2

    # Feb 2024: Charlie (Feb 25) placed his first order
    feb_metrics = get_customer_metrics(
        session,
        start_date=datetime(2024, 2, 1),
        end_date=datetime(2024, 2, 29, 23, 59, 59),
    )
    assert feb_metrics["new_customers"] == 1

    # Mar 2024: David's first eligible order was O7 (Mar 15, pending)
    mar_metrics = get_customer_metrics(
        session,
        start_date=datetime(2024, 3, 1),
        end_date=datetime(2024, 3, 31, 23, 59, 59),
    )
    assert mar_metrics["new_customers"] == 1


def test_inactive_customers_calculation(seeded_db_session):
    """10. Verify inactive customers (no eligible purchases in last 90 days)."""
    session = seeded_db_session
    # Reference date: end of March 2024 (90 days lookback = Jan 1, 2024)
    # Eve (C5) last purchased in April 2023 -> INACTIVE
    metrics = get_customer_metrics(
        session,
        end_date=datetime(2024, 3, 31, 23, 59, 59),
        inactive_days=90,
    )
    assert metrics["total_customers"] == 5
    assert metrics["inactive_customers"] == 1


def test_customer_order_frequency(seeded_db_session):
    """Verify customer order frequency distribution."""
    session = seeded_db_session
    start_2024 = datetime(2024, 1, 1)
    end_2024 = datetime(2024, 3, 31, 23, 59, 59)

    freq = get_customer_order_frequency(session, start_date=start_2024, end_date=end_2024)
    # Active in 2024: Bob (1), Charlie (1), David (1) -> 3 with 1 order
    # Alice (2) -> 1 with 2-3 orders
    assert freq["one_order"] == 3
    assert freq["two_to_three"] == 1
    assert freq["four_to_five"] == 0
    assert freq["six_plus"] == 0
    # Average orders = (1 + 1 + 1 + 2) / 4 = 1.25
    assert freq["average_orders_per_customer"] == 1.25


def test_empty_customer_metrics(empty_db_session):
    """Verify customer analytics on empty dataset."""
    session = empty_db_session
    metrics = get_customer_metrics(session)
    assert metrics["total_customers"] == 0
    assert metrics["new_customers"] == 0
    assert metrics["repeat_customers"] == 0
    assert metrics["inactive_customers"] == 0

    assert get_top_customers(session) == []
    freq = get_customer_order_frequency(session)
    assert freq["average_orders_per_customer"] == 0.0
