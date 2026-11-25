"""Dashboard Summary API Router."""

from __future__ import annotations

from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.sales import parse_and_validate_date_range
from app.database.session import get_db
from app.schemas.dashboard import DashboardSummaryResponse
from app.services.analytics_service import get_dashboard_summary

router = APIRouter(prefix="/dashboard", tags=["Dashboard Summary"])


@router.get("", response_model=DashboardSummaryResponse)
@router.get("/", response_model=DashboardSummaryResponse, include_in_schema=False)
@router.get("/summary", response_model=DashboardSummaryResponse)
def get_dashboard(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    startDate: Optional[str] = Query(None, include_in_schema=False),
    endDate: Optional[str] = Query(None, include_in_schema=False),
    db: Session = Depends(get_db),
) -> DashboardSummaryResponse:
    """Returns a consolidated executive summary for the React dashboard.

    Includes:
    - Primary KPIs (Revenue, Orders, Customers, AOV)
    - Customer cohorts
    - Monthly revenue trends
    - Category distribution
    - Top 5 products by revenue
    """
    start_dt, end_dt = parse_and_validate_date_range(start_date or startDate, end_date or endDate)
    summary = get_dashboard_summary(db, start_date=start_dt, end_date=end_dt)
    return DashboardSummaryResponse(**summary)
