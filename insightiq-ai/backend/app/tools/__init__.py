"""Controlled AI Tool Calling Registry and Analytics Tool Definitions."""

from __future__ import annotations

from app.tools.registry import (
    ToolDefinition,
    ToolRegistry,
    default_tool_registry,
)
from app.tools.schemas import (
    ChartType,
    CustomerMetricsInput,
    CustomerOrderFrequencyInput,
    DashboardSummaryInput,
    DateRangeArgs,
    GenerateChartSpecInput,
    LowPerformingProductsInput,
    MonthlyRevenueInput,
    ProductDetailInput,
    RevenueByCategoryInput,
    RevenueByProductInput,
    RevenueDeclineInput,
    SalesGrowthInput,
    SalesMetricsInput,
    ToolExecutionResult,
    TopCustomersInput,
    TopNArgs,
    TopProductsInput,
)

# Import domain tool modules to trigger decorators on default_tool_registry
import app.tools.chart_tools  # noqa: F401
import app.tools.customer_tools  # noqa: F401
import app.tools.product_tools  # noqa: F401
import app.tools.sales_tools  # noqa: F401

__all__ = [
    "default_tool_registry",
    "ToolRegistry",
    "ToolDefinition",
    "ToolExecutionResult",
    "DateRangeArgs",
    "TopNArgs",
    "SalesMetricsInput",
    "MonthlyRevenueInput",
    "RevenueByCategoryInput",
    "RevenueByProductInput",
    "RevenueDeclineInput",
    "SalesGrowthInput",
    "CustomerMetricsInput",
    "TopCustomersInput",
    "CustomerOrderFrequencyInput",
    "TopProductsInput",
    "LowPerformingProductsInput",
    "ProductDetailInput",
    "DashboardSummaryInput",
    "ChartType",
    "GenerateChartSpecInput",
]
