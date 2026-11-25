"""Customer Analytics Service for InsightIQ AI.

Provides customer metrics, cohort retention, inactivity detection,
and top customer rankings.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional
from sqlalchemy import distinct, func, select
from sqlalchemy.orm import Session

from app.database.models import Customer, Order, OrderItem
from app.services.sales_service import INELIGIBLE_ORDER_STATUSES


def get_customer_metrics(
    db: Session,
    start_date: Optional[datetime | str] = None,
    end_date: Optional[datetime | str] = None,
    inactive_days: int = 90,
) -> Dict[str, Any]:
    """Calculates customer metrics:

    - total_customers: Total distinct registered customer count.
    - new_customers: Customers whose first eligible order date falls within [start_date, end_date].
    - repeat_customers: Customers with >= 2 eligible orders.
    - inactive_customers: Customers with no eligible orders in the last `inactive_days`.
    """
    # 1. Total Customers
    cust_stmt = select(func.count(Customer.customer_id))
    if end_date:
        cust_stmt = cust_stmt.where(Customer.created_at <= end_date)
    total_customers = db.scalar(cust_stmt) or 0

    # 2. First Order Date Subquery per customer (for new customers calculation)
    first_order_subq = (
        select(
            Order.customer_id,
            func.min(Order.order_date).label("first_order_date"),
        )
        .where(Order.status.notin_(INELIGIBLE_ORDER_STATUSES))
        .group_by(Order.customer_id)
        .subquery()
    )

    new_cust_stmt = select(func.count(first_order_subq.c.customer_id))
    if start_date:
        new_cust_stmt = new_cust_stmt.where(first_order_subq.c.first_order_date >= start_date)
    if end_date:
        new_cust_stmt = new_cust_stmt.where(first_order_subq.c.first_order_date <= end_date)

    new_customers = db.scalar(new_cust_stmt) or 0

    # 3. Repeat Customers: customers with >= 2 eligible orders
    order_counts_subq = (
        select(
            Order.customer_id,
            func.count(Order.order_id).label("cnt"),
        )
        .where(Order.status.notin_(INELIGIBLE_ORDER_STATUSES))
    )
    if start_date:
        order_counts_subq = order_counts_subq.where(Order.order_date >= start_date)
    if end_date:
        order_counts_subq = order_counts_subq.where(Order.order_date <= end_date)

    order_counts_subq = order_counts_subq.group_by(Order.customer_id).having(func.count(Order.order_id) >= 2).subquery()
    repeat_customers = db.scalar(select(func.count(order_counts_subq.c.customer_id))) or 0

    # 4. Inactive Customers: Customers with no eligible order in the last `inactive_days`
    # Determine reference date: use provided end_date, or max order_date in DB, or now
    if end_date:
        ref_date = pd_to_dt(end_date)
    else:
        max_dt_in_db = db.scalar(
            select(func.max(Order.order_date)).where(Order.status.notin_(INELIGIBLE_ORDER_STATUSES))
        )
        ref_date = max_dt_in_db if max_dt_in_db else datetime.now()

    cutoff_date = ref_date - timedelta(days=inactive_days)

    # Customers who placed an order after cutoff_date
    active_recent_subq = (
        select(distinct(Order.customer_id))
        .where(
            Order.status.notin_(INELIGIBLE_ORDER_STATUSES),
            Order.order_date >= cutoff_date,
            Order.order_date <= ref_date,
        )
        .subquery()
    )

    # Total customers registered by ref_date who did NOT place an order after cutoff_date
    inactive_stmt = (
        select(func.count(Customer.customer_id))
        .where(
            Customer.created_at <= ref_date,
            Customer.customer_id.notin_(select(active_recent_subq)),
        )
    )
    inactive_customers = db.scalar(inactive_stmt) or 0

    return {
        "total_customers": int(total_customers),
        "new_customers": int(new_customers),
        "repeat_customers": int(repeat_customers),
        "inactive_customers": int(inactive_customers),
    }


def get_top_customers(
    db: Session,
    limit: int = 10,
    start_date: Optional[datetime | str] = None,
    end_date: Optional[datetime | str] = None,
) -> List[Dict[str, Any]]:
    """Retrieves top customers ranked by total spend on eligible orders."""
    stmt = (
        select(
            Customer.customer_id,
            Customer.name,
            Customer.email,
            Customer.city,
            func.coalesce(func.sum(OrderItem.quantity * OrderItem.unit_price), 0).label("total_spend"),
            func.count(distinct(Order.order_id)).label("order_count"),
        )
        .join(Order, Customer.customer_id == Order.customer_id)
        .join(OrderItem, Order.order_id == OrderItem.order_id)
        .where(Order.status.notin_(INELIGIBLE_ORDER_STATUSES))
    )

    if start_date:
        stmt = stmt.where(Order.order_date >= start_date)
    if end_date:
        stmt = stmt.where(Order.order_date <= end_date)

    stmt = (
        stmt.group_by(Customer.customer_id, Customer.name, Customer.email, Customer.city)
        .order_by(func.sum(OrderItem.quantity * OrderItem.unit_price).desc())
        .limit(limit)
    )

    rows = db.execute(stmt).all()
    result: List[Dict[str, Any]] = []
    for r in rows:
        result.append({
            "customer_id": int(r.customer_id),
            "name": str(r.name),
            "email": str(r.email),
            "city": str(r.city),
            "total_spend": Decimal(str(r.total_spend)).quantize(Decimal("0.01")),
            "order_count": int(r.order_count),
        })
    return result


def get_customer_order_frequency(
    db: Session,
    start_date: Optional[datetime | str] = None,
    end_date: Optional[datetime | str] = None,
) -> Dict[str, Any]:
    """Calculates order frequency buckets and average orders per customer."""
    subq = (
        select(
            Order.customer_id,
            func.count(Order.order_id).label("orders_count"),
        )
        .where(Order.status.notin_(INELIGIBLE_ORDER_STATUSES))
    )
    if start_date:
        subq = subq.where(Order.order_date >= start_date)
    if end_date:
        subq = subq.where(Order.order_date <= end_date)

    subq = subq.group_by(Order.customer_id).subquery()

    counts = db.execute(select(subq.c.orders_count)).scalars().all()
    if not counts:
        return {
            "one_order": 0,
            "two_to_three": 0,
            "four_to_five": 0,
            "six_plus": 0,
            "average_orders_per_customer": 0.0,
        }

    one_order = sum(1 for c in counts if c == 1)
    two_to_three = sum(1 for c in counts if 2 <= c <= 3)
    four_to_five = sum(1 for c in counts if 4 <= c <= 5)
    six_plus = sum(1 for c in counts if c >= 6)
    avg_orders = round(sum(counts) / len(counts), 2)

    return {
        "one_order": one_order,
        "two_to_three": two_to_three,
        "four_to_five": four_to_five,
        "six_plus": six_plus,
        "average_orders_per_customer": avg_orders,
    }


def pd_to_dt(val: datetime | str) -> datetime:
    """Helper to ensure datetime conversion."""
    if isinstance(val, datetime):
        return val
    import pandas as pd
    return pd.to_datetime(val).to_pydatetime()
