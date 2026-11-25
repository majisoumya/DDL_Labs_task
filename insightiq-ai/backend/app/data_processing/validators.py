"""Data Validation Rules and Referential Integrity Checks for InsightIQ AI."""

from __future__ import annotations

from typing import Any, Dict, List, Set, Tuple
import pandas as pd


def validate_dates(
    df: pd.DataFrame,
    date_column: str,
    dataset_name: str,
) -> Tuple[pd.DataFrame, List[Dict[str, Any]]]:
    """Validates that values in a date column can be parsed into timestamps."""
    parsed = pd.to_datetime(df[date_column], errors="coerce", format="mixed")
    invalid_mask = parsed.isna()
    invalid_count = int(invalid_mask.sum())

    rejected: List[Dict[str, Any]] = []
    if invalid_count > 0:
        bad_rows = df[invalid_mask]
        for _, row in bad_rows.iterrows():
            rejected.append({
                "dataset": dataset_name,
                "stage": "date_validation",
                "reason": f"Unparseable date value in column '{date_column}': '{row[date_column]}'",
                "data": row.to_dict(),
            })

    valid_df = df[~invalid_mask].copy()
    valid_df[date_column] = parsed[~invalid_mask]
    return valid_df, rejected


def validate_numeric_constraints(
    df: pd.DataFrame,
    dataset_name: str,
    positive_int_cols: List[str] | None = None,
    non_negative_numeric_cols: List[str] | None = None,
) -> Tuple[pd.DataFrame, List[Dict[str, Any]]]:
    """Enforces domain constraints:

    - Positive integers (> 0) for fields like `quantity`.
    - Non-negative numbers (>= 0) for fields like `price`, `stock`, `unit_price`.
    """
    positive_int_cols = positive_int_cols or []
    non_negative_numeric_cols = non_negative_numeric_cols or []

    rejected: List[Dict[str, Any]] = []
    invalid_row_indices: Set[int] = set()

    # Check positive integer columns
    for col in positive_int_cols:
        if col in df.columns:
            numeric_vals = pd.to_numeric(df[col], errors="coerce")
            bad_mask = numeric_vals.isna() | (numeric_vals <= 0)
            for idx in df[bad_mask].index:
                invalid_row_indices.add(idx)
                rejected.append({
                    "dataset": dataset_name,
                    "stage": "numeric_validation",
                    "reason": f"Field '{col}' must be an integer > 0; found '{df.loc[idx, col]}'",
                    "data": df.loc[idx].to_dict(),
                })

    # Check non-negative numeric columns
    for col in non_negative_numeric_cols:
        if col in df.columns:
            numeric_vals = pd.to_numeric(df[col], errors="coerce")
            bad_mask = numeric_vals.isna() | (numeric_vals < 0)
            for idx in df[bad_mask].index:
                if idx not in invalid_row_indices:
                    invalid_row_indices.add(idx)
                    rejected.append({
                        "dataset": dataset_name,
                        "stage": "numeric_validation",
                        "reason": f"Field '{col}' must be a numeric value >= 0; found '{df.loc[idx, col]}'",
                        "data": df.loc[idx].to_dict(),
                    })

    valid_df = df.drop(index=list(invalid_row_indices)).copy()
    return valid_df, rejected


def validate_foreign_keys(
    df: pd.DataFrame,
    fk_column: str,
    valid_pk_set: Set[Any],
    dataset_name: str,
    target_table_name: str,
) -> Tuple[pd.DataFrame, List[Dict[str, Any]]]:
    """Validates that foreign key references exist in the target parent table."""
    invalid_mask = ~df[fk_column].isin(valid_pk_set)
    orphan_count = int(invalid_mask.sum())

    rejected: List[Dict[str, Any]] = []
    if orphan_count > 0:
        bad_rows = df[invalid_mask]
        for _, row in bad_rows.iterrows():
            rejected.append({
                "dataset": dataset_name,
                "stage": "foreign_key_validation",
                "reason": (
                    f"Orphan record: Foreign key '{fk_column}'={row[fk_column]} "
                    f"does not exist in parent table '{target_table_name}'."
                ),
                "data": row.to_dict(),
            })

    valid_df = df[~invalid_mask].copy()
    return valid_df, rejected
