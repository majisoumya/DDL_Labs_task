"""Product Analytics API Router."""

from __future__ import annotations

from decimal import Decimal
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.sales import parse_and_validate_date_range
from app.database.session import get_db
from app.schemas.products import ProductDetailResponse, ProductSummary
from app.services.product_service import (
    get_highest_revenue_products,
    get_low_performing_products,
    get_product_sales_quantity,
    get_top_selling_products,
)

router = APIRouter(prefix="/products", tags=["Product Analytics"])


@router.get("/top", response_model=List[ProductSummary])
def get_top_products(
    limit: int = Query(10, ge=1, le=100, description="Number of products to return"),
    sort_by: str = Query("revenue", pattern="^(revenue|units)$", description="Sort by 'revenue' or 'units'"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    startDate: Optional[str] = Query(None, include_in_schema=False),
    endDate: Optional[str] = Query(None, include_in_schema=False),
    db: Session = Depends(get_db),
) -> List[ProductSummary]:
    """Returns top performing products ranked by revenue or unit volume."""
    start_dt, end_dt = parse_and_validate_date_range(start_date or startDate, end_date or endDate)

    if sort_by == "units":
        products = get_top_selling_products(db, limit=limit, start_date=start_dt, end_date=end_dt)
    else:
        products = get_highest_revenue_products(db, limit=limit, start_date=start_dt, end_date=end_dt)

    return [ProductSummary(**p) for p in products]


@router.get("/low-performing", response_model=List[ProductSummary])
def get_low_products(
    limit: int = Query(10, ge=1, le=100, description="Number of products to return"),
    threshold_revenue: Optional[Decimal] = Query(None, ge=0, description="Optional maximum revenue cap"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    startDate: Optional[str] = Query(None, include_in_schema=False),
    endDate: Optional[str] = Query(None, include_in_schema=False),
    db: Session = Depends(get_db),
) -> List[ProductSummary]:
    """Returns low-performing catalog items, including products with zero sales."""
    start_dt, end_dt = parse_and_validate_date_range(start_date or startDate, end_date or endDate)
    products = get_low_performing_products(
        db,
        limit=limit,
        threshold_revenue=threshold_revenue,
        start_date=start_dt,
        end_date=end_dt,
    )
    return [ProductSummary(**p) for p in products]


@router.get("/{product_id}", response_model=ProductDetailResponse)
def get_product_detail(
    product_id: int,
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
) -> ProductDetailResponse:
    """Returns sales performance metrics for an individual product."""
    start_dt, end_dt = parse_and_validate_date_range(start_date, end_date)
    detail = get_product_sales_quantity(db, product_id=product_id, start_date=start_dt, end_date=end_dt)

    if detail.get("product_name") == "Unknown":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with ID {product_id} not found.",
        )

    return ProductDetailResponse(**detail)
