"""Data Profiler Module for InsightIQ AI.

Provides comprehensive inspection and profiling of CSV and Excel datasets:
- Schema detection (rows, columns, dtypes)
- Missing and duplicate record analysis
- Numeric integrity (negatives, non-positives)
- Date format and range verification
- Primary key and Foreign key relationship inference
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd


@dataclass
class ColumnProfile:
    """Statistical and structural profile of an individual dataframe column."""
    name: str
    dtype: str
    inferred_type: str
    total_count: int
    null_count: int
    null_percentage: float
    unique_count: int
    uniqueness_ratio: float
    is_candidate_pk: bool
    sample_values: List[Any]
    numeric_stats: Optional[Dict[str, Any]] = None
    date_stats: Optional[Dict[str, Any]] = None


@dataclass
class DatasetProfile:
    """Complete profile of a single dataset file."""
    dataset_name: str
    file_path: str
    file_type: str
    file_size_bytes: int
    row_count: int
    column_count: int
    duplicate_rows_count: int
    duplicate_rows_percentage: float
    columns: Dict[str, ColumnProfile] = field(default_factory=dict)
    candidate_primary_keys: List[str] = field(default_factory=list)
    data_quality_issues: List[str] = field(default_factory=list)


@dataclass
class RelationshipCandidate:
    """Inferred referential relationship between two datasets."""
    from_dataset: str
    from_column: str
    to_dataset: str
    to_column: str
    matched_ratio: float  # Percentage of foreign values existing in target primary key
    is_valid_fk: bool
    notes: str


@dataclass
class SystemProfile:
    """Global profiling result across all scanned datasets."""
    scanned_directory: str
    datasets: Dict[str, DatasetProfile] = field(default_factory=dict)
    relationships: List[RelationshipCandidate] = field(default_factory=list)
    schema_comparison: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    summary_notes: List[str] = field(default_factory=list)


class DataProfiler:
    """Profiles tabular datasets (CSV / Excel) for business intelligence ingestion."""

    EXPECTED_SCHEMA = {
        "customers": {
            "required_columns": ["customer_id", "name", "email", "city", "created_at"],
            "pk": "customer_id",
        },
        "products": {
            "required_columns": ["product_id", "product_name", "category", "price", "stock"],
            "pk": "product_id",
        },
        "orders": {
            "required_columns": ["order_id", "customer_id", "order_date", "status"],
            "pk": "order_id",
        },
        "order_items": {
            "required_columns": ["item_id", "order_id", "product_id", "quantity", "unit_price"],
            "pk": "item_id",
        },
    }

    def __init__(self, target_dir: Optional[str | Path] = None) -> None:
        self.target_dir = Path(target_dir) if target_dir else None

    def scan_files(self, directory: Optional[str | Path] = None) -> List[Path]:
        """Scans directory for supported tabular files (.csv, .xlsx, .xls)."""
        scan_path = Path(directory or self.target_dir or ".")
        if not scan_path.exists():
            return []

        supported_extensions = {".csv", ".xlsx", ".xls"}
        found_files: List[Path] = []
        for file in scan_path.rglob("*"):
            if file.is_file() and file.suffix.lower() in supported_extensions:
                found_files.append(file)
        return sorted(found_files)

    def load_dataset(self, file_path: str | Path) -> pd.DataFrame:
        """Loads CSV or Excel file into a pandas DataFrame."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        ext = path.suffix.lower()
        if ext == ".csv":
            return pd.read_csv(path)
        elif ext in {".xlsx", ".xls"}:
            return pd.read_excel(path)
        else:
            raise ValueError(f"Unsupported file format: {ext}")

    def profile_dataframe(self, df: pd.DataFrame, dataset_name: str, file_path: str = "") -> DatasetProfile:
        """Profiles a single DataFrame to extract structural and statistical characteristics."""
        row_count = len(df)
        column_count = len(df.columns)
        duplicate_count = int(df.duplicated().sum())
        duplicate_pct = round((duplicate_count / row_count * 100), 2) if row_count > 0 else 0.0

        file_size = 0
        file_ext = "dataframe"
        if file_path and os.path.exists(file_path):
            file_size = os.path.getsize(file_path)
            file_ext = Path(file_path).suffix.lower().replace(".", "")

        dataset_profile = DatasetProfile(
            dataset_name=dataset_name,
            file_path=str(file_path),
            file_type=file_ext,
            file_size_bytes=file_size,
            row_count=row_count,
            column_count=column_count,
            duplicate_rows_count=duplicate_count,
            duplicate_rows_percentage=duplicate_pct,
        )

        candidate_pks: List[str] = []
        issues: List[str] = []

        if duplicate_count > 0:
            issues.append(f"Found {duplicate_count} ({duplicate_pct}%) completely duplicate row(s).")

        for col_name in df.columns:
            series = df[col_name]
            col_profile = self._profile_column(series, col_name, row_count)
            dataset_profile.columns[col_name] = col_profile

            if col_profile.is_candidate_pk:
                candidate_pks.append(col_name)

            # Flag null values
            if col_profile.null_count > 0:
                issues.append(
                    f"Column '{col_name}' contains {col_profile.null_count} nulls "
                    f"({col_profile.null_percentage}%)."
                )

            # Flag invalid numeric fields (e.g. negative price or quantity)
            if col_profile.numeric_stats:
                num_stats = col_profile.numeric_stats
                if "price" in col_name.lower() or "amount" in col_name.lower():
                    if num_stats["negative_count"] > 0:
                        issues.append(
                            f"Column '{col_name}' has {num_stats['negative_count']} negative values "
                            f"(min: {num_stats['min']}). Prices must be non-negative."
                        )
                if "quantity" in col_name.lower() or "qty" in col_name.lower():
                    if num_stats["non_positive_count"] > 0:
                        issues.append(
                            f"Column '{col_name}' has {num_stats['non_positive_count']} non-positive values "
                            f"(min: {num_stats['min']}). Quantities should be >= 1."
                        )

            # Flag date parsing issues
            if col_profile.date_stats and col_profile.date_stats.get("unparseable_count", 0) > 0:
                issues.append(
                    f"Column '{col_name}' has {col_profile.date_stats['unparseable_count']} "
                    f"unparseable date strings."
                )

        dataset_profile.candidate_primary_keys = candidate_pks
        dataset_profile.data_quality_issues = issues
        return dataset_profile

    def _profile_column(self, series: pd.Series, col_name: str, total_rows: int) -> ColumnProfile:
        """Profiles an individual column for types, nulls, uniqueness, and domain constraints."""
        null_count = int(series.isna().sum())
        null_pct = round((null_count / total_rows * 100), 2) if total_rows > 0 else 0.0

        non_null_series = series.dropna()
        unique_count = int(non_null_series.nunique())
        uniqueness_ratio = round((unique_count / total_rows), 4) if total_rows > 0 else 0.0

        is_pk = (null_count == 0) and (unique_count == total_rows) and (total_rows > 0)

        # Inferred semantic type
        inferred_type = self._infer_semantic_type(series, col_name)

        # Sample values (up to 3 non-null samples)
        sample_vals = non_null_series.head(3).tolist()

        numeric_stats = None
        date_stats = None

        if inferred_type in {"integer", "float"} or pd.api.types.is_numeric_dtype(series):
            numeric_stats = self._calculate_numeric_stats(non_null_series)

        if inferred_type == "datetime" or "date" in col_name.lower() or "created_at" in col_name.lower():
            date_stats = self._inspect_date_column(non_null_series)

        return ColumnProfile(
            name=col_name,
            dtype=str(series.dtype),
            inferred_type=inferred_type,
            total_count=total_rows,
            null_count=null_count,
            null_percentage=null_pct,
            unique_count=unique_count,
            uniqueness_ratio=uniqueness_ratio,
            is_candidate_pk=is_pk,
            sample_values=sample_vals,
            numeric_stats=numeric_stats,
            date_stats=date_stats,
        )

    def _infer_semantic_type(self, series: pd.Series, col_name: str) -> str:
        """Infers the high-level semantic type of a series."""
        if pd.api.types.is_bool_dtype(series):
            return "boolean"
        if pd.api.types.is_integer_dtype(series):
            return "integer"
        if pd.api.types.is_float_dtype(series):
            return "float"
        if pd.api.types.is_datetime64_any_dtype(series):
            return "datetime"

        # If object/string, attempt heuristic checks
        non_null = series.dropna().astype(str).str.strip()
        if non_null.empty:
            return "empty"

        if "date" in col_name.lower() or "created_at" in col_name.lower() or "time" in col_name.lower():
            try:
                pd.to_datetime(non_null.iloc[:20], errors="raise")
                return "datetime"
            except (ValueError, TypeError):
                pass

        # Check boolean strings
        lower_vals = set(non_null.str.lower().unique())
        if lower_vals.issubset({"true", "false", "0", "1", "yes", "no"}):
            return "boolean"

        # Check numeric strings
        try:
            pd.to_numeric(non_null.iloc[:50], errors="raise")
            if "." in non_null.iloc[0]:
                return "float"
            return "integer"
        except (ValueError, TypeError):
            pass

        return "string"

    def _calculate_numeric_stats(self, non_null_series: pd.Series) -> Dict[str, Any]:
        """Calculates descriptive numeric statistics and invalidity flags."""
        numeric_series = pd.to_numeric(non_null_series, errors="coerce").dropna()
        if numeric_series.empty:
            return {"negative_count": 0, "non_positive_count": 0, "min": None, "max": None, "mean": None}

        neg_count = int((numeric_series < 0).sum())
        non_pos_count = int((numeric_series <= 0).sum())
        return {
            "min": float(numeric_series.min()),
            "max": float(numeric_series.max()),
            "mean": round(float(numeric_series.mean()), 2),
            "negative_count": neg_count,
            "non_positive_count": non_pos_count,
        }

    def _inspect_date_column(self, non_null_series: pd.Series) -> Dict[str, Any]:
        """Validates date format compliance and range."""
        parsed = pd.to_datetime(non_null_series, errors="coerce")
        unparseable = int(parsed.isna().sum())
        valid_dates = parsed.dropna()

        min_date_str = str(valid_dates.min()) if not valid_dates.empty else None
        max_date_str = str(valid_dates.max()) if not valid_dates.empty else None

        # Sample format inspection (e.g. ISO 8601 vs US style)
        sample = str(non_null_series.iloc[0]) if not non_null_series.empty else ""
        detected_format = "ISO/Standard" if "-" in sample else ("US slash" if "/" in sample else "Unknown")

        return {
            "min_date": min_date_str,
            "max_date": max_date_str,
            "unparseable_count": unparseable,
            "detected_format": detected_format,
        }

    def detect_relationships(self, datasets: Dict[str, pd.DataFrame]) -> List[RelationshipCandidate]:
        """Infers foreign-key relationships across multiple loaded datasets."""
        relationships: List[RelationshipCandidate] = []

        # Standard foreign-key naming patterns
        fk_mappings = [
            ("orders", "customer_id", "customers", "customer_id"),
            ("order_items", "order_id", "orders", "order_id"),
            ("order_items", "product_id", "products", "product_id"),
        ]

        # Check explicit expected mappings
        for from_tbl, from_col, to_tbl, to_col in fk_mappings:
            if from_tbl in datasets and to_tbl in datasets:
                df_from = datasets[from_tbl]
                df_to = datasets[to_tbl]

                if from_col in df_from.columns and to_col in df_to.columns:
                    fk_vals = set(df_from[from_col].dropna().unique())
                    pk_vals = set(df_to[to_col].dropna().unique())

                    if fk_vals:
                        intersection = fk_vals.intersection(pk_vals)
                        ratio = round(len(intersection) / len(fk_vals), 4)
                        is_valid = ratio >= 0.95  # At least 95% referential integrity
                        notes = (
                            f"{len(intersection)}/{len(fk_vals)} distinct foreign keys exist in parent table."
                            if is_valid
                            else f"Integrity warning: {len(fk_vals) - len(intersection)} orphan foreign keys."
                        )
                        relationships.append(
                            RelationshipCandidate(
                                from_dataset=from_tbl,
                                from_column=from_col,
                                to_dataset=to_tbl,
                                to_column=to_col,
                                matched_ratio=ratio,
                                is_valid_fk=is_valid,
                                notes=notes,
                            )
                        )

        # Heuristic check for other matching column names ending in _id
        existing_pairs = {(r.from_dataset, r.from_column, r.to_dataset, r.to_column) for r in relationships}
        for name_a, df_a in datasets.items():
            for name_b, df_b in datasets.items():
                if name_a == name_b:
                    continue
                for col_a in df_a.columns:
                    if col_a.endswith("_id") and col_a in df_b.columns:
                        pair = (name_a, col_a, name_b, col_a)
                        if pair not in existing_pairs and (pair[2], pair[3], pair[0], pair[1]) not in existing_pairs:
                            vals_a = set(df_a[col_a].dropna().unique())
                            vals_b = set(df_b[col_a].dropna().unique())
                            if vals_a and vals_b:
                                inter = vals_a.intersection(vals_b)
                                ratio_a_in_b = len(inter) / len(vals_a)
                                if ratio_a_in_b >= 0.8:
                                    relationships.append(
                                        RelationshipCandidate(
                                            from_dataset=name_a,
                                            from_column=col_a,
                                            to_dataset=name_b,
                                            to_column=col_a,
                                            matched_ratio=round(ratio_a_in_b, 4),
                                            is_valid_fk=ratio_a_in_b >= 0.95,
                                            notes=f"Heuristic match: {round(ratio_a_in_b*100, 1)}% values matched.",
                                        )
                                    )
                                    existing_pairs.add(pair)

        return relationships

    def compare_against_target_schema(self, datasets: Dict[str, pd.DataFrame]) -> Dict[str, Dict[str, Any]]:
        """Compares available dataset schemas against the target InsightIQ AI database schema."""
        comparison_results: Dict[str, Dict[str, Any]] = {}

        for expected_table, spec in self.EXPECTED_SCHEMA.items():
            expected_cols = spec["required_columns"]
            pk_col = spec["pk"]

            # Match exact or case-insensitive / stripped names
            matched_dataset_key = None
            for key in datasets.keys():
                clean_key = key.lower().replace(".csv", "").replace(".xlsx", "").replace(".xls", "").strip()
                if clean_key == expected_table:
                    matched_dataset_key = key
                    break

            if matched_dataset_key is None:
                comparison_results[expected_table] = {
                    "status": "MISSING",
                    "dataset_found": None,
                    "missing_columns": expected_cols,
                    "extra_columns": [],
                    "pk_present": False,
                }
            else:
                actual_cols = list(datasets[matched_dataset_key].columns)
                missing = [col for col in expected_cols if col not in actual_cols]
                extra = [col for col in actual_cols if col not in expected_cols]
                pk_present = pk_col in actual_cols

                comparison_results[expected_table] = {
                    "status": "MATCHED" if not missing else "PARTIAL",
                    "dataset_found": matched_dataset_key,
                    "missing_columns": missing,
                    "extra_columns": extra,
                    "pk_present": pk_present,
                }

        return comparison_results

    def profile_all(self, directory: Optional[str | Path] = None) -> SystemProfile:
        """Executes full profiling pipeline over a directory."""
        scan_dir = Path(directory or self.target_dir or ".")
        files = self.scan_files(scan_dir)

        system_profile = SystemProfile(scanned_directory=str(scan_dir))

        if not files:
            system_profile.summary_notes.append(
                f"No tabular datasets (.csv, .xlsx, .xls) found in directory: {scan_dir}."
            )
            return system_profile

        loaded_dfs: Dict[str, pd.DataFrame] = {}

        for file in files:
            dataset_name = file.stem
            try:
                df = self.load_dataset(file)
                loaded_dfs[dataset_name] = df
                profile = self.profile_dataframe(df, dataset_name=dataset_name, file_path=str(file))
                system_profile.datasets[dataset_name] = profile
            except Exception as exc:
                system_profile.summary_notes.append(f"Failed to load {file.name}: {exc}")

        # Relationships and target schema comparison
        system_profile.relationships = self.detect_relationships(loaded_dfs)
        system_profile.schema_comparison = self.compare_against_target_schema(loaded_dfs)

        return system_profile
