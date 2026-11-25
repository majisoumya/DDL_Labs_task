"""Unit and integration tests for data cleaning, validation, and ingestion pipeline."""

from datetime import datetime
from decimal import Decimal
import tempfile
from pathlib import Path
import pandas as pd
import pytest
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.base import Base
from app.database.models import Customer, Order, OrderItem, Product
from app.database.session import init_db
from app.data_processing.cleaner import (
    clean_dataset,
    deduplicate_dataframe,
    normalize_column_names,
    strip_string_columns,
)
from app.data_processing.ingestion import IngestionPipeline, IngestionSummary
from app.data_processing.transformers import (
    transform_customer_records,
    transform_order_item_records,
    transform_order_records,
    transform_product_records,
)
from app.data_processing.validators import (
    validate_dates,
    validate_foreign_keys,
    validate_numeric_constraints,
)


# -------------------------------------------------------------
# Unit Tests: Cleaning
# -------------------------------------------------------------

def test_normalize_column_names():
    df = pd.DataFrame(columns=[" Customer ID ", "Unit-Price", "Order Date!", "STATUS"])
    normalized = normalize_column_names(df)
    assert list(normalized.columns) == ["customer_id", "unitprice", "order_date", "status"]


def test_strip_string_columns():
    df = pd.DataFrame({
        "name": ["  Alice  ", "Bob   ", "  Charlie"],
        "num": [1, 2, 3],
    })
    stripped = strip_string_columns(df)
    assert stripped["name"].tolist() == ["Alice", "Bob", "Charlie"]
    assert stripped["num"].tolist() == [1, 2, 3]


def test_clean_dataset_filters_nulls_and_duplicates():
    df = pd.DataFrame({
        "id": [1, 2, 3, 4, 4],
        "name": ["A", "B", None, "D", "E"],  # row 2 has null name; row 4 has duplicate id=4
    })
    cleaned, rejected, dup_count, null_count = clean_dataset(
        df,
        dataset_name="test_items",
        required_columns=["id", "name"],
        primary_key="id",
    )
    # Row 2 filtered for null name; Row 4 filtered for duplicate id
    assert len(cleaned) == 3
    assert null_count == 1
    assert dup_count == 1
    assert len(rejected) == 2


# -------------------------------------------------------------
# Unit Tests: Validation
# -------------------------------------------------------------

def test_validate_dates():
    df = pd.DataFrame({
        "date_str": ["2024-01-01 10:00:00", "not-a-date", "2024-02-15"],
    })
    valid_df, rejects = validate_dates(df, "date_str", "test_dates")
    assert len(valid_df) == 2
    assert len(rejects) == 1
    assert rejects[0]["reason"].startswith("Unparseable date")


def test_validate_numeric_constraints():
    df = pd.DataFrame({
        "price": [19.99, -5.00, 25.50],
        "quantity": [1, 2, 0],
    })
    valid_df, rejects = validate_numeric_constraints(
        df,
        dataset_name="test_numeric",
        positive_int_cols=["quantity"],
        non_negative_numeric_cols=["price"],
    )
    # Row 1 has negative price, Row 2 has 0 quantity
    assert len(valid_df) == 1
    assert len(rejects) == 2


def test_validate_foreign_keys():
    df = pd.DataFrame({
        "order_id": [101, 102, 103],
        "customer_id": [1, 2, 999],  # 999 does not exist
    })
    valid_customers = {1, 2, 3}
    valid_df, rejects = validate_foreign_keys(
        df,
        fk_column="customer_id",
        valid_pk_set=valid_customers,
        dataset_name="orders",
        target_table_name="customers",
    )
    assert len(valid_df) == 2
    assert len(rejects) == 1
    assert "999" in rejects[0]["reason"]


# -------------------------------------------------------------
# Unit Tests: Transformers
# -------------------------------------------------------------

