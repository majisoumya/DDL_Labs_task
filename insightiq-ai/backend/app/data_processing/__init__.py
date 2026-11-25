"""Data processing, ingestion, validation, and profiling package for InsightIQ AI."""

from .cleaner import clean_dataset, deduplicate_dataframe, normalize_column_names, strip_string_columns
from .ingestion import IngestionPipeline, IngestionSummary, TableIngestionReport
from .profiler import DataProfiler
from .quality_report import generate_quality_report, save_quality_report
from .transformers import (
    transform_customer_records,
    transform_order_item_records,
    transform_order_records,
    transform_product_records,
)
from .validators import validate_dates, validate_foreign_keys, validate_numeric_constraints

__all__ = [
    "clean_dataset",
    "deduplicate_dataframe",
    "normalize_column_names",
    "strip_string_columns",
    "validate_dates",
    "validate_numeric_constraints",
    "validate_foreign_keys",
    "transform_customer_records",
    "transform_product_records",
    "transform_order_records",
    "transform_order_item_records",
    "IngestionPipeline",
    "IngestionSummary",
    "TableIngestionReport",
    "DataProfiler",
    "generate_quality_report",
    "save_quality_report",
]
