"""Unified Analytics Service Coordinator for InsightIQ AI.

Consolidates sales, customer, and product metrics for executive dashboards
and AI analyst tool routing.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional
from sqlalchemy.orm import Session

from app.services.customer_service import (
    get_customer_metrics,
    get_customer_order_frequency,
    get_top_customers,
)
from app.services.product_service import (
    get_highest_revenue_products,
    get_low_performing_products,
    get_product_category_breakdown,
    get_product_sales_quantity,
    get_top_selling_products,
)
from app.services.sales_service import (
    get_monthly_revenue,
    get_revenue_by_category,
    get_revenue_by_product,
    get_sales_growth,
    get_sales_metrics,
)


def get_dashboard_summary(
    db: Session,
    start_date: Optional[datetime | str] = None,
    end_date: Optional[datetime | str] = None,
) -> Dict[str, Any]:
    """Generates an executive dashboard overview aggregating:

    - Core KPIs: Total Revenue, Total Orders, Total Customers, Average Order Value (AOV).
    - Monthly Revenue trends.
    - Revenue by Product Category.
    - Top 5 Products by Revenue.
    - Customer Cohort Metrics.
    """
    sales_kpis = get_sales_metrics(db, start_date=start_date, end_date=end_date)
    customer_kpis = get_customer_metrics(db, start_date=start_date, end_date=end_date)
    monthly_trend = get_monthly_revenue(db, start_date=start_date, end_date=end_date)
    category_split = get_revenue_by_category(db, start_date=start_date, end_date=end_date)
    top_products = get_highest_revenue_products(db, limit=5, start_date=start_date, end_date=end_date)

    return {
        "kpis": {
            "total_revenue": sales_kpis["total_revenue"],
            "total_orders": sales_kpis["total_orders"],
            "total_customers": customer_kpis["total_customers"],
            "average_order_value": sales_kpis["aov"],
        },
        "customer_summary": customer_kpis,
        "monthly_trend": monthly_trend,
        "category_distribution": category_split,
        "category_breakdown": category_split,
        "top_products": top_products,
    }
