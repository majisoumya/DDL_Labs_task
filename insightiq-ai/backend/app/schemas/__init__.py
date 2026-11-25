"""Pydantic schemas package for API validation and serialization."""

from app.schemas.charts import (
    ChartGenerationRequest,
    ChartMetadata,
    ChartSeriesConfig,
    ChartSpec,
    ChartType,
    ChartValidationResult,
)
from app.schemas.customers import (
    CustomerMetricsResponse,
    CustomerOrderFrequencyResponse,
    TopCustomerItem,
)
from app.schemas.dashboard import DashboardKPIs, DashboardSummaryResponse
from app.schemas.products import ProductDetailResponse, ProductSummary
from app.schemas.sales import (
    CategoryRevenueItem,
    MonthlyRevenueItem,
    PeriodMetrics,
    ProductRevenueItem,
    SalesGrowthResponse,
    SalesMetricsResponse,
)

__all__ = [
    "SalesMetricsResponse",
    "MonthlyRevenueItem",
    "CategoryRevenueItem",
    "ProductRevenueItem",
    "PeriodMetrics",
    "SalesGrowthResponse",
    "ProductSummary",
    "ProductDetailResponse",
    "CustomerMetricsResponse",
    "TopCustomerItem",
    "CustomerOrderFrequencyResponse",
    "DashboardKPIs",
    "DashboardSummaryResponse",
    "ChartType",
    "ChartSpec",
    "ChartMetadata",
    "ChartSeriesConfig",
    "ChartGenerationRequest",
    "ChartValidationResult",
]
