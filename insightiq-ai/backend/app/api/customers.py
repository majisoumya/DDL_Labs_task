"""Customer Analytics API Router."""

from __future__ import annotations

from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.sales import parse_and_validate_date_range
from app.database.session import get_db
from app.schemas.customers import (
    CustomerMetricsResponse,
    CustomerOrderFrequencyResponse,
    TopCustomerItem,
)
from app.services.customer_service import (
    get_customer_metrics,
    get_customer_order_frequency,
    get_top_customers,
)

router = APIRouter(prefix="/customers", tags=["Customer Analytics"])


@router.get("/metrics", response_model=CustomerMetricsResponse)
def get_metrics(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    startDate: Optional[str] = Query(None, include_in_schema=False),
    endDate: Optional[str] = Query(None, include_in_schema=False),
    inactive_days: int = Query(90, ge=1, le=365, description="Lookback days to define an inactive customer"),
    db: Session = Depends(get_db),
) -> CustomerMetricsResponse:
    """Returns customer cohort metrics: total, new, repeat, and inactive customers."""
    start_dt, end_dt = parse_and_validate_date_range(start_date or startDate, end_date or endDate)
    metrics = get_customer_metrics(db, start_date=start_dt, end_date=end_dt, inactive_days=inactive_days)
    return CustomerMetricsResponse(**metrics)


@router.get("/top", response_model=List[TopCustomerItem])
def get_top_spending_customers(
    limit: int = Query(10, ge=1, le=100, description="Maximum customers to return"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    startDate: Optional[str] = Query(None, include_in_schema=False),
    endDate: Optional[str] = Query(None, include_in_schema=False),
    db: Session = Depends(get_db),
) -> List[TopCustomerItem]:
    """Returns high-value customers ranked by cumulative spend on eligible orders."""
    start_dt, end_dt = parse_and_validate_date_range(start_date or startDate, end_date or endDate)
    customers = get_top_customers(db, limit=limit, start_date=start_dt, end_date=end_dt)
    return [TopCustomerItem(**c) for c in customers]


@router.get("/frequency", response_model=CustomerOrderFrequencyResponse)
def get_frequency(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    startDate: Optional[str] = Query(None, include_in_schema=False),
    endDate: Optional[str] = Query(None, include_in_schema=False),
    db: Session = Depends(get_db),
) -> CustomerOrderFrequencyResponse:
    """Returns customer order frequency distribution buckets and average orders per customer."""
    start_dt, end_dt = parse_and_validate_date_range(start_date or startDate, end_date or endDate)
    freq = get_customer_order_frequency(db, start_date=start_dt, end_date=end_dt)
    return CustomerOrderFrequencyResponse(**freq)
