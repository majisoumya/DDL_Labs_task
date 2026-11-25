"""Sales Analytics API Router."""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional, Tuple
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.sales import (
    CategoryRevenueItem,
    MonthlyRevenueItem,
    ProductRevenueItem,
    SalesGrowthResponse,
    SalesMetricsResponse,
)
from app.services.sales_service import (
    get_monthly_revenue,
    get_revenue_by_category,
    get_revenue_by_product,
    get_sales_growth,
    get_sales_metrics,
)

router = APIRouter(prefix="/sales", tags=["Sales Analytics"])


def parse_and_validate_date_range(
    start_date: Optional[str],
    end_date: Optional[str],
) -> Tuple[Optional[datetime], Optional[datetime]]:
    """Validates date parameters and ensures start_date <= end_date.

    If end_date is given as a YYYY-MM-DD date string without time components,
    it automatically includes the entire day up to 23:59:59.999999.
    """
    start_dt = None
    end_dt = None

    if start_date:
        try:
            start_dt = datetime.fromisoformat(start_date.strip())
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid start_date format '{start_date}'. Expected ISO format (YYYY-MM-DD).",
            )

    if end_date:
        try:
            raw_end = end_date.strip()
            end_dt = datetime.fromisoformat(raw_end)
            if len(raw_end) <= 10 and end_dt.hour == 0 and end_dt.minute == 0 and end_dt.second == 0:
                end_dt = end_dt.replace(hour=23, minute=59, second=59, microsecond=999999)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid end_date format '{end_date}'. Expected ISO format (YYYY-MM-DD).",
            )

    if start_dt and end_dt and start_dt > end_dt:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"start_date ({start_date}) cannot be greater than end_date ({end_date}).",
        )

    return start_dt, end_dt


@router.get("/metrics", response_model=SalesMetricsResponse)
def get_metrics(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    startDate: Optional[str] = Query(None, include_in_schema=False),
    endDate: Optional[str] = Query(None, include_in_schema=False),
    db: Session = Depends(get_db),
) -> SalesMetricsResponse:
    """Returns total revenue, eligible orders count, and Average Order Value (AOV)."""
    start_dt, end_dt = parse_and_validate_date_range(start_date or startDate, end_date or endDate)
    metrics = get_sales_metrics(db, start_date=start_dt, end_date=end_dt)
    return SalesMetricsResponse(**metrics)


@router.get("/monthly", response_model=List[MonthlyRevenueItem])
def get_monthly(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    startDate: Optional[str] = Query(None, include_in_schema=False),
    endDate: Optional[str] = Query(None, include_in_schema=False),
    db: Session = Depends(get_db),
) -> List[MonthlyRevenueItem]:
    """Returns monthly revenue trend, order volume, and units sold."""
    start_dt, end_dt = parse_and_validate_date_range(start_date or startDate, end_date or endDate)
    monthly_data = get_monthly_revenue(db, start_date=start_dt, end_date=end_dt)
    return [MonthlyRevenueItem(**item) for item in monthly_data]


@router.get("/categories", response_model=List[CategoryRevenueItem])
def get_categories(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    startDate: Optional[str] = Query(None, include_in_schema=False),
    endDate: Optional[str] = Query(None, include_in_schema=False),
    db: Session = Depends(get_db),
) -> List[CategoryRevenueItem]:
    """Returns revenue breakdown and percentage distribution by product category."""
    start_dt, end_dt = parse_and_validate_date_range(start_date or startDate, end_date or endDate)
    category_data = get_revenue_by_category(db, start_date=start_dt, end_date=end_dt)
    return [CategoryRevenueItem(**item) for item in category_data]


@router.get("/products", response_model=List[ProductRevenueItem])
def get_products(
    limit: int = Query(10, ge=1, le=100, description="Maximum products to return"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    startDate: Optional[str] = Query(None, include_in_schema=False),
    endDate: Optional[str] = Query(None, include_in_schema=False),
    db: Session = Depends(get_db),
) -> List[ProductRevenueItem]:
    """Returns top products ranked by gross revenue."""
    start_dt, end_dt = parse_and_validate_date_range(start_date or startDate, end_date or endDate)
    products_data = get_revenue_by_product(db, limit=limit, start_date=start_dt, end_date=end_dt)
    return [ProductRevenueItem(**item) for item in products_data]


@router.get("/growth", response_model=SalesGrowthResponse)
def get_growth(
    current_start: str = Query(..., description="Current period start (YYYY-MM-DD)"),
    current_end: str = Query(..., description="Current period end (YYYY-MM-DD)"),
    previous_start: str = Query(..., description="Previous period start (YYYY-MM-DD)"),
    previous_end: str = Query(..., description="Previous period end (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
) -> SalesGrowthResponse:
    """Calculates period-over-period sales growth comparisons."""
    c_start, c_end = parse_and_validate_date_range(current_start, current_end)
    p_start, p_end = parse_and_validate_date_range(previous_start, previous_end)

    growth_data = get_sales_growth(
        db,
        current_start=c_start,
        current_end=c_end,
        previous_start=p_start,
        previous_end=p_end,
    )
    return SalesGrowthResponse(**growth_data)
