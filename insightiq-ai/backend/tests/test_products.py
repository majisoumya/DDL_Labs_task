"""Independent Verification Tests for Product Analytics.

Validates:
1. Top-selling products ranked by units sold against independent raw SQL.
2. Highest revenue products ranked by revenue.
3. Low-performing product detection (including zero-sales catalog items).
4. Revenue threshold filtering.
5. Single product sales and volume metrics.
6. Empty database and boundary conditions.
"""

from datetime import datetime
from decimal import Decimal
import pytest
from sqlalchemy import text

from app.services.product_service import (
    get_highest_revenue_products,
    get_low_performing_products,
    get_product_category_breakdown,
    get_product_sales_quantity,
    get_top_selling_products,
)


def test_top_selling_products_ranked_by_units(seeded_db_session):
    """6. Verify top-selling products by volume against manual calculations and raw SQL."""
    session = seeded_db_session
    start_2024 = datetime(2024, 1, 1)
    end_2024 = datetime(2024, 3, 31, 23, 59, 59)

    top_units = get_top_selling_products(session, limit=5, start_date=start_2024, end_date=end_2024)
    # Expected units in 2024:
    # 1. P4 (Cap): 2 (O2) + 3 (O7) = 5 units
    # 2. P3 (Hoodie): 1 (O2) + 2 (O3) = 3 units (O6 returned excluded)
    # 3. P2 (Mouse): 2 (O1) + 1 (O4) = 3 units (O8 2023 excluded)
    # 4. P1 (Laptop): 1 (O1) + 1 (O4) = 2 units (O5 cancelled excluded)
    assert len(top_units) == 4

    assert top_units[0]["product_id"] == 4
    assert top_units[0]["product_name"] == "Classic Baseball Cap"
    assert top_units[0]["units_sold"] == 5

    # Raw SQL Verification for P4 units
    raw_sql = text("""
        SELECT SUM(oi.quantity)
        FROM order_items oi
        JOIN orders o ON o.order_id = oi.order_id
        WHERE oi.product_id = 4
          AND o.status NOT IN ('cancelled', 'returned')
          AND o.order_date >= :start_dt AND o.order_date <= :end_dt
    """)
    raw_p4_units = session.execute(raw_sql, {"start_dt": start_2024, "end_dt": end_2024}).scalar()
    assert int(raw_p4_units) == 5


def test_highest_revenue_products_ranking(seeded_db_session):
    """Verify products ranked by gross revenue."""
    session = seeded_db_session
    start_2024 = datetime(2024, 1, 1)
    end_2024 = datetime(2024, 3, 31, 23, 59, 59)

    top_rev = get_highest_revenue_products(session, limit=5, start_date=start_2024, end_date=end_2024)
    # Expected revenue in 2024:
    # 1. P1 (Laptop): 2 x $1,000 = $2,000.00
    # 2. P3 (Hoodie): 3 x $80    = $240.00
    # 3. P2 (Mouse):  3 x $50    = $150.00
    # 4. P4 (Cap):    5 x $20    = $100.00
    assert len(top_rev) == 4

    assert top_rev[0]["product_id"] == 1
    assert top_rev[0]["product_name"] == "Pro Laptop 15"
    assert top_rev[0]["revenue"] == Decimal("2000.00")

    assert top_rev[1]["product_id"] == 3
    assert top_rev[1]["revenue"] == Decimal("240.00")

    assert top_rev[2]["product_id"] == 2
    assert top_rev[2]["revenue"] == Decimal("150.00")

    assert top_rev[3]["product_id"] == 4
    assert top_rev[3]["revenue"] == Decimal("100.00")


def test_low_performing_products_includes_zero_sales_items(seeded_db_session):
    """Verify lowest-performing products captures catalog items with zero sales (P5 Book)."""
    session = seeded_db_session
    start_2024 = datetime(2024, 1, 1)
    end_2024 = datetime(2024, 3, 31, 23, 59, 59)

    low_products = get_low_performing_products(session, limit=5, start_date=start_2024, end_date=end_2024)
    assert len(low_products) == 5

    # P5 (Book) had zero sales -> must be first
    assert low_products[0]["product_id"] == 5
    assert low_products[0]["product_name"] == "Zero Sales Book"
    assert low_products[0]["revenue"] == Decimal("0.00")
    assert low_products[0]["units_sold"] == 0

    # Second lowest: P4 (Cap) with $100 revenue
    assert low_products[1]["product_id"] == 4
    assert low_products[1]["revenue"] == Decimal("100.00")


def test_low_performing_products_threshold_filter(seeded_db_session):
    """Verify filtering low performing products below a maximum revenue threshold."""
    session = seeded_db_session
    start_2024 = datetime(2024, 1, 1)
    end_2024 = datetime(2024, 3, 31, 23, 59, 59)

    # Threshold: <= $100.00 revenue (should capture P5 Book with $0 and P4 Cap with $100)
    filtered = get_low_performing_products(
        session,
        limit=10,
        threshold_revenue=Decimal("100.00"),
        start_date=start_2024,
        end_date=end_2024,
    )
    assert len(filtered) == 2
    assert {p["product_id"] for p in filtered} == {4, 5}


def test_get_product_sales_quantity(seeded_db_session):
    """Verify single-product metrics for active and unsold products."""
    session = seeded_db_session
    start_2024 = datetime(2024, 1, 1)
    end_2024 = datetime(2024, 3, 31, 23, 59, 59)

    # Active product (Laptop P1)
    laptop_stats = get_product_sales_quantity(session, product_id=1, start_date=start_2024, end_date=end_2024)
    assert laptop_stats["product_name"] == "Pro Laptop 15"
    assert laptop_stats["units_sold"] == 2
    assert laptop_stats["revenue"] == Decimal("2000.00")
    assert laptop_stats["order_count"] == 2

    # Unsold product (Book P5)
    book_stats = get_product_sales_quantity(session, product_id=5, start_date=start_2024, end_date=end_2024)
    assert book_stats["product_name"] == "Zero Sales Book"
    assert book_stats["units_sold"] == 0
    assert book_stats["revenue"] == Decimal("0.00")
    assert book_stats["order_count"] == 0

    # Unknown product (P999)
    unknown = get_product_sales_quantity(session, product_id=999)
    assert unknown["product_name"] == "Unknown"
    assert unknown["units_sold"] == 0


def test_empty_product_analytics(empty_db_session):
    """Verify product analytics behavior on empty database."""
    session = empty_db_session
    assert get_top_selling_products(session) == []
    assert get_highest_revenue_products(session) == []
    assert get_low_performing_products(session) == []
    assert get_product_category_breakdown(session) == []
