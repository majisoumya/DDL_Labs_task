"""Services package for InsightIQ AI business logic and analytics."""

from app.services.analytics_service import get_dashboard_summary
from app.services.chart_service import (
    build_category_revenue_chart,
    build_monthly_revenue_chart,
    build_sales_trend_chart,
    build_top_products_chart,
    generate_chart_from_query,
    validate_chart_specification,
)
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
    INELIGIBLE_ORDER_STATUSES,
    get_monthly_revenue,
    get_revenue_by_category,
    get_revenue_by_product,
    get_sales_growth,
    get_sales_metrics,
)

__all__ = [
    "INELIGIBLE_ORDER_STATUSES",
    "get_sales_metrics",
    "get_monthly_revenue",
    "get_revenue_by_category",
    "get_revenue_by_product",
    "get_sales_growth",
    "get_customer_metrics",
    "get_top_customers",
    "get_customer_order_frequency",
    "get_top_selling_products",
    "get_highest_revenue_products",
    "get_low_performing_products",
    "get_product_sales_quantity",
    "get_product_category_breakdown",
    "get_dashboard_summary",
    "build_monthly_revenue_chart",
    "build_sales_trend_chart",
    "build_category_revenue_chart",
    "build_top_products_chart",
    "generate_chart_from_query",
    "validate_chart_specification",
]
