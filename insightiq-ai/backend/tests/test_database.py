"""Unit tests for database models, relationships, constraints, and sessions."""

from datetime import datetime, timezone
from decimal import Decimal
import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.base import Base
from app.database.models import Customer, Order, OrderItem, Product
from app.database.session import db_context, init_db


@pytest.fixture
def test_db_session():
    """Provides an isolated in-memory SQLite database session with enforced foreign keys."""
    # SQLite requires foreign_keys pragma enabled per connection
    test_engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    # Enable foreign keys for SQLite
    with test_engine.connect() as conn:
        conn.exec_driver_sql("PRAGMA foreign_keys = ON")

    # Create schema
    init_db(test_engine)

    TestingSessionLocal = sessionmaker(
        bind=test_engine,
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
    )

    session = TestingSessionLocal()
    try:
        yield session, TestingSessionLocal
    finally:
        session.close()
        Base.metadata.drop_all(bind=test_engine)


def test_create_customer(test_db_session):
    session, _ = test_db_session
    customer = Customer(
        name="Bruce Wayne",
        email="bruce.wayne@waynecorp.com",
        city="Gotham",
        created_at=datetime.now(timezone.utc),
    )
    session.add(customer)
    session.commit()

    retrieved = session.scalar(select(Customer).filter_by(email="bruce.wayne@waynecorp.com"))
    assert retrieved is not None
    assert retrieved.customer_id == 1
    assert retrieved.name == "Bruce Wayne"
    assert retrieved.city == "Gotham"


def test_customer_unique_email_constraint(test_db_session):
    session, _ = test_db_session
    c1 = Customer(name="User One", email="same@example.com", city="City A")
    c2 = Customer(name="User Two", email="same@example.com", city="City B")
    session.add(c1)
    session.commit()

    session.add(c2)
    with pytest.raises(IntegrityError):
        session.commit()
    session.rollback()


def test_product_model_and_decimal_precision(test_db_session):
    session, _ = test_db_session
    product = Product(
        product_name="Mechanical Keyboard",
        category="Electronics",
        price=Decimal("129.99"),
        stock=45,
    )
    session.add(product)
    session.commit()

    retrieved = session.scalar(select(Product).filter_by(product_name="Mechanical Keyboard"))
    assert retrieved is not None
    assert retrieved.price == Decimal("129.99")
    assert retrieved.stock == 45


def test_product_negative_price_constraint(test_db_session):
    session, _ = test_db_session
    invalid_product = Product(
        product_name="Faulty Item",
        category="Misc",
        price=Decimal("-10.00"),  # Violates chk_product_price_non_negative
        stock=5,
    )
    session.add(invalid_product)
    with pytest.raises(IntegrityError):
        session.commit()
    session.rollback()


def test_order_and_order_items_relationship(test_db_session):
    session, _ = test_db_session

    customer = Customer(name="Diana Prince", email="diana@themyscira.gov", city="Gateway City")
    product1 = Product(product_name="Shield", category="Armor", price=Decimal("150.00"), stock=10)
    product2 = Product(product_name="Lasso", category="Gear", price=Decimal("75.50"), stock=5)

    session.add_all([customer, product1, product2])
    session.commit()

    order = Order(
        customer_id=customer.customer_id,
        order_date=datetime.now(timezone.utc),
        status="completed",
    )
    session.add(order)
    session.commit()

    item1 = OrderItem(order_id=order.order_id, product_id=product1.product_id, quantity=1, unit_price=Decimal("150.00"))
    item2 = OrderItem(order_id=order.order_id, product_id=product2.product_id, quantity=2, unit_price=Decimal("75.50"))

    session.add_all([item1, item2])
    session.commit()

    # Verify bidirectional navigation
    loaded_order = session.scalar(select(Order).filter_by(order_id=order.order_id))
    assert loaded_order is not None
    assert len(loaded_order.items) == 2
    assert loaded_order.customer.name == "Diana Prince"

    # Verify total price calculation
    assert item1.total_price == Decimal("150.00")
    assert item2.total_price == Decimal("151.00")


def test_order_item_positive_quantity_constraint(test_db_session):
    session, _ = test_db_session

    customer = Customer(name="Clark Kent", email="clark@dailyplanet.com", city="Metropolis")
    product = Product(product_name="Glasses", category="Accessories", price=Decimal("25.00"), stock=10)
    session.add_all([customer, product])
    session.commit()

    order = Order(customer_id=customer.customer_id, order_date=datetime.now(timezone.utc), status="completed")
    session.add(order)
    session.commit()

    # Invalid quantity <= 0
    invalid_item = OrderItem(order_id=order.order_id, product_id=product.product_id, quantity=0, unit_price=Decimal("25.00"))
    session.add(invalid_item)
    with pytest.raises(IntegrityError):
        session.commit()
    session.rollback()


def test_cascade_delete_order_removes_items(test_db_session):
    session, _ = test_db_session

    customer = Customer(name="Barry Allen", email="barry@starlabs.org", city="Central City")
    product = Product(product_name="Running Shoes", category="Footwear", price=Decimal("120.00"), stock=20)
    session.add_all([customer, product])
    session.commit()

    order = Order(customer_id=customer.customer_id, order_date=datetime.now(timezone.utc), status="completed")
    session.add(order)
    session.commit()

    item = OrderItem(order_id=order.order_id, product_id=product.product_id, quantity=1, unit_price=Decimal("120.00"))
    session.add(item)
    session.commit()

    # Delete order
    session.delete(order)
    session.commit()

    # Verify order items were cascade deleted
    remaining_items = session.scalars(select(OrderItem).filter_by(order_id=order.order_id)).all()
    assert len(remaining_items) == 0


def test_db_context_manager(test_db_session):
    _, testing_maker = test_db_session

    with db_context(custom_sessionmaker=testing_maker) as session:
        customer = Customer(name="Arthur Curry", email="arthur@atlantis.ocean", city="Atlantis")
        session.add(customer)

    # Verify committed outside context
    with db_context(custom_sessionmaker=testing_maker) as session:
        found = session.scalar(select(Customer).filter_by(name="Arthur Curry"))
        assert found is not None
        assert found.city == "Atlantis"
