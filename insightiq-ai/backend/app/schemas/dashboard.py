"""Pydantic Schemas for Executive Dashboard Overview."""

from __future__ import annotations

from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, Field

from app.schemas.customers import CustomerMetricsResponse
from app.schemas.products import ProductSummary
from app.schemas.sales import CategoryRevenueItem, MonthlyRevenueItem


class DashboardKPIs(BaseModel):
    """Primary operational KPI metrics."""
    total_revenue: Decimal = Field(..., description="Gross revenue from eligible orders")
    total_orders: int = Field(..., description="Distinct eligible orders")
    total_customers: int = Field(..., description="Total distinct registered customers")
    average_order_value: Decimal = Field(..., description="Average order value")


class DashboardSummaryResponse(BaseModel):
    """Consolidated executive dashboard payload."""
    kpis: DashboardKPIs
    customer_summary: CustomerMetricsResponse
    monthly_trend: List[MonthlyRevenueItem]
    category_distribution: List[CategoryRevenueItem]
    category_breakdown: Optional[List[CategoryRevenueItem]] = Field(default=None, description="Alias for category_distribution")
    top_products: List[ProductSummary]
