"""FastAPI Router for Analytics CSV Data Export."""

from __future__ import annotations

import csv
from decimal import Decimal
import io
from typing import Optional
from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.logging_config import get_logger
from app.services.customer_service import get_top_customers
from app.services.product_service import get_highest_revenue_products
from app.services.sales_service import get_monthly_revenue, get_sales_metrics

logger = get_logger("insightiq.api.export")

export_router = APIRouter(prefix="/export", tags=["Data Export"])


@export_router.get(
    "/sales-csv",
    status_code=status.HTTP_200_OK,
    summary="Export Sales Performance to CSV",
    description="Streams a verified CSV file summarizing monthly revenue, order volume, and AOV.",
)
def export_sales_csv(
    start_date: Optional[str] = Query(None, description="Start date filter (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date filter (YYYY-MM-DD)"),
    startDate: Optional[str] = Query(None, include_in_schema=False),
    endDate: Optional[str] = Query(None, include_in_schema=False),
    db: Session = Depends(get_db),
) -> Response:
    """Exports monthly sales metrics to downloadable CSV format."""
    s_date = start_date or startDate
    e_date = end_date or endDate
    logger.info("Generating sales CSV export for range [%s to %s]", s_date, e_date)

    monthly_records = get_monthly_revenue(db, start_date=s_date, end_date=e_date)
    sales_kpis = get_sales_metrics(db, start_date=s_date, end_date=e_date)

    output = io.StringIO()
    writer = csv.writer(output)

    total_rev = sales_kpis.get("total_revenue", 0.0)
    total_orders = sales_kpis.get("total_orders", 0)
    aov = sales_kpis.get("aov", 0.0)

    # 1. Summary Header Section
    writer.writerow(["# InsightIQ AI - Executive Sales Report"])
    writer.writerow(["# Start Date", s_date or "All History"])
    writer.writerow(["# End Date", e_date or "Present"])
    writer.writerow(["# Total Revenue ($)", f"{float(total_rev):.2f}"])
    writer.writerow(["# Total Qualifying Orders", total_orders])
    writer.writerow(["# Average Order Value ($)", f"{float(aov):.2f}"])
    writer.writerow(["# Governance Policy", "Cancelled and returned orders are excluded."])
    writer.writerow([])

    # 2. Monthly Trend Table
    writer.writerow(["Month", "Revenue ($)", "Order Count", "Units Sold", "AOV ($)"])
    for row in monthly_records:
        rev = float(row.get("revenue", 0.0))
        cnt = int(row.get("order_count", 0))
        units = int(row.get("units_sold", 0))
        m_aov = rev / cnt if cnt > 0 else 0.0
        writer.writerow([
            row.get("month", ""),
            f"{rev:.2f}",
            cnt,
            units,
            f"{m_aov:.2f}",
        ])

    csv_content = output.getvalue()
    filename = "insightiq_sales_report.csv"
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@export_router.get(
    "/products-csv",
    status_code=status.HTTP_200_OK,
    summary="Export Product Catalog Analytics to CSV",
    description="Streams a verified CSV file of top revenue-generating products.",
)
def export_products_csv(
    limit: int = Query(50, ge=1, le=500, description="Maximum products to export"),
    start_date: Optional[str] = Query(None, description="Start date filter (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date filter (YYYY-MM-DD)"),
    startDate: Optional[str] = Query(None, include_in_schema=False),
    endDate: Optional[str] = Query(None, include_in_schema=False),
    db: Session = Depends(get_db),
) -> Response:
    """Exports catalog performance metrics to downloadable CSV format."""
    s_date = start_date or startDate
    e_date = end_date or endDate
    logger.info("Generating products CSV export (limit=%s, range=[%s to %s])", limit, s_date, e_date)
    products = get_highest_revenue_products(db, limit=limit, start_date=s_date, end_date=e_date)

    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow(["Product ID", "Product Name", "Category", "Unit Price ($)", "Total Revenue ($)", "Units Sold", "Current Stock"])
    for p in products:
        writer.writerow([
            p.get("product_id"),
            p.get("product_name"),
            p.get("category"),
            f"{float(p.get('price', 0)):.2f}",
            f"{float(p.get('revenue', 0)):.2f}",
            p.get("units_sold", 0),
            p.get("stock", 0),
        ])

    csv_content = output.getvalue()
    filename = "insightiq_products_catalog.csv"
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@export_router.get(
    "/customers-csv",
    status_code=status.HTTP_200_OK,
    summary="Export Customer Cohort Analytics to CSV",
    description="Streams a verified CSV file ranking customer accounts by total expenditure.",
)
def export_customers_csv(
    limit: int = Query(50, ge=1, le=500, description="Maximum customer cohorts to export"),
    start_date: Optional[str] = Query(None, description="Start date filter (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date filter (YYYY-MM-DD)"),
    startDate: Optional[str] = Query(None, include_in_schema=False),
    endDate: Optional[str] = Query(None, include_in_schema=False),
    db: Session = Depends(get_db),
) -> Response:
    """Exports customer cohort metrics to downloadable CSV format."""
    s_date = start_date or startDate
    e_date = end_date or endDate
    logger.info("Generating customers CSV export (limit=%s, range=[%s to %s])", limit, s_date, e_date)
    customers = get_top_customers(db, limit=limit, start_date=s_date, end_date=e_date)

    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow(["Customer ID", "Name", "Email", "City", "Total Spend ($)", "Completed Orders"])
    for c in customers:
        writer.writerow([
            c.get("customer_id"),
            c.get("name"),
            c.get("email"),
            c.get("city"),
            f"{float(c.get('total_spend', 0)):.2f}",
            c.get("completed_orders", 0),
        ])

    csv_content = output.getvalue()
    filename = "insightiq_customers_cohort.csv"
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
