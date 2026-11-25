"""Unit tests for the DataProfiler and Quality Report generator."""

import tempfile
from pathlib import Path
import pandas as pd
import pytest

from app.data_processing.profiler import DataProfiler, DatasetProfile, SystemProfile
from app.data_processing.quality_report import generate_quality_report, save_quality_report


@pytest.fixture
def sample_csv_directory():
    """Creates a temporary directory with controlled CSV data fixtures."""
    with tempfile.TemporaryDirectory() as temp_dir:
        dir_path = Path(temp_dir)

        # 1. Customers CSV
        customers_df = pd.DataFrame({
            "customer_id": [1, 2, 3, 4, 5],
            "name": ["Alice Smith", "Bob Jones", "Charlie Brown", "Diana Prince", "Evan Wright"],
            "email": ["alice@ex.com", "bob@ex.com", "charlie@ex.com", "diana@ex.com", "evan@ex.com"],
            "city": ["New York", "Chicago", "Austin", "Seattle", "Boston"],
            "created_at": ["2024-01-15 10:00:00", "2024-02-01 11:30:00", "2024-02-14 09:15:00", "2024-03-01 14:00:00", "2024-03-20 16:45:00"],
        })
        customers_df.to_csv(dir_path / "customers.csv", index=False)

        # 2. Products CSV
        products_df = pd.DataFrame({
            "product_id": [101, 102, 103],
            "product_name": ["Wireless Mouse", "Mechanical Keyboard", "USB Hub"],
            "category": ["Electronics", "Electronics", "Electronics"],
            "price": [29.99, 89.99, 19.99],
            "stock": [100, 50, 200],
        })
        products_df.to_csv(dir_path / "products.csv", index=False)

        # 3. Orders CSV (with one cancelled order and one orphan customer_id for relationship testing)
        orders_df = pd.DataFrame({
            "order_id": [1001, 1002, 1003, 1004],
            "customer_id": [1, 2, 3, 999],  # 999 is orphan FK
            "order_date": ["2024-02-01", "2024-02-10", "2024-02-15", "invalid-date"],
            "status": ["completed", "completed", "cancelled", "pending"],
        })
        orders_df.to_csv(dir_path / "orders.csv", index=False)

        yield dir_path


def test_scan_files_finds_csv_files(sample_csv_directory):
    profiler = DataProfiler()
    found = profiler.scan_files(sample_csv_directory)
    file_names = {f.name for f in found}
    assert "customers.csv" in file_names
    assert "products.csv" in file_names
    assert "orders.csv" in file_names
    assert len(found) == 3


def test_profile_dataframe_counts_and_pk(sample_csv_directory):
    profiler = DataProfiler()
    df = pd.read_csv(sample_csv_directory / "customers.csv")
    profile = profiler.profile_dataframe(df, dataset_name="customers")

    assert profile.row_count == 5
    assert profile.column_count == 5
    assert profile.duplicate_rows_count == 0
    assert "customer_id" in profile.candidate_primary_keys
    assert profile.columns["customer_id"].is_candidate_pk is True
    assert profile.columns["customer_id"].null_count == 0


def test_profile_detects_duplicates():
    profiler = DataProfiler()
    df = pd.DataFrame({
        "id": [1, 2, 2],
        "val": ["A", "B", "B"],
    })
    profile = profiler.profile_dataframe(df, dataset_name="test_dup")
    assert profile.duplicate_rows_count == 1
    assert profile.duplicate_rows_percentage == pytest.approx(33.33, rel=1e-2)
    assert any("duplicate" in issue.lower() for issue in profile.data_quality_issues)


def test_profile_detects_nulls():
    profiler = DataProfiler()
    df = pd.DataFrame({
        "id": [1, 2, 3],
        "optional_note": ["first", None, "third"],
    })
    profile = profiler.profile_dataframe(df, dataset_name="test_nulls")
    assert profile.columns["optional_note"].null_count == 1
    assert profile.columns["optional_note"].null_percentage == pytest.approx(33.33, rel=1e-2)
    assert any("nulls" in issue.lower() for issue in profile.data_quality_issues)


def test_profile_detects_negative_prices_and_invalid_quantities():
    profiler = DataProfiler()
    df = pd.DataFrame({
        "product_id": [1, 2],
        "price": [19.99, -5.00],  # Invalid negative price
        "quantity": [2, 0],       # Invalid non-positive quantity
    })
    profile = profiler.profile_dataframe(df, dataset_name="test_invalids")
    assert any("negative values" in issue.lower() for issue in profile.data_quality_issues)
    assert any("non-positive values" in issue.lower() for issue in profile.data_quality_issues)


def test_profile_inspects_date_columns():
    profiler = DataProfiler()
    df = pd.DataFrame({
        "event_id": [1, 2, 3],
        "order_date": ["2024-01-01", "2024-01-15", "bad-date-format"],
    })
    profile = profiler.profile_dataframe(df, dataset_name="test_dates")
    date_stats = profile.columns["order_date"].date_stats
    assert date_stats is not None
    assert date_stats["unparseable_count"] == 1
    assert any("unparseable" in issue.lower() for issue in profile.data_quality_issues)


def test_relationship_detection(sample_csv_directory):
    profiler = DataProfiler()
    sys_profile = profiler.profile_all(sample_csv_directory)

    # orders.customer_id -> customers.customer_id
    cust_order_rels = [
        r for r in sys_profile.relationships
        if r.from_dataset == "orders" and r.to_dataset == "customers"
    ]
    assert len(cust_order_rels) == 1
    rel = cust_order_rels[0]
    assert rel.from_column == "customer_id"
    assert rel.to_column == "customer_id"
    # 3 out of 4 keys matched (customer 999 is orphan) -> 0.75
    assert rel.matched_ratio == 0.75
    assert rel.is_valid_fk is False  # Flagged warning due to orphan


def test_target_schema_comparison(sample_csv_directory):
    profiler = DataProfiler()
    sys_profile = profiler.profile_all(sample_csv_directory)

    assert "customers" in sys_profile.schema_comparison
    assert sys_profile.schema_comparison["customers"]["status"] == "MATCHED"
    # order_items was not in the sample fixtures
    assert sys_profile.schema_comparison["order_items"]["status"] == "MISSING"


def test_generate_and_save_quality_report(sample_csv_directory, tmp_path):
    profiler = DataProfiler()
    sys_profile = profiler.profile_all(sample_csv_directory)
    report_md = generate_quality_report(sys_profile)

    assert "# InsightIQ AI — Dataset Inspection & Data Quality Report" in report_md
    assert "Dataset Inventory" in report_md
    assert "Target Schema Comparison" in report_md

    out_file = tmp_path / "data_quality_report.md"
    saved = save_quality_report(sys_profile, out_file)
    assert saved.exists()
    assert saved.read_text(encoding="utf-8") == report_md
