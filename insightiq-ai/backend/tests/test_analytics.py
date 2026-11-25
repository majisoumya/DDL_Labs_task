"""Unit and verification tests for the Core Business Analytics Engine."""

from datetime import datetime
from decimal import Decimal
import pytest
from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.base import Base
from app.database.models import Customer, Order, OrderItem, Product
from app.database.session import init_db
from app.services.analytics_service import get_dashboard_summary
from app.services.customer_service import (
    get_customer_metrics,
    get_customer_order_frequency,
    get_top_customers,
)
from app.services.product_service import (
    get_highest_revenue_products,
    get_low_performing_products,
    get_product_sales_quantity,
    get_top_selling_products,
)
from app.services.sales_service import (
    get_monthly_revenue,
    get_revenue_by_category,
    get_revenue_by_product,
    get_sales_growth,
    get_sales_metrics,
)


@pytest.fixture
def analytics_db_session():
    """Sets up an in-memory SQLite database populated with controlled analytics fixtures."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    with engine.connect() as conn:
        conn.exec_driver_sql("PRAGMA foreign_keys = ON")

    init_db(engine)
    TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    session = TestingSession()

    # 1. Customers
    # Customer 1: Registered Jan 2024 (Repeat buyer, total 2 eligible orders)
    # Customer 2: Registered Feb 2024 (Single buyer)
    # Customer 3: Registered Mar 2024 (Only placed a cancelled order)
    # Customer 4: Registered Aug 2023 (Inactive, no recent orders)
    c1 = Customer(customer_id=1, name="Alice", email="alice@test.com", city="New York", created_at=datetime(2024, 1, 10))
    c2 = Customer(customer_id=2, name="Bob", email="bob@test.com", city="Chicago", created_at=datetime(2024, 2, 5))
    c3 = Customer(customer_id=3, name="Charlie", email="charlie@test.com", city="Austin", created_at=datetime(2024, 3, 1))
    c4 = Customer(customer_id=4, name="Diana", email="diana@test.com", city="Denver", created_at=datetime(2023, 8, 1))
    session.add_all([c1, c2, c3, c4])

    # 2. Products
    p1 = Product(product_id=1, product_name="Headphones", category="Electronics", price=Decimal("100.00"), stock=50)
    p2 = Product(product_id=2, product_name="Keyboard", category="Electronics", price=Decimal("50.00"), stock=30)
    p3 = Product(product_id=3, product_name="T-Shirt", category="Apparel", price=Decimal("25.00"), stock=100)
    p4 = Product(product_id=4, product_name="Unsold Book", category="Books", price=Decimal("15.00"), stock=20)
    session.add_all([p1, p2, p3, p4])
    session.commit()

    # 3. Orders
    # Order 1: Jan 15, completed, Alice -> Headphones ($100 * 2 = $200)
    o1 = Order(order_id=1, customer_id=1, order_date=datetime(2024, 1, 15, 10, 0), status="completed")
    # Order 2: Feb 10, completed, Alice -> Keyboard ($50 * 1 = $50) + T-Shirt ($25 * 2 = $50) -> $100
    o2 = Order(order_id=2, customer_id=1, order_date=datetime(2024, 2, 10, 11, 0), status="completed")
    # Order 3: Feb 20, completed, Bob -> T-Shirt ($25 * 4 = $100)
    o3 = Order(order_id=3, customer_id=2, order_date=datetime(2024, 2, 20, 14, 0), status="completed")
    # Order 4: Mar 05, cancelled, Charlie -> Headphones ($100 * 1 = $100) - SHOULD BE EXCLUDED
    o4 = Order(order_id=4, customer_id=3, order_date=datetime(2024, 3, 5, 9, 0), status="cancelled")
    # Order 5: Mar 10, returned, Bob -> Keyboard ($50 * 1 = $50) - SHOULD BE EXCLUDED
    o5 = Order(order_id=5, customer_id=2, order_date=datetime(2024, 3, 10, 15, 0), status="returned")
    session.add_all([o1, o2, o3, o4, o5])
    session.commit()

    # 4. Order Items
    items = [
        OrderItem(item_id=1, order_id=1, product_id=1, quantity=2, unit_price=Decimal("100.00")),  # $200
        OrderItem(item_id=2, order_id=2, product_id=2, quantity=1, unit_price=Decimal("50.00")),   # $50
        OrderItem(item_id=3, order_id=2, product_id=3, quantity=2, unit_price=Decimal("25.00")),   # $50
        OrderItem(item_id=4, order_id=3, product_id=3, quantity=4, unit_price=Decimal("25.00")),   # $100
        OrderItem(item_id=5, order_id=4, product_id=1, quantity=1, unit_price=Decimal("100.00")),  # Cancelled ($100)
        OrderItem(item_id=6, order_id=5, product_id=2, quantity=1, unit_price=Decimal("50.00")),   # Returned ($50)
    ]
    session.add_all(items)
    session.commit()

    yield session

    session.close()
    Base.metadata.drop_all(bind=engine)


# -------------------------------------------------------------
# SALES SERVICE TESTS
# -------------------------------------------------------------

def test_get_sales_metrics_excludes_cancelled_and_returned(analytics_db_session):
    session = analytics_db_session
    metrics = get_sales_metrics(session)

    # Eligible orders: Order 1 ($200), Order 2 ($100), Order 3 ($100).
    # Cancelled Order 4 ($100) and Returned Order 5 ($50) must be excluded.
    # Total Revenue = $400.00.
    # Total Orders = 3.
    # AOV = 400.00 / 3 = 133.33.
    assert metrics["total_revenue"] == Decimal("400.00")
    assert metrics["total_orders"] == 3
    assert metrics["aov"] == Decimal("133.33")

    # Independent Raw SQL Verification
    raw_sql = text("""
        SELECT SUM(oi.quantity * oi.unit_price) AS raw_sum
        FROM order_items oi
        JOIN orders o ON o.order_id = oi.order_id
        WHERE o.status NOT IN ('cancelled', 'returned')
    """)
    raw_res = session.execute(raw_sql).scalar()
    assert Decimal(str(raw_res)).quantize(Decimal("0.01")) == metrics["total_revenue"]


def test_get_sales_metrics_date_range_filter(analytics_db_session):
    session = analytics_db_session
    # Filter for January only
    jan_metrics = get_sales_metrics(session, start_date=datetime(2024, 1, 1), end_date=datetime(2024, 1, 31, 23, 59))
    assert jan_metrics["total_revenue"] == Decimal("200.00")
    assert jan_metrics["total_orders"] == 1
    assert jan_metrics["aov"] == Decimal("200.00")


def test_get_sales_metrics_empty_results_handling(analytics_db_session):
    session = analytics_db_session
    # Date range with zero orders
    empty_metrics = get_sales_metrics(session, start_date=datetime(2020, 1, 1), end_date=datetime(2020, 1, 31))
    assert empty_metrics["total_revenue"] == Decimal("0.00")
    assert empty_metrics["total_orders"] == 0
    assert empty_metrics["aov"] == Decimal("0.00")


def test_get_monthly_revenue(analytics_db_session):
    session = analytics_db_session
    monthly = get_monthly_revenue(session)

    assert len(monthly) == 2
    # Jan 2024: $200 revenue, 1 order, 2 units
    assert monthly[0]["month"] == "2024-01"
    assert monthly[0]["revenue"] == Decimal("200.00")
    assert monthly[0]["order_count"] == 1
    assert monthly[0]["units_sold"] == 2

    # Feb 2024: $200 revenue, 2 orders (Order 2 + Order 3), 7 units (1+2+4)
    assert monthly[1]["month"] == "2024-02"
    assert monthly[1]["revenue"] == Decimal("200.00")
    assert monthly[1]["order_count"] == 2
    assert monthly[1]["units_sold"] == 7


def test_get_revenue_by_category(analytics_db_session):
    session = analytics_db_session
    cat_revenue = get_revenue_by_category(session)

    # Categories:
    # Electronics: p1 ($200) + p2 ($50) = $250.00 (62.5%)
    # Apparel: p3 ($50 + $100) = $150.00 (37.5%)
    # Books: $0 (not in eligible sales)
    assert len(cat_revenue) == 2
    assert cat_revenue[0]["category"] == "Electronics"
    assert cat_revenue[0]["revenue"] == Decimal("250.00")
    assert cat_revenue[0]["percentage"] == 62.5

    assert cat_revenue[1]["category"] == "Apparel"
    assert cat_revenue[1]["revenue"] == Decimal("150.00")
    assert cat_revenue[1]["percentage"] == 37.5


def test_get_sales_growth(analytics_db_session):
    session = analytics_db_session
    growth = get_sales_growth(
        session,
        current_start=datetime(2024, 2, 1),
        current_end=datetime(2024, 2, 29),
        previous_start=datetime(2024, 1, 1),
        previous_end=datetime(2024, 1, 31),
    )
    # Jan: $200 revenue, 1 order, AOV $200
    # Feb: $200 revenue, 2 orders, AOV $100
    assert growth["revenue_growth_pct"] == 0.0
    assert growth["orders_growth_pct"] == 100.0  # From 1 to 2 orders (+100%)
    assert growth["aov_growth_pct"] == -50.0     # From $200 to $100 (-50%)


# -------------------------------------------------------------
# CUSTOMER SERVICE TESTS
# -------------------------------------------------------------

def test_get_customer_metrics(analytics_db_session):
    session = analytics_db_session
    cust_metrics = get_customer_metrics(session, end_date=datetime(2024, 3, 31))

    # Total customers: 4
    assert cust_metrics["total_customers"] == 4

    # Repeat customers: Alice has 2 eligible orders -> 1
    assert cust_metrics["repeat_customers"] == 1

    # Inactive customers: Diana registered in Aug 2023 and has 0 orders in last 90 days
    assert cust_metrics["inactive_customers"] >= 1


def test_get_top_customers(analytics_db_session):
    session = analytics_db_session
    top_custs = get_top_customers(session, limit=5)

    # Alice spent $300 (Order 1 $200 + Order 2 $100)
    # Bob spent $100 (Order 3 $100)
    assert len(top_custs) == 2
    assert top_custs[0]["customer_id"] == 1
    assert top_custs[0]["name"] == "Alice"
    assert top_custs[0]["total_spend"] == Decimal("300.00")
    assert top_custs[0]["order_count"] == 2

    assert top_custs[1]["customer_id"] == 2
    assert top_custs[1]["name"] == "Bob"
    assert top_custs[1]["total_spend"] == Decimal("100.00")


def test_get_customer_order_frequency(analytics_db_session):
    session = analytics_db_session
    freq = get_customer_order_frequency(session)

    # Bob has 1 order, Alice has 2 orders
    assert freq["one_order"] == 1
    assert freq["two_to_three"] == 1
    assert freq["average_orders_per_customer"] == 1.5


# -------------------------------------------------------------
# PRODUCT SERVICE TESTS
# -------------------------------------------------------------

def test_get_top_selling_and_highest_revenue_products(analytics_db_session):
    session = analytics_db_session

    # Units sold:
    # p3 (T-Shirt): 2 + 4 = 6 units
    # p1 (Headphones): 2 units
    # p2 (Keyboard): 1 unit
    top_units = get_top_selling_products(session, limit=2)
    assert top_units[0]["product_id"] == 3
    assert top_units[0]["units_sold"] == 6

    # Highest revenue:
    # p1: $200.00
    # p3: $150.00
    top_rev = get_highest_revenue_products(session, limit=2)
    assert top_rev[0]["product_id"] == 1
    assert top_rev[0]["revenue"] == Decimal("200.00")


def test_get_low_performing_products_includes_zero_sales(analytics_db_session):
    session = analytics_db_session
    low_prods = get_low_performing_products(session, limit=5)

    # Unsold Book (p4) has 0 revenue and 0 units sold, should be first
    assert low_prods[0]["product_id"] == 4
    assert low_prods[0]["revenue"] == Decimal("0.00")
    assert low_prods[0]["units_sold"] == 0


def test_get_product_sales_quantity(analytics_db_session):
    session = analytics_db_session
    p1_details = get_product_sales_quantity(session, product_id=1)
    assert p1_details["product_name"] == "Headphones"
    assert p1_details["units_sold"] == 2
    assert p1_details["revenue"] == Decimal("200.00")
    assert p1_details["order_count"] == 1


# -------------------------------------------------------------
# DASHBOARD SUMMARY TESTS
# -------------------------------------------------------------

def test_get_dashboard_summary(analytics_db_session):
    session = analytics_db_session
    summary = get_dashboard_summary(session)

    assert "kpis" in summary
    assert summary["kpis"]["total_revenue"] == Decimal("400.00")
    assert summary["kpis"]["total_orders"] == 3
    assert summary["kpis"]["total_customers"] == 4
    assert summary["kpis"]["average_order_value"] == Decimal("133.33")

    assert len(summary["monthly_trend"]) == 2
    assert len(summary["category_distribution"]) == 2
    assert len(summary["top_products"]) == 3
