"""Controlled Customer Analytics Tools for InsightIQ AI."""

from __future__ import annotations

from typing import Any, Dict, List
from sqlalchemy.orm import Session

from app.services.customer_service import (
    get_customer_metrics as svc_cust_metrics,
    get_customer_order_frequency as svc_cust_freq,
    get_top_customers as svc_top_cust,
)
from app.tools.registry import default_tool_registry
from app.tools.schemas import (
    CustomerMetricsInput,
    CustomerOrderFrequencyInput,
    TopCustomersInput,
)


@default_tool_registry.register(
    name="get_customer_metrics",
    description="Calculates customer acquisition, retention, and churn metrics: total registered customers, new buyers, repeat buyers (>= 2 orders), and inactive customers.",
    input_schema=CustomerMetricsInput,
)
def tool_get_customer_metrics(args: CustomerMetricsInput, db: Session) -> Dict[str, Any]:
    return svc_cust_metrics(
        db=db,
        start_date=args.start_date,
        end_date=args.end_date,
        inactive_days=args.inactive_days,
    )


@default_tool_registry.register(
    name="get_top_customers",
    description="Ranks top customers by cumulative spend on eligible orders within a given date range.",
    input_schema=TopCustomersInput,
)
def tool_get_top_customers(args: TopCustomersInput, db: Session) -> List[Dict[str, Any]]:
    return svc_top_cust(db=db, limit=args.limit, start_date=args.start_date, end_date=args.end_date)


@default_tool_registry.register(
    name="get_customer_order_frequency",
    description="Segments customers into order volume frequency distribution brackets (1 order, 2-3 orders, 4-5 orders, 6+ orders) and calculates average orders per customer.",
    input_schema=CustomerOrderFrequencyInput,
)
def tool_get_customer_order_frequency(args: CustomerOrderFrequencyInput, db: Session) -> Dict[str, Any]:
    return svc_cust_freq(db=db, start_date=args.start_date, end_date=args.end_date)
