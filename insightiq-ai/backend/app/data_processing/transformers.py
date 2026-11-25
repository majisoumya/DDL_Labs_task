"""Data Transformation and Type Conversion Module for InsightIQ AI."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List
import pandas as pd


def transform_customer_records(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """Converts cleaned customer DataFrame into records matching the Customer model."""
    records: List[Dict[str, Any]] = []
    for _, row in df.iterrows():
        created_val = row["created_at"]
        if isinstance(created_val, str):
            created_dt = pd.to_datetime(created_val).to_pydatetime()
        elif hasattr(created_val, "to_pydatetime"):
            created_dt = created_val.to_pydatetime()
        else:
            created_dt = created_val

        records.append({
            "customer_id": int(row["customer_id"]),
            "name": str(row["name"]).strip(),
            "email": str(row["email"]).strip().lower(),
            "city": str(row["city"]).strip(),
            "created_at": created_dt,
        })
    return records


def transform_product_records(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """Converts cleaned product DataFrame into records matching the Product model."""
    records: List[Dict[str, Any]] = []
    for _, row in df.iterrows():
        records.append({
            "product_id": int(row["product_id"]),
            "product_name": str(row["product_name"]).strip(),
            "category": str(row["category"]).strip(),
            "price": Decimal(str(round(float(row["price"]), 2))),
            "stock": int(row["stock"]),
        })
    return records


def transform_order_records(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """Converts cleaned order DataFrame into records matching the Order model."""
    records: List[Dict[str, Any]] = []
    for _, row in df.iterrows():
        order_val = row["order_date"]
        if isinstance(order_val, str):
            order_dt = pd.to_datetime(order_val).to_pydatetime()
        elif hasattr(order_val, "to_pydatetime"):
            order_dt = order_val.to_pydatetime()
        else:
            order_dt = order_val

        status_clean = str(row["status"]).strip().lower()

        records.append({
            "order_id": int(row["order_id"]),
            "customer_id": int(row["customer_id"]),
            "order_date": order_dt,
            "status": status_clean,
        })
    return records


def transform_order_item_records(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """Converts cleaned order items DataFrame into records matching the OrderItem model."""
    records: List[Dict[str, Any]] = []
    for _, row in df.iterrows():
        records.append({
            "item_id": int(row["item_id"]),
            "order_id": int(row["order_id"]),
            "product_id": int(row["product_id"]),
            "quantity": int(row["quantity"]),
            "unit_price": Decimal(str(round(float(row["unit_price"]), 2))),
        })
    return records
