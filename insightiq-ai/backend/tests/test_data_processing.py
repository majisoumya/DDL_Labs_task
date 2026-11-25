"""Comprehensive Verification Tests for Data Processing, Profiling, Cleaning, and Ingestion."""

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
from app.data_processing.profiler import DataProfiler, DatasetProfile, SystemProfile
from app.data_processing.quality_report import generate_quality_report, save_quality_report
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
# 1. Profiler Tests
# -------------------------------------------------------------

def test_profiler_dimension_and_primary_key_inference():
    profiler = DataProfiler()
    df = pd.DataFrame({
        "customer_id": [1, 2, 3],
        "name": ["Alice", "Bob", "Charlie"],
        "email": ["a@ex.com", "b@ex.com", "c@ex.com"],
    })
    profile = profiler.profile_dataframe(df, dataset_name="customers")
    assert profile.row_count == 3
    assert profile.column_count == 3
    assert "customer_id" in profile.candidate_primary_keys
    assert profile.columns["customer_id"].is_candidate_pk is True


def test_profiler_duplicate_and_null_detection():
    profiler = DataProfiler()
    df = pd.DataFrame({
        "id": [1, 2, 2],
        "val": ["X", None, None],
    })
    profile = profiler.profile_dataframe(df, dataset_name="test_dataset")
    assert profile.duplicate_rows_count == 1
    assert profile.columns["val"].null_count == 2
    assert any("duplicate" in i.lower() for i in profile.data_quality_issues)


def test_profiler_invalid_numeric_and_date_detection():
    profiler = DataProfiler()
    df = pd.DataFrame({
        "price": [10.0, -5.0],
        "quantity": [2, 0],
        "created_at": ["2024-01-01", "invalid-date-format"],
    })
    profile = profiler.profile_dataframe(df, dataset_name="test_invalids")
    assert any("negative values" in i.lower() for i in profile.data_quality_issues)
    assert any("non-positive values" in i.lower() for i in profile.data_quality_issues)
    assert any("unparseable" in i.lower() for i in profile.data_quality_issues)


# -------------------------------------------------------------
# 2. Cleaner Tests
# -------------------------------------------------------------

def test_cleaner_normalization_and_whitespace_trimming():
    df = pd.DataFrame({
        " First Name ": ["  Alice  ", "Bob   "],
        "Unit Price!": [10.5, 20.0],
    })
    normalized = normalize_column_names(df)
    assert list(normalized.columns) == ["first_name", "unit_price"]

    stripped = strip_string_columns(normalized)
    assert stripped["first_name"].tolist() == ["Alice", "Bob"]


def test_cleaner_filters_missing_mandatory_and_duplicates():
    df = pd.DataFrame({
        "id": [1, 2, 3, 4, 4],
        "name": ["A", "B", None, "D", "E"],
    })
    cleaned, rejected, dup_count, null_count = clean_dataset(
        df,
        dataset_name="clean_test",
        required_columns=["id", "name"],
        primary_key="id",
    )
    # Row 2 filtered for null name; Row 4 filtered for duplicate id
    assert len(cleaned) == 3
    assert null_count == 1
    assert dup_count == 1
    assert len(rejected) == 2


# -------------------------------------------------------------
# 3. Validator Tests
# -------------------------------------------------------------

def test_validator_dates_and_numerics():
    df_dates = pd.DataFrame({"dt": ["2024-01-01", "not-valid-date", "2024-02-15 10:00:00"]})
    valid_dates, date_rejects = validate_dates(df_dates, "dt", "dates")
    assert len(valid_dates) == 2
    assert len(date_rejects) == 1

    df_num = pd.DataFrame({"qty": [1, -1, 0, 5], "price": [10.0, 20.0, -5.0, 30.0]})
    valid_num, num_rejects = validate_numeric_constraints(
        df_num, "nums", positive_int_cols=["qty"], non_negative_numeric_cols=["price"]
    )
    # Row 1 (qty -1), Row 2 (qty 0, price -5) are invalid
    assert len(valid_num) == 2
    assert len(num_rejects) == 2


def test_validator_foreign_keys():
    df = pd.DataFrame({"order_id": [1, 2], "customer_id": [10, 999]})
    valid_df, rejects = validate_foreign_keys(
        df, "customer_id", valid_pk_set={10}, dataset_name="orders", target_table_name="customers"
    )
    assert len(valid_df) == 1
    assert len(rejects) == 1
    assert "999" in rejects[0]["reason"]


# -------------------------------------------------------------
# 4. Ingestion Pipeline & Idempotency Integration Test
# -------------------------------------------------------------

def test_ingestion_pipeline_end_to_end_and_idempotency():
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

    with tempfile.TemporaryDirectory() as temp_dir:
        raw_dir = Path(temp_dir)

        # Write test CSVs
        pd.DataFrame({
            "customer_id": [1, 2],
            "name": ["Alice", "Bob"],
            "email": ["alice@ex.com", "bob@ex.com"],
            "city": ["New York", "Chicago"],
            "created_at": ["2024-01-01", "2024-01-02"],
        }).to_csv(raw_dir / "customers.csv", index=False)

        pd.DataFrame({
            "product_id": [101, 102],
            "product_name": ["Prod A", "Prod B"],
            "category": ["Cat1", "Cat2"],
            "price": [10.00, 20.00],
            "stock": [50, 60],
        }).to_csv(raw_dir / "products.csv", index=False)

        pd.DataFrame({
            "order_id": [201, 202, 203],
            "customer_id": [1, 2, 999],  # 203 has orphan customer 999
            "order_date": ["2024-02-01", "2024-02-02", "2024-02-03"],
            "status": ["completed", "completed", "completed"],
        }).to_csv(raw_dir / "orders.csv", index=False)

        pd.DataFrame({
            "item_id": [301, 302, 302, 303],  # duplicate 302, orphan 303
            "order_id": [201, 202, 202, 999],
            "product_id": [101, 102, 102, 101],
            "quantity": [1, 2, 2, 1],
            "unit_price": [10.00, 20.00, 20.00, 10.00],
        }).to_csv(raw_dir / "order_items.csv", index=False)

        pipeline = IngestionPipeline(data_dir=raw_dir)

        # Run 1
        summary1 = pipeline.run(session)
        session.commit()
        assert summary1.success is True
        assert summary1.total_inserted_records == 8
        assert summary1.total_rejected_rows == 3

        assert session.scalar(select(func.count(Customer.customer_id))) == 2
        assert session.scalar(select(func.count(Product.product_id))) == 2
        assert session.scalar(select(func.count(Order.order_id))) == 2
        assert session.scalar(select(func.count(OrderItem.item_id))) == 2

        # Run 2: Idempotency
        summary2 = pipeline.run(session)
        session.commit()
        assert summary2.success is True
        assert summary2.total_inserted_records == 0
        assert summary2.total_skipped_existing == 8

    session.close()
    Base.metadata.drop_all(bind=engine)
