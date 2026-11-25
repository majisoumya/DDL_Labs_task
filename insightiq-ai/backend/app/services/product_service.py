"""Product Analytics Service for InsightIQ AI.

Provides catalog performance, top-sellers, revenue leaders, and low-performing product analysis.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional
from sqlalchemy import distinct, func, select
from sqlalchemy.orm import Session

from app.database.models import Order, OrderItem, Product
from app.services.sales_service import INELIGIBLE_ORDER_STATUSES, get_revenue_by_category


def get_top_selling_products(
    db: Session,
    limit: int = 10,
    start_date: Optional[datetime | str] = None,
    end_date: Optional[datetime | str] = None,
) -> List[Dict[str, Any]]:
    """Retrieves top products ranked by total unit volume sold on eligible orders."""
    stmt = (
        select(
            Product.product_id,
            Product.product_name,
            Product.category,
            func.coalesce(func.sum(OrderItem.quantity), 0).label("units_sold"),
            func.coalesce(func.sum(OrderItem.quantity * OrderItem.unit_price), 0).label("revenue"),
            Product.stock,
        )
        .join(OrderItem, Product.product_id == OrderItem.product_id)
        .join(Order, Order.order_id == OrderItem.order_id)
        .where(Order.status.notin_(INELIGIBLE_ORDER_STATUSES))
    )

    if start_date:
        stmt = stmt.where(Order.order_date >= start_date)
    if end_date:
        stmt = stmt.where(Order.order_date <= end_date)

    stmt = stmt.group_by(
        Product.product_id, Product.product_name, Product.category, Product.stock
    ).order_by(func.sum(OrderItem.quantity).desc()).limit(limit)

    rows = db.execute(stmt).all()
    result: List[Dict[str, Any]] = []
    for r in rows:
        result.append({
            "product_id": int(r.product_id),
            "product_name": str(r.product_name),
            "category": str(r.category),
            "units_sold": int(r.units_sold),
            "revenue": Decimal(str(r.revenue)).quantize(Decimal("0.01")),
            "stock": int(r.stock),
        })
    return result


def get_highest_revenue_products(
    db: Session,
    limit: int = 10,
    start_date: Optional[datetime | str] = None,
    end_date: Optional[datetime | str] = None,
) -> List[Dict[str, Any]]:
    """Retrieves top products ranked by total revenue generated."""
    stmt = (
        select(
            Product.product_id,
            Product.product_name,
            Product.category,
            func.coalesce(func.sum(OrderItem.quantity * OrderItem.unit_price), 0).label("revenue"),
            func.coalesce(func.sum(OrderItem.quantity), 0).label("units_sold"),
            Product.stock,
        )
        .join(OrderItem, Product.product_id == OrderItem.product_id)
        .join(Order, Order.order_id == OrderItem.order_id)
        .where(Order.status.notin_(INELIGIBLE_ORDER_STATUSES))
    )

    if start_date:
        stmt = stmt.where(Order.order_date >= start_date)
    if end_date:
        stmt = stmt.where(Order.order_date <= end_date)

    stmt = stmt.group_by(
        Product.product_id, Product.product_name, Product.category, Product.stock
    ).order_by(func.sum(OrderItem.quantity * OrderItem.unit_price).desc()).limit(limit)

    rows = db.execute(stmt).all()
    result: List[Dict[str, Any]] = []
    for r in rows:
        result.append({
            "product_id": int(r.product_id),
            "product_name": str(r.product_name),
            "category": str(r.category),
            "revenue": Decimal(str(r.revenue)).quantize(Decimal("0.01")),
            "units_sold": int(r.units_sold),
            "stock": int(r.stock),
        })
    return result


def get_low_performing_products(
    db: Session,
    limit: int = 10,
    threshold_revenue: Optional[Decimal | float] = None,
    start_date: Optional[datetime | str] = None,
    end_date: Optional[datetime | str] = None,
) -> List[Dict[str, Any]]:
    """Identifies lowest-performing catalog items by revenue (including zero-sales products)."""
    # Outer join to capture products with 0 sales
    subq = (
        select(
            OrderItem.product_id,
            func.sum(OrderItem.quantity * OrderItem.unit_price).label("sales_rev"),
            func.sum(OrderItem.quantity).label("units_sold"),
        )
        .join(Order, Order.order_id == OrderItem.order_id)
        .where(Order.status.notin_(INELIGIBLE_ORDER_STATUSES))
    )
    if start_date:
        subq = subq.where(Order.order_date >= start_date)
    if end_date:
        subq = subq.where(Order.order_date <= end_date)

    subq = subq.group_by(OrderItem.product_id).subquery()

    stmt = (
        select(
            Product.product_id,
            Product.product_name,
            Product.category,
            func.coalesce(subq.c.sales_rev, 0).label("revenue"),
            func.coalesce(subq.c.units_sold, 0).label("units_sold"),
            Product.stock,
        )
        .outerjoin(subq, Product.product_id == subq.c.product_id)
    )

    if threshold_revenue is not None:
        stmt = stmt.where(func.coalesce(subq.c.sales_rev, 0) <= threshold_revenue)

    stmt = stmt.order_by(
        func.coalesce(subq.c.sales_rev, 0).asc(),
        func.coalesce(subq.c.units_sold, 0).asc(),
        Product.product_id.asc(),
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
            "stock": int(r.stock),
        })
    return result


def get_product_sales_quantity(
    db: Session,
    product_id: int,
    start_date: Optional[datetime | str] = None,
    end_date: Optional[datetime | str] = None,
) -> Dict[str, Any]:
    """Retrieves specific sales and volume metrics for an individual product."""
    product = db.scalar(select(Product).filter_by(product_id=product_id))
    if not product:
        return {
            "product_id": product_id,
            "product_name": "Unknown",
            "category": "Unknown",
            "units_sold": 0,
            "revenue": Decimal("0.00"),
            "order_count": 0,
        }

    stmt = (
        select(
            func.coalesce(func.sum(OrderItem.quantity), 0).label("units_sold"),
            func.coalesce(func.sum(OrderItem.quantity * OrderItem.unit_price), 0).label("revenue"),
            func.count(distinct(Order.order_id)).label("order_count"),
        )
        .join(Order, Order.order_id == OrderItem.order_id)
        .where(
            OrderItem.product_id == product_id,
            Order.status.notin_(INELIGIBLE_ORDER_STATUSES),
        )
    )

    if start_date:
        stmt = stmt.where(Order.order_date >= start_date)
    if end_date:
        stmt = stmt.where(Order.order_date <= end_date)

    row = db.execute(stmt).first()
    return {
        "product_id": product.product_id,
        "product_name": product.product_name,
        "category": product.category,
        "units_sold": int(row.units_sold) if row else 0,
        "revenue": Decimal(str(row.revenue if row else 0)).quantize(Decimal("0.01")),
        "order_count": int(row.order_count) if row else 0,
    }


def get_product_category_breakdown(
    db: Session,
    start_date: Optional[datetime | str] = None,
    end_date: Optional[datetime | str] = None,
) -> List[Dict[str, Any]]:
    """Calculates category revenue and volume breakdown."""
    return get_revenue_by_category(db, start_date=start_date, end_date=end_date)