def test_transformers():
    df_cust = pd.DataFrame({
        "customer_id": [1],
        "name": [" Bruce Wayne "],
        "email": [" BRUCE@WayneCorp.COM "],
        "city": [" Gotham "],
        "created_at": ["2024-01-01 12:00:00"],
    })
    cust_records = transform_customer_records(df_cust)
    assert cust_records[0]["email"] == "bruce@waynecorp.com"
    assert cust_records[0]["name"] == "Bruce Wayne"
    assert isinstance(cust_records[0]["created_at"], datetime)

    df_prod = pd.DataFrame({
        "product_id": [10],
        "product_name": ["Gadget"],
        "category": ["Tech"],
        "price": [99.994],
        "stock": [50],
    })
    prod_records = transform_product_records(df_prod)
    assert prod_records[0]["price"] == Decimal("99.99")


# -------------------------------------------------------------
# Integration Test: IngestionPipeline & Idempotency
# -------------------------------------------------------------

@pytest.fixture
def ingestion_fixture():
    """Sets up an in-memory SQLite database and test CSV files."""
    test_engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    with test_engine.connect() as conn:
        conn.exec_driver_sql("PRAGMA foreign_keys = ON")

    init_db(test_engine)

    TestingSession = sessionmaker(bind=test_engine, autoflush=False, autocommit=False)
    session = TestingSession()

    with tempfile.TemporaryDirectory() as temp_dir:
        raw_dir = Path(temp_dir)

        # 1. Customers CSV
        pd.DataFrame({
            "customer_id": [1, 2],
            "name": ["Alice", "Bob"],
            "email": ["alice@ex.com", "bob@ex.com"],
            "city": ["New York", "Chicago"],
            "created_at": ["2024-01-01 10:00:00", "2024-01-02 11:00:00"],
        }).to_csv(raw_dir / "customers.csv", index=False)

        # 2. Products CSV
        pd.DataFrame({
            "product_id": [101, 102],
            "product_name": ["Item A", "Item B"],
            "category": ["Cat1", "Cat2"],
            "price": [19.99, 49.99],
            "stock": [100, 50],
        }).to_csv(raw_dir / "products.csv", index=False)

        # 3. Orders CSV (order 203 has orphan customer 999)
        pd.DataFrame({
            "order_id": [201, 202, 203],
            "customer_id": [1, 2, 999],
            "order_date": ["2024-02-01 14:00:00", "2024-02-02 15:00:00", "2024-02-03 16:00:00"],
            "status": ["completed", "pending", "completed"],
        }).to_csv(raw_dir / "orders.csv", index=False)

        # 4. Order Items CSV (item 302 has duplicate, item 303 has orphan order 999)
        pd.DataFrame({
            "item_id": [301, 302, 302, 303],
            "order_id": [201, 202, 202, 999],
            "product_id": [101, 102, 102, 101],
            "quantity": [1, 2, 2, 1],
            "unit_price": [19.99, 49.99, 49.99, 19.99],
        }).to_csv(raw_dir / "order_items.csv", index=False)

        yield session, raw_dir

    session.close()
    Base.metadata.drop_all(bind=test_engine)


def test_ingestion_pipeline_end_to_end_and_idempotency(ingestion_fixture):
    session, raw_dir = ingestion_fixture
    pipeline = IngestionPipeline(data_dir=raw_dir)

    # First Run
    summary1 = pipeline.run(session)
    session.commit()

    assert summary1.success is True
    assert summary1.total_inserted_records == 8  # 2 cust + 2 prod + 2 orders + 2 items
    assert summary1.total_duplicate_rows == 1    # item 302 duplicate
    assert summary1.total_rejected_rows == 3     # 1 item duplicate + 1 order orphan (cust 999) + 1 item orphan (order 999)

    # Verify rows in DB
    assert session.scalar(select(func.count(Customer.customer_id))) == 2
    assert session.scalar(select(func.count(Product.product_id))) == 2
    assert session.scalar(select(func.count(Order.order_id))) == 2
    assert session.scalar(select(func.count(OrderItem.item_id))) == 2

    # Second Run (Idempotency verification)
    summary2 = pipeline.run(session)
    session.commit()

    assert summary2.success is True
    assert summary2.total_inserted_records == 0  # No duplicates inserted
    assert summary2.total_skipped_existing == 8  # All 8 existing records skipped cleanly
    assert session.scalar(select(func.count(Customer.customer_id))) == 2

    # Markdown format verification
    md = summary1.to_markdown()
    assert "### Ingestion Execution Summary" in md
    assert "customers" in md
    assert "order_items" in md
