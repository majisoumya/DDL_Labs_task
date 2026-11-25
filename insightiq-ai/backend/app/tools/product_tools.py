"""Controlled Product Analytics Tools for InsightIQ AI."""

from __future__ import annotations

from typing import Any, Dict, List
from sqlalchemy.orm import Session

from app.services.product_service import (
    get_highest_revenue_products as svc_highest_rev,
    get_low_performing_products as svc_low_perf,
    get_product_sales_quantity as svc_product_qty,
    get_top_selling_products as svc_top_units,
)
from app.tools.registry import default_tool_registry
from app.tools.schemas import (
    LowPerformingProductsInput,
    ProductDetailInput,
    TopProductsInput,
)


@default_tool_registry.register(
    name="get_top_products",
    description="Retrieves the highest performing products ranked by gross revenue or total unit sales volume.",
    input_schema=TopProductsInput,
)
def tool_get_top_products(args: TopProductsInput, db: Session) -> List[Dict[str, Any]]:
    if args.sort_by == "units":
        return svc_top_units(db=db, limit=args.limit, start_date=args.start_date, end_date=args.end_date)
    return svc_highest_rev(db=db, limit=args.limit, start_date=args.start_date, end_date=args.end_date)


@default_tool_registry.register(
    name="get_low_performing_products",
    description="Identifies underperforming or zero-sales products generating less revenue than a specified threshold.",
    input_schema=LowPerformingProductsInput,
)
def tool_get_low_performing_products(args: LowPerformingProductsInput, db: Session) -> List[Dict[str, Any]]:
    return svc_low_perf(
        db=db,
        threshold_revenue=args.threshold_revenue,
        limit=args.limit,
        start_date=args.start_date,
        end_date=args.end_date,
    )


@default_tool_registry.register(
    name="get_product_detail",
    description="Retrieves granular performance, units sold, and revenue for a specific product SKU by product ID.",
    input_schema=ProductDetailInput,
)
def tool_get_product_detail(args: ProductDetailInput, db: Session) -> Dict[str, Any]:
    return svc_product_qty(
        db=db,
        product_id=args.product_id,
        start_date=args.start_date,
        end_date=args.end_date,
    )
