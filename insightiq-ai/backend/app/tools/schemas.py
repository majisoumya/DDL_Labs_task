"""Strict Pydantic Input Schemas and Execution Metadata for Controlled AI Tools."""

from __future__ import annotations

import re
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field, field_validator, model_validator

DATE_REGEX = re.compile(r"^\d{4}-\d{2}-\d{2}$")


# -----------------------------------------------------------------------------
# 1. Base Reusable Schemas
# -----------------------------------------------------------------------------
class DateRangeArgs(BaseModel):
    """Base schema validating optional YYYY-MM-DD temporal filters."""
    start_date: Optional[str] = Field(None, description="Start date in YYYY-MM-DD format (inclusive)")
    end_date: Optional[str] = Field(None, description="End date in YYYY-MM-DD format (inclusive)")

    @field_validator("start_date", "end_date")
    @classmethod
    def validate_date_format(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            if not DATE_REGEX.match(v):
                raise ValueError(f"Invalid date format: '{v}'. Expected YYYY-MM-DD.")
            try:
                datetime.strptime(v, "%Y-%m-%d")
            except ValueError as exc:
                raise ValueError(f"Invalid calendar date: '{v}'") from exc
        return v

    @model_validator(mode="after")
    def validate_date_order(self) -> DateRangeArgs:
        if self.start_date and self.end_date:
            dt_start = datetime.strptime(self.start_date, "%Y-%m-%d")
            dt_end = datetime.strptime(self.end_date, "%Y-%m-%d")
            if dt_start > dt_end:
                raise ValueError(
                    f"start_date ({self.start_date}) cannot be greater than end_date ({self.end_date})."
                )
        return self


class TopNArgs(DateRangeArgs):
    """Base schema enforcing safe top-N result limits (1 to 100)."""
    limit: int = Field(10, ge=1, le=100, description="Maximum number of items to return (1-100)")


# -----------------------------------------------------------------------------
# 2. Domain-Specific Tool Arguments
# -----------------------------------------------------------------------------
class SalesMetricsInput(DateRangeArgs):
    """Input for calculating overall revenue, eligible orders, and AOV."""
    pass


class MonthlyRevenueInput(DateRangeArgs):
    """Input for calculating monthly revenue aggregation and trend."""
    pass


class RevenueByCategoryInput(DateRangeArgs):
    """Input for aggregating revenue and share percentages by product category."""
    pass


class RevenueByProductInput(TopNArgs):
    """Input for ranking individual products by sales revenue."""
    pass


class SalesGrowthInput(BaseModel):
    """Input for computing percentage revenue growth between two explicit periods."""
    current_start: str = Field(..., description="Current period start date (YYYY-MM-DD)")
    current_end: str = Field(..., description="Current period end date (YYYY-MM-DD)")
    previous_start: str = Field(..., description="Previous comparative period start date (YYYY-MM-DD)")
    previous_end: str = Field(..., description="Previous comparative period end date (YYYY-MM-DD)")

    @field_validator("current_start", "current_end", "previous_start", "previous_end")
    @classmethod
    def validate_dates(cls, v: str) -> str:
        if not DATE_REGEX.match(v):
            raise ValueError(f"Invalid date format: '{v}'. Expected YYYY-MM-DD.")
        try:
            datetime.strptime(v, "%Y-%m-%d")
        except ValueError as exc:
            raise ValueError(f"Invalid calendar date: '{v}'") from exc
        return v


class CustomerMetricsInput(DateRangeArgs):
    """Input for customer counts, new vs repeat cohorts, and inactivity analysis."""
    inactive_days: int = Field(
        90, ge=1, le=730, description="Threshold of days without an order to classify customer as inactive"
    )


class TopCustomersInput(TopNArgs):
    """Input for ranking high-value customers by total monetary spend."""
    pass


class CustomerOrderFrequencyInput(DateRangeArgs):
    """Input for segmenting customers into order volume frequency tiers."""
    pass


class TopProductsInput(TopNArgs):
    """Input for retrieving top products sorted by revenue or unit volume."""
    sort_by: Literal["revenue", "units"] = Field(
        "revenue", description="Sorting criteria: 'revenue' for gross dollars, 'units' for sales volume"
    )


class LowPerformingProductsInput(TopNArgs):
    """Input for discovering bottom-performing or zero-sales products."""
    threshold_revenue: Optional[float] = Field(
        None, ge=0.0, description="Optional revenue threshold below which products are flagged as low-performing"
    )


class ProductDetailInput(DateRangeArgs):
    """Input for deep-dive metrics on a specific product SKU."""
    product_id: int = Field(..., ge=1, description="Unique primary key of the target product")


class DashboardSummaryInput(DateRangeArgs):
    """Input for consolidated multi-domain executive overview."""
    pass


class RevenueDeclineInput(BaseModel):
    """Input for multi-step revenue decline investigation across comparative periods."""
    current_start: Optional[str] = Field(None, description="Current evaluation period start date (YYYY-MM-DD)")
    current_end: Optional[str] = Field(None, description="Current evaluation period end date (YYYY-MM-DD)")
    previous_start: Optional[str] = Field(None, description="Baseline comparison period start date (YYYY-MM-DD)")
    previous_end: Optional[str] = Field(None, description="Baseline comparison period end date (YYYY-MM-DD)")


# -----------------------------------------------------------------------------
# 3. Chart Tools Arguments
# -----------------------------------------------------------------------------
class ChartType(str, Enum):
    """Supported interactive chart visualizations for React / Recharts."""
    LINE = "line"
    BAR = "bar"
    PIE = "pie"
    AREA = "area"


class GenerateChartSpecInput(BaseModel):
    """Input for creating a structured chart specification."""
    chart_type: ChartType = Field(..., description="Visual chart type: line, bar, pie, or area")
    title: str = Field(..., min_length=3, max_length=150, description="User-facing title of the chart")
    x_key: str = Field(..., description="Key identifying the category/time axis (e.g. 'month', 'category')")
    y_key: Optional[str] = Field(None, description="Primary metric key (e.g. 'revenue')")
    y_keys: Optional[List[str]] = Field(None, description="List of metric keys for value axis (e.g. ['revenue'])")
    data: List[Dict[str, Any]] = Field(default_factory=list, description="Dataset records to be visualized")
    description: Optional[str] = Field(None, description="Optional brief explanation of chart insight")

    @model_validator(mode="after")
    def harmonize_y_keys(self) -> GenerateChartSpecInput:
        if not self.y_key and not self.y_keys:
            raise ValueError("Either 'y_key' or 'y_keys' must be provided.")
        if not self.y_key and self.y_keys:
            self.y_key = self.y_keys[0]
        if not self.y_keys and self.y_key:
            self.y_keys = [self.y_key]
        return self


# -----------------------------------------------------------------------------
# 4. Tool Execution Result Schema
# -----------------------------------------------------------------------------
class ToolExecutionResult(BaseModel):
    """Complete execution record of a controlled tool invocation."""
    tool_name: str = Field(..., description="Name of the invoked tool")
    arguments: Dict[str, Any] = Field(default_factory=dict, description="Validated input arguments used")
    success: bool = Field(..., description="Whether tool execution completed without error")
    data: Optional[Any] = Field(None, description="Structured output payload if successful")
    error: Optional[str] = Field(None, description="Error message if execution failed")
    execution_time_ms: float = Field(..., description="Duration of tool execution in milliseconds")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Diagnostic and source metadata")
