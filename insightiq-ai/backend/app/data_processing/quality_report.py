"""Data Quality Report Generator for InsightIQ AI.

Produces a GitHub-flavored Markdown document documenting:
- File inventories and metrics
- Data types, missing values, duplicates, and invalid numbers
- Date parsing and formatting
- Candidate primary keys and referential relationships
- Target schema comparison and remediation suggestions
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Optional

from .profiler import SystemProfile


def generate_quality_report(profile: SystemProfile) -> str:
    """Renders a comprehensive Markdown Data Quality Report from a SystemProfile."""
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    md: list[str] = [
        "# InsightIQ AI — Dataset Inspection & Data Quality Report",
        "",
        f"> **Generated at:** {now_str}  ",
        f"> **Scanned Directory:** `{profile.scanned_directory}`  ",
        f"> **Total Datasets Analyzed:** {len(profile.datasets)}",
        "",
        "---",
        "",
        "## 1. Executive Summary",
        "",
    ]

    if not profile.datasets:
        md.extend([
            "> [!WARNING]",
            "> **No raw datasets were found in the scanned directory.**  ",
            "> In accordance with the project specification, a **Synthetic Data Strategy** has been activated to generate realistic, production-grade e-commerce retail data matching the proposed database schema.",
            "",
            "### Synthetic Data Strategy Overview",
            "1. **Entity Generation:**",
            "   - **`customers.csv`:** 100+ realistic retail customers across major cities with account creation timestamps.",
            "   - **`products.csv`:** 30 catalog items across 5 retail categories (Electronics, Apparel, Home & Kitchen, Books, Sports) with realistic unit prices and stock levels.",
            "   - **`orders.csv`:** 500+ transactional orders spanning multiple fiscal months (enabling month-over-month trend analysis and revenue drop investigations) with realistic statuses (`completed`, `pending`, `cancelled`, `returned`).",
            "   - **`order_items.csv`:** 1,200+ line items with integer quantities and matching unit prices.",
            "2. **Controlled Data Quality Edge Cases:**",
            "   - Intentional test cases (e.g., whitespace in names, a duplicate row, a cancelled order, an edge case date) to validate downstream cleaning in Phase 4.",
            "",
            "---",
        ])
    else:
        total_rows = sum(d.row_count for d in profile.datasets.values())
        total_issues = sum(len(d.data_quality_issues) for d in profile.datasets.values())

        status_alert = "> [!NOTE]" if total_issues == 0 else "> [!IMPORTANT]"
        md.extend([
            status_alert,
            f"> Found **{len(profile.datasets)} dataset(s)** comprising **{total_rows:,} total rows** across the directory.",
            f"> Identified **{total_issues} data quality issue(s)** requiring handling during ETL ingestion.",
            "",
        ])

    # Table of Datasets
    if profile.datasets:
        md.extend([
            "## 2. Dataset Inventory",
            "",
            "| Dataset Name | File Format | File Size | Row Count | Columns | Duplicates (%) | Candidate PK(s) |",
            "| :--- | :---: | :---: | :---: | :---: | :---: | :--- |",
        ])
        for name, d in profile.datasets.items():
            pks = ", ".join(f"`{k}`" for k in d.candidate_primary_keys) or "*None*"
            size_kb = f"{round(d.file_size_bytes / 1024, 1)} KB" if d.file_size_bytes else "In-Memory"
            md.append(
                f"| **`{name}`** | {d.file_type.upper()} | {size_kb} | {d.row_count:,} | "
                f"{d.column_count} | {d.duplicate_rows_count} ({d.duplicate_rows_percentage}%) | {pks} |"
            )
        md.append("")

        # Detailed Profiles per Dataset
        md.extend([
            "---",
            "",
            "## 3. Detailed Column Profiles",
            "",
        ])

        for name, d in profile.datasets.items():
            md.extend([
                f"### 3.{list(profile.datasets.keys()).index(name) + 1} Dataset: `{name}`",
                f"- **Source Path:** `{d.file_path}`",
                f"- **Dimensions:** {d.row_count:,} rows × {d.column_count} columns",
                f"- **Duplicate Rows:** {d.duplicate_rows_count} ({d.duplicate_rows_percentage}%)",
                "",
                "| Column Name | Raw Dtype | Inferred Type | Null Count | Null % | Unique | PK Candidate? | Sample Values |",
                "| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |",
            ])

            for col_name, c in d.columns.items():
                samples = ", ".join(str(s) for s in c.sample_values) if c.sample_values else "*empty*"
                if len(samples) > 35:
                    samples = samples[:32] + "..."
                pk_badge = "Yes" if c.is_candidate_pk else "No"
                md.append(
                    f"| `{col_name}` | `{c.dtype}` | `{c.inferred_type}` | {c.null_count} | "
                    f"{c.null_percentage}% | {c.unique_count} | {pk_badge} | `{samples}` |"
                )
            md.append("")

            # Numeric Details if any
            numeric_cols = [c for c in d.columns.values() if c.numeric_stats is not None]
            if numeric_cols:
                md.extend([
                    "**Numeric Distribution & Validation:**",
                    "",
                    "| Numeric Column | Min | Max | Mean | Negative Count | Non-Positive (<=0) Count |",
                    "| :--- | :---: | :---: | :---: | :---: | :---: |",
                ])
                for nc in numeric_cols:
                    ns = nc.numeric_stats or {}
                    md.append(
                        f"| `{nc.name}` | {ns.get('min')} | {ns.get('max')} | {ns.get('mean')} | "
                        f"{ns.get('negative_count')} | {ns.get('non_positive_count')} |"
                    )
                md.append("")

            # Date Details if any
            date_cols = [c for c in d.columns.values() if c.date_stats is not None]
            if date_cols:
                md.extend([
                    "**Temporal Analysis & Formatting:**",
                    "",
                    "| Date Column | Earliest Date | Latest Date | Unparseable Count | Format Style |",
                    "| :--- | :---: | :---: | :---: | :---: |",
                ])
                for dc in date_cols:
                    ds = dc.date_stats or {}
                    md.append(
                        f"| `{dc.name}` | `{ds.get('min_date')}` | `{ds.get('max_date')}` | "
                        f"{ds.get('unparseable_count')} | {ds.get('detected_format')} |"
                    )
                md.append("")

            # Issues for this dataset
            if d.data_quality_issues:
                md.extend([
                    "**Identified Data Quality Warnings:**",
                    "",
                ])
                for issue in d.data_quality_issues:
                    md.append(f"- ⚠️ {issue}")
                md.append("")

    # Section 4: Target Schema Comparison
    md.extend([
        "---",
        "",
        "## 4. Target Schema Comparison",
        "",
        "Comparison against the required InsightIQ AI PostgreSQL database schema:",
        "",
        "| Target Table | Status | Matched File | Missing Columns | Extra Columns | PK Present |",
        "| :--- | :---: | :---: | :--- | :--- | :---: |",
    ])

    for target_table, comp in profile.schema_comparison.items():
        missing_str = ", ".join(f"`{c}`" for c in comp["missing_columns"]) if comp["missing_columns"] else "*None*"
        extra_str = ", ".join(f"`{c}`" for c in comp["extra_columns"]) if comp["extra_columns"] else "*None*"
        pk_str = "Yes" if comp["pk_present"] else "No"
        status_badge = f"**{comp['status']}**"
        dataset_str = f"`{comp['dataset_found']}`" if comp["dataset_found"] else "*Missing*"

        md.append(
            f"| `{target_table}` | {status_badge} | {dataset_str} | {missing_str} | {extra_str} | {pk_str} |"
        )
    md.append("")

    # Section 5: Referential Integrity & Inferred Relationships
    md.extend([
        "---",
        "",
        "## 5. Inferred Foreign Key Relationships",
        "",
    ])

    if profile.relationships:
        md.extend([
            "| Origin Table & Column | Target Table & Column | Match Ratio | Referential Status | Notes |",
            "| :--- | :--- | :---: | :---: | :--- |",
        ])
        for rel in profile.relationships:
            status_text = "VALID FK" if rel.is_valid_fk else "INTEGRITY WARNING"
            md.append(
                f"| `{rel.from_dataset}.{rel.from_column}` | `{rel.to_dataset}.{rel.to_column}` | "
                f"{round(rel.matched_ratio * 100, 1)}% | **{status_text}** | {rel.notes} |"
            )
        md.append("")
    else:
        md.extend([
            "_No foreign key relationships detected._",
            "",
        ])

    # Section 6: Actionable Recommendations for Phase 4 (Cleaning and Ingestion)
    md.extend([
        "---",
        "",
        "## 6. Recommendations for Data Cleaning & Ingestion (Phase 4)",
        "",
        "1. **Deduplication:** Ensure ingestion pipelines implement `ON CONFLICT DO NOTHING` or upsert patterns to drop duplicate rows gracefully.",
        "2. **Whitespace Trimming:** Strip leading/trailing whitespaces across all string fields (e.g. `name`, `city`, `category`, `status`).",
        "3. **Null Handling:** Reject orders or line items lacking valid customer or product foreign keys; log dropped records in an ingestion audit log.",
        "4. **Status Normalization:** Normalize order status strings to lowercase (`completed`, `cancelled`, `pending`, `returned`) to guarantee accurate revenue aggregation.",
        "5. **Numeric Precision:** Enforce `Decimal` / PostgreSQL `NUMERIC(12, 2)` for prices to prevent floating-point rounding errors in AOV and revenue metrics.",
        "",
    ])

    return "\n".join(md)


def save_quality_report(profile: SystemProfile, output_path: str | Path) -> Path:
    """Generates and writes the Markdown data quality report to disk."""
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    report_text = generate_quality_report(profile)
    out.write_text(report_text, encoding="utf-8")
    return out
