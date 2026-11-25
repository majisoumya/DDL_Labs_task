"""Transactional Data Ingestion Pipeline for InsightIQ AI."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models import Customer, Order, OrderItem, Product
from app.database.session import db_context
from app.data_processing.cleaner import clean_dataset
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

logger = logging.getLogger("insightiq.ingestion")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] [Ingestion] %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


@dataclass
class TableIngestionReport:
    """Summary metrics for a specific database entity."""
    table_name: str
    source_rows: int = 0
    valid_rows: int = 0
    rejected_rows: int = 0
    duplicate_rows: int = 0
    missing_values: int = 0
    inserted_records: int = 0
    skipped_existing: int = 0
    rejections: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class IngestionSummary:
    """Consolidated ingestion summary across all tables."""
    reports: Dict[str, TableIngestionReport] = field(default_factory=dict)
    all_rejections: List[Dict[str, Any]] = field(default_factory=list)
    success: bool = False
    error_message: Optional[str] = None

    @property
    def total_source_rows(self) -> int:
        return sum(r.source_rows for r in self.reports.values())

    @property
    def total_valid_rows(self) -> int:
        return sum(r.valid_rows for r in self.reports.values())

    @property
    def total_rejected_rows(self) -> int:
        return sum(r.rejected_rows for r in self.reports.values())

    @property
    def total_duplicate_rows(self) -> int:
        return sum(r.duplicate_rows for r in self.reports.values())

    @property
    def total_missing_values(self) -> int:
        return sum(r.missing_values for r in self.reports.values())

    @property
    def total_inserted_records(self) -> int:
        return sum(r.inserted_records for r in self.reports.values())

    @property
    def total_skipped_existing(self) -> int:
        return sum(r.skipped_existing for r in self.reports.values())

    def to_markdown(self) -> str:
        """Renders summary into GitHub-flavored Markdown."""
        lines = [
            "### Ingestion Execution Summary",
            "",
            f"- **Status:** {'SUCCESS' if self.success else 'FAILED'}",
            f"- **Total Source Records:** {self.total_source_rows:,}",
            f"- **Valid Records:** {self.total_valid_rows:,}",
            f"- **Inserted Records:** {self.total_inserted_records:,}",
            f"- **Skipped (Already Existing):** {self.total_skipped_existing:,}",
            f"- **Rejected Records:** {self.total_rejected_rows:,} (Duplicates: {self.total_duplicate_rows:,}, Missing/Invalid: {self.total_rejected_rows - self.total_duplicate_rows:,})",
            "",
            "| Entity Table | Source Rows | Valid Rows | Inserted | Skipped Existing | Duplicates | Missing/Invalid |",
            "| :--- | :---: | :---: | :---: | :---: | :---: | :---: |",
        ]
        for tbl, r in self.reports.items():
            lines.append(
                f"| `{tbl}` | {r.source_rows:,} | {r.valid_rows:,} | {r.inserted_records:,} | "
                f"{r.skipped_existing:,} | {r.duplicate_rows:,} | {r.rejected_rows - r.duplicate_rows:,} |"
            )
        lines.append("")

        if self.all_rejections:
            lines.extend([
                "**Sample Rejected Records & Audit Log:**",
                "",
            ])
            for rej in self.all_rejections[:10]:
                lines.append(f"- **[{rej.get('dataset')}]** {rej.get('stage')}: {rej.get('reason')}")
            if len(self.all_rejections) > 10:
                lines.append(f"- *... and {len(self.all_rejections) - 10} additional rejected records.*")
            lines.append("")

        return "\n".join(lines)


class IngestionPipeline:
    """Robust ETL pipeline ingesting raw CSV/Excel datasets into PostgreSQL/SQLAlchemy."""

    def __init__(self, data_dir: str | Path) -> None:
        self.data_dir = Path(data_dir)

    def load_csv(self, filename: str) -> pd.DataFrame:
        """Reads a CSV file from the raw data directory."""
        file_path = self.data_dir / filename
        if not file_path.exists():
            raise FileNotFoundError(f"Source file not found: {file_path}")
        return pd.read_csv(file_path)

    def run(self, session: Session) -> IngestionSummary:
        """Executes the full cleaning, validation, and ingestion pipeline atomically.

        Enforces referential integrity across the 4 entities:
        1. Customers
        2. Products
        3. Orders (FK -> Customers)
        4. OrderItems (FK -> Orders, Products)
        """
        summary = IngestionSummary()
        logger.info("Initiating ingestion pipeline from directory: %s", self.data_dir)

        try:
            # ----------------------------------------------------
            # 1. CUSTOMERS
            # ----------------------------------------------------
            cust_report = TableIngestionReport(table_name="customers")
            df_cust_raw = self.load_csv("customers.csv")
            cust_report.source_rows = len(df_cust_raw)

            df_cust_clean, cust_rejects, cust_dups, cust_nulls = clean_dataset(
                df_cust_raw,
                dataset_name="customers",
                required_columns=["customer_id", "name", "email", "city", "created_at"],
                primary_key="customer_id",
            )
            cust_report.duplicate_rows = cust_dups
            cust_report.missing_values = cust_nulls
            cust_report.rejections.extend(cust_rejects)

            # Date validation
            df_cust_valid, date_rejects = validate_dates(df_cust_clean, "created_at", "customers")
            cust_report.rejections.extend(date_rejects)
            cust_report.valid_rows = len(df_cust_valid)
            cust_report.rejected_rows = len(cust_report.rejections)

            # Query existing customer IDs for idempotency
            existing_cust_ids: Set[int] = set(session.scalars(select(Customer.customer_id)).all())
            cust_records = transform_customer_records(df_cust_valid)

            to_insert_custs = [r for r in cust_records if r["customer_id"] not in existing_cust_ids]
            cust_report.skipped_existing = len(cust_records) - len(to_insert_custs)

            if to_insert_custs:
                session.bulk_insert_mappings(Customer, to_insert_custs)
                session.flush()
            cust_report.inserted_records = len(to_insert_custs)
            summary.reports["customers"] = cust_report
            summary.all_rejections.extend(cust_report.rejections)

            # Current pool of valid customer IDs in DB
            all_valid_customer_ids: Set[int] = existing_cust_ids.union(
                {r["customer_id"] for r in to_insert_custs}
            )

            # ----------------------------------------------------
            # 2. PRODUCTS
            # ----------------------------------------------------
            prod_report = TableIngestionReport(table_name="products")
            df_prod_raw = self.load_csv("products.csv")
            prod_report.source_rows = len(df_prod_raw)

            df_prod_clean, prod_rejects, prod_dups, prod_nulls = clean_dataset(
                df_prod_raw,
                dataset_name="products",
                required_columns=["product_id", "product_name", "category", "price", "stock"],
                primary_key="product_id",
            )
            prod_report.duplicate_rows = prod_dups
            prod_report.missing_values = prod_nulls
            prod_report.rejections.extend(prod_rejects)

            # Numeric constraint validation (price >= 0, stock >= 0)
            df_prod_valid, prod_num_rejects = validate_numeric_constraints(
                df_prod_clean,
                dataset_name="products",
                non_negative_numeric_cols=["price", "stock"],
            )
            prod_report.rejections.extend(prod_num_rejects)
            prod_report.valid_rows = len(df_prod_valid)
            prod_report.rejected_rows = len(prod_report.rejections)

            existing_prod_ids: Set[int] = set(session.scalars(select(Product.product_id)).all())
            prod_records = transform_product_records(df_prod_valid)

            to_insert_prods = [r for r in prod_records if r["product_id"] not in existing_prod_ids]
            prod_report.skipped_existing = len(prod_records) - len(to_insert_prods)

            if to_insert_prods:
                session.bulk_insert_mappings(Product, to_insert_prods)
                session.flush()
            prod_report.inserted_records = len(to_insert_prods)
            summary.reports["products"] = prod_report
            summary.all_rejections.extend(prod_report.rejections)

            all_valid_product_ids: Set[int] = existing_prod_ids.union(
                {r["product_id"] for r in to_insert_prods}
            )

            # ----------------------------------------------------
            # 3. ORDERS
            # ----------------------------------------------------
            ord_report = TableIngestionReport(table_name="orders")
            df_ord_raw = self.load_csv("orders.csv")
            ord_report.source_rows = len(df_ord_raw)

            df_ord_clean, ord_rejects, ord_dups, ord_nulls = clean_dataset(
                df_ord_raw,
                dataset_name="orders",
                required_columns=["order_id", "customer_id", "order_date", "status"],
                primary_key="order_id",
            )
            ord_report.duplicate_rows = ord_dups
            ord_report.missing_values = ord_nulls
            ord_report.rejections.extend(ord_rejects)

            # Date validation
            df_ord_date_valid, ord_date_rejects = validate_dates(df_ord_clean, "order_date", "orders")
            ord_report.rejections.extend(ord_date_rejects)

            # Customer Foreign Key validation
            df_ord_valid, ord_fk_rejects = validate_foreign_keys(
                df_ord_date_valid,
                fk_column="customer_id",
                valid_pk_set=all_valid_customer_ids,
                dataset_name="orders",
                target_table_name="customers",
            )
            ord_report.rejections.extend(ord_fk_rejects)
            ord_report.valid_rows = len(df_ord_valid)
            ord_report.rejected_rows = len(ord_report.rejections)

            existing_order_ids: Set[int] = set(session.scalars(select(Order.order_id)).all())
            order_records = transform_order_records(df_ord_valid)

            to_insert_orders = [r for r in order_records if r["order_id"] not in existing_order_ids]
            ord_report.skipped_existing = len(order_records) - len(to_insert_orders)

            if to_insert_orders:
                session.bulk_insert_mappings(Order, to_insert_orders)
                session.flush()
            ord_report.inserted_records = len(to_insert_orders)
            summary.reports["orders"] = ord_report
            summary.all_rejections.extend(ord_report.rejections)

            all_valid_order_ids: Set[int] = existing_order_ids.union(
                {r["order_id"] for r in to_insert_orders}
            )

            # ----------------------------------------------------
            # 4. ORDER ITEMS
            # ----------------------------------------------------
            items_report = TableIngestionReport(table_name="order_items")
            df_items_raw = self.load_csv("order_items.csv")
            items_report.source_rows = len(df_items_raw)

            df_items_clean, items_rejects, items_dups, items_nulls = clean_dataset(
                df_items_raw,
                dataset_name="order_items",
                required_columns=["item_id", "order_id", "product_id", "quantity", "unit_price"],
                primary_key="item_id",
            )
            items_report.duplicate_rows = items_dups
            items_report.missing_values = items_nulls
            items_report.rejections.extend(items_rejects)

            # Numeric constraint validation (quantity > 0, unit_price >= 0)
            df_items_num_valid, items_num_rejects = validate_numeric_constraints(
                df_items_clean,
                dataset_name="order_items",
                positive_int_cols=["quantity"],
                non_negative_numeric_cols=["unit_price"],
            )
            items_report.rejections.extend(items_num_rejects)

            # Order FK validation
            df_items_ord_valid, items_ord_fk_rejects = validate_foreign_keys(
                df_items_num_valid,
                fk_column="order_id",
                valid_pk_set=all_valid_order_ids,
                dataset_name="order_items",
                target_table_name="orders",
            )
            items_report.rejections.extend(items_ord_fk_rejects)

            # Product FK validation
            df_items_valid, items_prod_fk_rejects = validate_foreign_keys(
                df_items_ord_valid,
                fk_column="product_id",
                valid_pk_set=all_valid_product_ids,
                dataset_name="order_items",
                target_table_name="products",
            )
            items_report.rejections.extend(items_prod_fk_rejects)
            items_report.valid_rows = len(df_items_valid)
            items_report.rejected_rows = len(items_report.rejections)

            existing_item_ids: Set[int] = set(session.scalars(select(OrderItem.item_id)).all())
            item_records = transform_order_item_records(df_items_valid)

            to_insert_items = [r for r in item_records if r["item_id"] not in existing_item_ids]
            items_report.skipped_existing = len(item_records) - len(to_insert_items)

            if to_insert_items:
                session.bulk_insert_mappings(OrderItem, to_insert_items)
                session.flush()
            items_report.inserted_records = len(to_insert_items)
            summary.reports["order_items"] = items_report
            summary.all_rejections.extend(items_report.rejections)

            summary.success = True
            logger.info(
                "Ingestion complete: %d records inserted, %d skipped existing, %d rejected.",
                summary.total_inserted_records,
                summary.total_skipped_existing,
                summary.total_rejected_rows,
            )

        except Exception as exc:
            summary.success = False
            summary.error_message = str(exc)
            logger.error("Ingestion failed with exception: %s", exc, exc_info=True)
            raise

        return summary
