"""Data Cleaning and Normalization Module for InsightIQ AI.

Provides deterministic cleaning operations:
- Column name standardization
- Whitespace stripping
- Duplicate record extraction and logging
- Null detection on mandatory attributes
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Tuple
import pandas as pd


def normalize_column_names(df: pd.DataFrame) -> pd.DataFrame:
    """Standardizes column names to lowercase, stripped, underscore-separated strings."""
    df_copy = df.copy()
    cleaned_cols = []
    for col in df_copy.columns:
        clean = str(col).strip().lower()
        clean = re.sub(r"[^\w\s]", "", clean)
        clean = re.sub(r"\s+", "_", clean)
        cleaned_cols.append(clean)
    df_copy.columns = cleaned_cols
    return df_copy


def strip_string_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Strips leading and trailing whitespace from all string/object columns."""
    df_copy = df.copy()
    for col in df_copy.columns:
        if df_copy[col].dtype == "object":
            df_copy[col] = df_copy[col].apply(lambda x: x.strip() if isinstance(x, str) else x)
    return df_copy


def deduplicate_dataframe(
    df: pd.DataFrame,
    subset_keys: List[str],
    dataset_name: str,
) -> Tuple[pd.DataFrame, List[Dict[str, Any]], int]:
    """Identifies and separates duplicate records based on primary key or full row.

    Returns:
        (deduplicated_df, rejected_records_list, duplicate_count)
    """
    total_rows = len(df)
    duplicates_mask = df.duplicated(subset=subset_keys, keep="first")
    duplicate_count = int(duplicates_mask.sum())

    rejected_records: List[Dict[str, Any]] = []
    if duplicate_count > 0:
        dup_rows = df[duplicates_mask]
        for _, row in dup_rows.iterrows():
            rejected_records.append({
                "dataset": dataset_name,
                "stage": "deduplication",
                "reason": f"Duplicate record detected on keys {subset_keys}",
                "data": row.to_dict(),
            })

    cleaned_df = df[~duplicates_mask].copy()
    return cleaned_df, rejected_records, duplicate_count


def clean_dataset(
    df: pd.DataFrame,
    dataset_name: str,
    required_columns: List[str],
    primary_key: str,
) -> Tuple[pd.DataFrame, List[Dict[str, Any]], int, int]:
    """Applies standard cleaning pipeline:

    1. Normalize column names.
    2. Strip string whitespaces.
    3. Filter out records with null primary keys or required fields.
    4. Deduplicate on primary key.

    Returns:
        (cleaned_df, rejected_records, duplicate_count, missing_value_rows_count)
    """
    df_norm = normalize_column_names(df)
    df_stripped = strip_string_columns(df_norm)

    rejected: List[Dict[str, Any]] = []

    # Check for missing required columns in schema
    for col in required_columns:
        if col not in df_stripped.columns:
            raise ValueError(f"Dataset '{dataset_name}' missing required column: '{col}'")

    # Filter nulls in required columns
    null_mask = df_stripped[required_columns].isna().any(axis=1)
    missing_value_rows_count = int(null_mask.sum())

    if missing_value_rows_count > 0:
        bad_null_rows = df_stripped[null_mask]
        for _, row in bad_null_rows.iterrows():
            null_cols = [c for c in required_columns if pd.isna(row[c])]
            rejected.append({
                "dataset": dataset_name,
                "stage": "null_validation",
                "reason": f"Missing mandatory field(s): {null_cols}",
                "data": row.to_dict(),
            })

    valid_non_null = df_stripped[~null_mask].copy()

    # Deduplicate on primary key
    deduped_df, dup_rejects, dup_count = deduplicate_dataframe(
        valid_non_null,
        subset_keys=[primary_key],
        dataset_name=dataset_name,
    )
    rejected.extend(dup_rejects)

    return deduped_df, rejected, dup_count, missing_value_rows_count
