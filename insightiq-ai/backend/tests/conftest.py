"""Shared Pytest Fixtures and Deterministic Datasets for Analytics Verification."""

from datetime import datetime
from decimal import Decimal
from typing import Generator
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.base import Base
from app.database.models import Customer, Order, OrderItem, Product
from app.database.session import init_db


@pytest.fixture
def empty_db_session() -> Generator[Session, None, None]:
    """Provides an empty in-memory SQLite session with enforced foreign keys."""
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

    yield session

    session.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def seeded_db_session(empty_db_session: Session) -> Session:
    """Populates empty_db_session with a deterministic reference dataset.

    Deterministic Dataset Specification:
    -----------------------------------
    CUSTOMERS (5):
      - C1 (Alice):   Registered 2023-11-01 08:00 (Repeat buyer in 2024, 2 orders)
      - C2 (Bob):     Registered 2024-01-15 10:00 (Single buyer in 2024, 1 completed, 1 returned)
      - C3 (Charlie): Registered 2024-02-01 12:00 (Single buyer in 2024, 1 completed)
      - C4 (David):   Registered 2024-03-01 14:00 (1 cancelled order, 1 pending order)
      - C5 (Eve):     Registered 2023-01-01 09:00 (Historical buyer in Apr 2023, inactive in 2024)

    PRODUCTS (5):
      - P1 (Laptop):  Electronics, Price $1,000.00, Stock 20
      - P2 (Mouse):   Electronics, Price $50.00,    Stock 100
      - P3 (Hoodie):  Apparel,     Price $80.00,    Stock 50
      - P4 (Cap):     Apparel,     Price $20.00,    Stock 150
      - P5 (Book):    Books,       Price $30.00,    Stock 40 (Zero sales)

    ORDERS (8):
      - O1: 2024-01-10 10:00 | C1 | completed | 1x P1 ($1,000) + 2x P2 ($100) = $1,100.00
      - O2: 2024-01-20 11:00 | C2 | completed | 1x P3 ($80)    + 2x P4 ($40)  = $120.00
      - O3: 2024-02-14 15:00 | C1 | completed | 2x P3 ($160)                  = $160.00
      - O4: 2024-02-25 16:00 | C3 | completed | 1x P1 ($1,000) + 1x P2 ($50)  = $1,050.00
      - O5: 2024-03-05 09:00 | C4 | cancelled | 1x P1 ($1,000)                = $1,000.00 (EXCLUDED)
      - O6: 2024-03-10 14:00 | C2 | returned  | 1x P3 ($80)                    = $80.00    (EXCLUDED)
      - O7: 2024-03-15 12:00 | C4 | pending   | 3x P4 ($60)                    = $60.00    (ELIGIBLE)
      - O8: 2023-04-01 10:00 | C5 | completed | 1x P2 ($50)                    = $50.00    (HISTORICAL)

    ELIGIBLE 2024 METRICS (O1, O2, O3, O4, O7):
      - Total Revenue: $1,100 + $120 + $160 + $1,050 + $60 = $2,490.00
      - Total Orders: 5
      - Average Order Value (AOV): $2,490.00 / 5 = $498.00
      - Category Revenue:
          Electronics: $1,100 (O1) + $1,050 (O4) = $2,150.00 (86.35%)
          Apparel:     $120 (O2) + $160 (O3) + $60 (O7) = $340.00 (13.65%)
          Books:       $0.00 (0.0%)
    """
    session = empty_db_session

    # Customers
    c1 = Customer(customer_id=1, name="Alice Smith", email="alice@test.com", city="New York", created_at=datetime(2023, 11, 1, 8, 0))
    c2 = Customer(customer_id=2, name="Bob Jones", email="bob@test.com", city="Chicago", created_at=datetime(2024, 1, 15, 10, 0))
    c3 = Customer(customer_id=3, name="Charlie Brown", email="charlie@test.com", city="Austin", created_at=datetime(2024, 2, 1, 12, 0))
    c4 = Customer(customer_id=4, name="David Miller", email="david@test.com", city="Seattle", created_at=datetime(2024, 3, 1, 14, 0))
    c5 = Customer(customer_id=5, name="Eve Taylor", email="eve@test.com", city="Denver", created_at=datetime(2023, 1, 1, 9, 0))
    session.add_all([c1, c2, c3, c4, c5])
    session.commit()

    # Products
    p1 = Product(product_id=1, product_name="Pro Laptop 15", category="Electronics", price=Decimal("1000.00"), stock=20)
    p2 = Product(product_id=2, product_name="Wireless Mouse", category="Electronics", price=Decimal("50.00"), stock=100)
    p3 = Product(product_id=3, product_name="Premium Hoodie", category="Apparel", price=Decimal("80.00"), stock=50)
    p4 = Product(product_id=4, product_name="Classic Baseball Cap", category="Apparel", price=Decimal("20.00"), stock=150)
    p5 = Product(product_id=5, product_name="Zero Sales Book", category="Books", price=Decimal("30.00"), stock=40)
    session.add_all([p1, p2, p3, p4, p5])
    session.commit()

    # Orders
    orders = [
        Order(order_id=1, customer_id=1, order_date=datetime(2024, 1, 10, 10, 0), status="completed"),
        Order(order_id=2, customer_id=2, order_date=datetime(2024, 1, 20, 11, 0), status="completed"),
        Order(order_id=3, customer_id=1, order_date=datetime(2024, 2, 14, 15, 0), status="completed"),
        Order(order_id=4, customer_id=3, order_date=datetime(2024, 2, 25, 16, 0), status="completed"),
        Order(order_id=5, customer_id=4, order_date=datetime(2024, 3, 5, 9, 0), status="cancelled"),
        Order(order_id=6, customer_id=2, order_date=datetime(2024, 3, 10, 14, 0), status="returned"),
        Order(order_id=7, customer_id=4, order_date=datetime(2024, 3, 15, 12, 0), status="pending"),
        Order(order_id=8, customer_id=5, order_date=datetime(2023, 4, 1, 10, 0), status="completed"),
    ]
    session.add_all(orders)
    session.commit()

    # Order Items
    items = [
        # O1: 1x P1 ($1000), 2x P2 ($100) = $1100
        OrderItem(item_id=1, order_id=1, product_id=1, quantity=1, unit_price=Decimal("1000.00")),
        OrderItem(item_id=2, order_id=1, product_id=2, quantity=2, unit_price=Decimal("50.00")),
        # O2: 1x P3 ($80), 2x P4 ($40) = $120
        OrderItem(item_id=3, order_id=2, product_id=3, quantity=1, unit_price=Decimal("80.00")),
        OrderItem(item_id=4, order_id=2, product_id=4, quantity=2, unit_price=Decimal("20.00")),
        # O3: 2x P3 ($160) = $160
        OrderItem(item_id=5, order_id=3, product_id=3, quantity=2, unit_price=Decimal("80.00")),
        # O4: 1x P1 ($1000), 1x P2 ($50) = $1050
        OrderItem(item_id=6, order_id=4, product_id=1, quantity=1, unit_price=Decimal("1000.00")),
        OrderItem(item_id=7, order_id=4, product_id=2, quantity=1, unit_price=Decimal("50.00")),
        # O5 (Cancelled): 1x P1 ($1000)
        OrderItem(item_id=8, order_id=5, product_id=1, quantity=1, unit_price=Decimal("1000.00")),
        # O6 (Returned): 1x P3 ($80)
        OrderItem(item_id=9, order_id=6, product_id=3, quantity=1, unit_price=Decimal("80.00")),
        # O7 (Pending): 3x P4 ($60) = $60
        OrderItem(item_id=10, order_id=7, product_id=4, quantity=3, unit_price=Decimal("20.00")),
        # O8 (Historical): 1x P2 ($50) = $50
        OrderItem(item_id=11, order_id=8, product_id=2, quantity=1, unit_price=Decimal("50.00")),
    ]
    session.add_all(items)
    session.commit()

    return session


def verify_with_raw_sql(session: Session, query: str, **params) -> Decimal | int | float | None:
    """Executes an independent direct raw SQL query to cross-verify analytical results."""
    result = session.execute(text(query), params).scalar()
    return result
