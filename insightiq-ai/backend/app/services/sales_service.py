"""Sales Analytics Service for InsightIQ AI.

Calculates deterministic sales and revenue metrics from PostgreSQL / SQLAlchemy.
Applies business rules:
- Excludes cancelled and returned orders from revenue and order eligibility.
- Uses exact Decimal arithmetic for monetary values.
- Prevents division-by-zero errors.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional
from sqlalchemy import distinct, func, select
from sqlalchemy.orm import Session

from app.database.models import Order, OrderItem, Product

# Standard business exclusion for ineligible orders
INELIGIBLE_ORDER_STATUSES = ("cancelled", "returned")


def _get_month_expression(db: Session):
    """Returns a SQL expression to extract YYYY-MM formatted string across PostgreSQL and SQLite."""
    dialect_name = db.bind.dialect.name if db.bind else "sqlite"
    if dialect_name == "postgresql":
        return func.to_char(Order.order_date, "YYYY-MM")
    # Fallback to SQLite strftime
    return func.strftime("%Y-%m", Order.order_date)


def get_sales_metrics(
    db: Session,
    start_date: Optional[datetime | str] = None,
    end_date: Optional[datetime | str] = None,
) -> Dict[str, Any]:
    """Calculates total revenue, eligible orders count, and Average Order Value (AOV).

    Revenue = SUM(quantity * unit_price) for order items of eligible orders.
    Eligible Orders = COUNT(DISTINCT order_id) where status NOT IN ('cancelled', 'returned').
    AOV = Total Revenue / Eligible Orders (or 0 if orders == 0).
    """
    stmt = (
        select(
            func.coalesce(func.sum(OrderItem.quantity * OrderItem.unit_price), 0).label("revenue"),
            func.count(distinct(Order.order_id)).label("order_count"),
        )
        .join(OrderItem, Order.order_id == OrderItem.order_id)
        .where(Order.status.notin_(INELIGIBLE_ORDER_STATUSES))
    )

    if start_date:
        stmt = stmt.where(Order.order_date >= start_date)
    if end_date:
        stmt = stmt.where(Order.order_date <= end_date)

    row = db.execute(stmt).first()
    revenue_raw = row.revenue if row else 0
    orders_count = int(row.order_count) if row else 0

    total_revenue = Decimal(str(revenue_raw)).quantize(Decimal("0.01"))
    if orders_count > 0:
        aov = (total_revenue / Decimal(orders_count)).quantize(Decimal("0.01"))
    else:
        aov = Decimal("0.00")

    return {
        "total_revenue": total_revenue,
        "total_orders": orders_count,
        "aov": aov,
    }


def get_monthly_revenue(
    db: Session,
    start_date: Optional[datetime | str] = None,
    end_date: Optional[datetime | str] = None,
) -> List[Dict[str, Any]]:
    """Aggregates revenue, order volume, and units sold grouped chronologically by month (YYYY-MM)."""
    month_col = _get_month_expression(db).label("month")

    stmt = (
        select(
            month_col,
            func.coalesce(func.sum(OrderItem.quantity * OrderItem.unit_price), 0).label("revenue"),
            func.count(distinct(Order.order_id)).label("order_count"),
            func.coalesce(func.sum(OrderItem.quantity), 0).label("units_sold"),
        )
        .join(OrderItem, Order.order_id == OrderItem.order_id)
        .where(Order.status.notin_(INELIGIBLE_ORDER_STATUSES))
    )

    if start_date:
        stmt = stmt.where(Order.order_date >= start_date)
    if end_date:
        stmt = stmt.where(Order.order_date <= end_date)

    stmt = stmt.group_by(month_col).order_by(month_col.asc())
    rows = db.execute(stmt).all()

    result: List[Dict[str, Any]] = []
    for r in rows:
        result.append({
            "month": str(r.month),
            "revenue": Decimal(str(r.revenue)).quantize(Decimal("0.01")),
            "order_count": int(r.order_count),
            "units_sold": int(r.units_sold),
        })
    return result


def get_revenue_by_category(
    db: Session,
    start_date: Optional[datetime | str] = None,
    end_date: Optional[datetime | str] = None,
) -> List[Dict[str, Any]]:
    """Calculates revenue and units sold broken down by product category."""
    stmt = (
        select(
            Product.category,
            func.coalesce(func.sum(OrderItem.quantity * OrderItem.unit_price), 0).label("revenue"),
            func.count(distinct(Order.order_id)).label("order_count"),
            func.coalesce(func.sum(OrderItem.quantity), 0).label("units_sold"),
        )
        .join(OrderItem, Product.product_id == OrderItem.product_id)
        .join(Order, Order.order_id == OrderItem.order_id)
        .where(Order.status.notin_(INELIGIBLE_ORDER_STATUSES))
    )

    if start_date:
        stmt = stmt.where(Order.order_date >= start_date)
    if end_date:
        stmt = stmt.where(Order.order_date <= end_date)

    stmt = stmt.group_by(Product.category).order_by(func.sum(OrderItem.quantity * OrderItem.unit_price).desc())
    rows = db.execute(stmt).all()

    total_revenue_all = sum(Decimal(str(r.revenue)) for r in rows) if rows else Decimal("0.00")

    result: List[Dict[str, Any]] = []
    for r in rows:
        cat_rev = Decimal(str(r.revenue)).quantize(Decimal("0.01"))
        pct = round(float((cat_rev / total_revenue_all) * 100), 2) if total_revenue_all > 0 else 0.0
        result.append({
            "category": str(r.category),
            "revenue": cat_rev,
            "percentage": pct,
            "order_count": int(r.order_count),
            "units_sold": int(r.units_sold),
        })
    return result


def get_revenue_by_product(
    db: Session,
    limit: int = 10,
    start_date: Optional[datetime | str] = None,
    end_date: Optional[datetime | str] = None,
) -> List[Dict[str, Any]]:
    """Calculates top products ranked by total revenue."""
    stmt = (
        select(
            Product.product_id,
            Product.product_name,
            Product.category,
            func.coalesce(func.sum(OrderItem.quantity * OrderItem.unit_price), 0).label("revenue"),
            func.coalesce(func.sum(OrderItem.quantity), 0).label("units_sold"),
        )
        .join(OrderItem, Product.product_id == OrderItem.product_id)
        .join(Order, Order.order_id == OrderItem.order_id)
        .where(Order.status.notin_(INELIGIBLE_ORDER_STATUSES))
    )

    if start_date:
        stmt = stmt.where(Order.order_date >= start_date)
    if end_date:
        stmt = stmt.where(Order.order_date <= end_date)

    stmt = stmt.group_by(Product.product_id, Product.product_name, Product.category).order_by(
        func.sum(OrderItem.quantity * OrderItem.unit_price).desc()
    ).limit(limit)

    rows = db.execute(stmt).all()

    result: List[Dict[str, Any]] = []
    for r in rows:
        result.append({
            "product_id": int(r.product_id),
            "product_name": str(r.product_name),
            "category": str(r.category),
            "revenue": Decimal(str(r.revenue)).quantize(Decimal("0.01")),
            "units_sold": int(r.units_sold),
        })
    return result


def get_sales_growth(
    db: Session,
    current_start: datetime | str,
    current_end: datetime | str,
    previous_start: datetime | str,
    previous_end: datetime | str,
) -> Dict[str, Any]:
    """Compares sales metrics across two time periods and computes growth percentages."""
    curr = get_sales_metrics(db, start_date=current_start, end_date=current_end)
    prev = get_sales_metrics(db, start_date=previous_start, end_date=previous_end)

    # Growth helper
    def _pct_change(current_val: float, previous_val: float) -> Optional[float]:
        if previous_val == 0:
            return None if current_val == 0 else 100.0
        return round(((current_val - previous_val) / previous_val) * 100, 2)

    rev_curr = float(curr["total_revenue"])
    rev_prev = float(prev["total_revenue"])
    ord_curr = curr["total_orders"]
    ord_prev = prev["total_orders"]
    aov_curr = float(curr["aov"])
    aov_prev = float(prev["aov"])

    return {
        "current_period": {
            "start": str(current_start),
            "end": str(current_end),
            "revenue": curr["total_revenue"],
            "orders": curr["total_orders"],
            "aov": curr["aov"],
        },
        "previous_period": {
            "start": str(previous_start),
            "end": str(previous_end),
            "revenue": prev["total_revenue"],
            "orders": prev["total_orders"],
            "aov": prev["aov"],
        },
        "revenue_growth_pct": _pct_change(rev_curr, rev_prev),
        "orders_growth_pct": _pct_change(ord_curr, ord_prev),
        "aov_growth_pct": _pct_change(aov_curr, aov_prev),
    }
