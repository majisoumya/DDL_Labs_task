"""FastAPI Router for Dynamic Business Chart Generation and Validation."""

from __future__ import annotations

from typing import Any, Dict, Optional
from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.logging_config import get_logger
from app.schemas.charts import (
    ChartGenerationRequest,
    ChartSpec,
    ChartValidationResult,
)
from app.services.chart_service import (
    build_category_revenue_chart,
    build_monthly_revenue_chart,
    build_sales_trend_chart,
    build_top_products_chart,
    generate_chart_from_query,
    validate_chart_specification,
)

logger = get_logger("insightiq.api.charts")

charts_router = APIRouter(prefix="/charts", tags=["Visualizations & Charts"])


@charts_router.get(
    "/monthly-revenue",
    response_model=ChartSpec,
    summary="Get Monthly Revenue Chart Specification",
    description="Returns a validated, Recharts-compatible line or area chart specification for historical monthly revenue.",
)
def get_monthly_revenue_chart_endpoint(
    start_date: Optional[str] = Query(None, pattern=r"^\d{4}-\d{2}-\d{2}$", description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, pattern=r"^\d{4}-\d{2}-\d{2}$", description="End date (YYYY-MM-DD)"),
    startDate: Optional[str] = Query(None, include_in_schema=False),
    endDate: Optional[str] = Query(None, include_in_schema=False),
    chart_type: str = Query("line", description="Visual chart type: line, area, or bar"),
    db: Session = Depends(get_db),
) -> ChartSpec:
    """Generates monthly revenue chart specification."""
    s_date = start_date or startDate
    e_date = end_date or endDate
    if s_date and e_date and s_date > e_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Inverted date range: start_date '{s_date}' cannot be after end_date '{e_date}'.",
        )
    return build_monthly_revenue_chart(db, start_date=s_date, end_date=e_date, chart_type=chart_type)


@charts_router.get(
    "/category-revenue",
    response_model=ChartSpec,
    summary="Get Category Revenue Chart Specification",
    description="Returns a validated pie or bar chart specification showing revenue breakdown by product category.",
)
def get_category_revenue_chart_endpoint(
    start_date: Optional[str] = Query(None, pattern=r"^\d{4}-\d{2}-\d{2}$", description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, pattern=r"^\d{4}-\d{2}-\d{2}$", description="End date (YYYY-MM-DD)"),
    startDate: Optional[str] = Query(None, include_in_schema=False),
    endDate: Optional[str] = Query(None, include_in_schema=False),
    chart_type: str = Query("pie", description="Visual chart type: pie or bar"),
    db: Session = Depends(get_db),
) -> ChartSpec:
    """Generates category revenue distribution chart specification."""
    s_date = start_date or startDate
    e_date = end_date or endDate
    if s_date and e_date and s_date > e_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Inverted date range: start_date '{s_date}' cannot be after end_date '{e_date}'.",
        )
    return build_category_revenue_chart(db, start_date=s_date, end_date=e_date, chart_type=chart_type)


@charts_router.get(
    "/top-products",
    response_model=ChartSpec,
    summary="Get Top Products Chart Specification",
    description="Returns a validated ranked bar chart specification for catalog leaders by revenue or units sold.",
)
def get_top_products_chart_endpoint(
    limit: int = Query(5, ge=1, le=50, description="Top N product count"),
    sort_by: str = Query("revenue", pattern="^(revenue|units)$", description="Ranking metric: revenue or units"),
    start_date: Optional[str] = Query(None, pattern=r"^\d{4}-\d{2}-\d{2}$", description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, pattern=r"^\d{4}-\d{2}-\d{2}$", description="End date (YYYY-MM-DD)"),
    startDate: Optional[str] = Query(None, include_in_schema=False),
    endDate: Optional[str] = Query(None, include_in_schema=False),
    chart_type: str = Query("bar", description="Visual chart type: bar or line"),
    db: Session = Depends(get_db),
) -> ChartSpec:
    """Generates top products ranked bar chart specification."""
    s_date = start_date or startDate
    e_date = end_date or endDate
    if s_date and e_date and s_date > e_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Inverted date range: start_date '{s_date}' cannot be after end_date '{e_date}'.",
        )
    return build_top_products_chart(
        db, limit=limit, start_date=s_date, end_date=e_date, sort_by=sort_by, chart_type=chart_type
    )


@charts_router.get(
    "/sales-trend",
    response_model=ChartSpec,
    summary="Get Customer Orders and Sales Trend Chart Specification",
    description="Returns a validated multi-series chart specification comparing customer order volume and unit throughput over time.",
)
def get_sales_trend_chart_endpoint(
    start_date: Optional[str] = Query(None, pattern=r"^\d{4}-\d{2}-\d{2}$", description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, pattern=r"^\d{4}-\d{2}-\d{2}$", description="End date (YYYY-MM-DD)"),
    startDate: Optional[str] = Query(None, include_in_schema=False),
    endDate: Optional[str] = Query(None, include_in_schema=False),
    chart_type: str = Query("bar", description="Visual chart type: bar, line, or area"),
    db: Session = Depends(get_db),
) -> ChartSpec:
    """Generates customer orders and unit volume trend chart specification."""
    s_date = start_date or startDate
    e_date = end_date or endDate
    if s_date and e_date and s_date > e_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Inverted date range: start_date '{s_date}' cannot be after end_date '{e_date}'.",
        )
    return build_sales_trend_chart(db, start_date=s_date, end_date=e_date, chart_type=chart_type)


@charts_router.post(
    "/generate",
    response_model=ChartSpec,
    summary="Generate Dynamic Chart from Natural Query or Configuration",
    description="Interprets natural language inquiries or explicit chart configs and returns validated chart specs.",
)
def generate_chart_endpoint(
    req: ChartGenerationRequest,
    db: Session = Depends(get_db),
) -> ChartSpec:
    """Dispatches natural-language or structured request to appropriate analytical chart builder."""
    if req.start_date and req.end_date and req.start_date > req.end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Inverted date range: start_date '{req.start_date}' cannot be after end_date '{req.end_date}'.",
        )

    try:
        if req.query:
            return generate_chart_from_query(
                db=db,
                query=req.query,
                chart_type_override=req.chart_type,
                start_date=req.start_date,
                end_date=req.end_date,
                limit=req.limit,
            )
        elif req.metric == "category_revenue" or req.domain == "products" and req.chart_type == "pie":
            return build_category_revenue_chart(
                db=db, start_date=req.start_date, end_date=req.end_date, chart_type=req.chart_type or "pie"
            )
        elif req.metric == "top_products":
            return build_top_products_chart(
                db=db,
                limit=req.limit or 5,
                start_date=req.start_date,
                end_date=req.end_date,
                chart_type=req.chart_type or "bar",
            )
        else:
            return build_monthly_revenue_chart(
                db=db, start_date=req.start_date, end_date=req.end_date, chart_type=req.chart_type or "line"
            )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@charts_router.post(
    "/validate",
    response_model=ChartValidationResult,
    summary="Validate Arbitrary Chart Specification",
    description="Validates that a chart specification adheres to required schema, keys, and numeric types.",
)
def validate_chart_endpoint(
    spec: Dict[str, Any] = Body(..., description="Raw chart specification dictionary"),
) -> ChartValidationResult:
    """Validates chart specification payload integrity."""
    return validate_chart_specification(spec)
