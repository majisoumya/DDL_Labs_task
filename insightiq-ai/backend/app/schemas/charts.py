"""Pydantic Schemas for Dynamic Chart Specifications and Validations."""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Literal, Optional, Union
from pydantic import BaseModel, Field, field_validator, model_validator


class ChartType(str, Enum):
    """Supported visual chart types in InsightIQ AI."""
    LINE = "line"
    BAR = "bar"
    PIE = "pie"
    AREA = "area"


SUPPORTED_CHART_TYPES = {ct.value for ct in ChartType}


class ChartSeriesConfig(BaseModel):
    """Configuration for an individual data series in a chart."""
    key: str = Field(..., description="Data field key corresponding to the metric")
    label: Optional[str] = Field(None, description="Human-readable legend label")
    color: Optional[str] = Field(None, description="Hex color code for rendering")
    unit: Optional[str] = Field(None, description="Unit symbol (e.g., '$', '%', 'units')")


class ChartMetadata(BaseModel):
    """Auxiliary layout, labeling, and provenance metadata for charts."""
    total_points: int = Field(0, description="Total number of data records")
    x_label: Optional[str] = Field(None, description="Title for the X-axis")
    y_label: Optional[str] = Field(None, description="Title for the Y-axis")
    unit: Optional[str] = Field(None, description="Primary unit of measurement")
    generated_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO timestamp of chart spec creation",
    )
    source_tool: Optional[str] = Field(None, description="Name of analytics service/tool that supplied the data")
    is_empty: bool = Field(False, description="Flag indicating whether data payload is empty")
    color_palette: List[str] = Field(
        default_factory=lambda: [
            "#3B82F6",  # Blue
            "#10B981",  # Green
            "#F59E0B",  # Amber
            "#EF4444",  # Red
            "#8B5CF6",  # Purple
            "#06B6D4",  # Cyan
            "#EC4899",  # Pink
            "#F97316",  # Orange
        ],
        description="Default hex color palette for multi-series or categorical slices",
    )


class ChartSpec(BaseModel):
    """
    Standardized, validated chart specification for rendering dynamic business charts in React / Recharts.
    Strictly conforms to:
    {
      "chart_type": "line",
      "title": "Monthly Revenue",
      "x_key": "month",
      "y_key": "revenue",
      "data": [...]
    }
    """
    chart_type: str = Field(..., description="Visual chart type: 'line', 'bar', 'pie', or 'area'")
    title: str = Field(..., min_length=2, max_length=150, description="User-facing title of the chart")
    x_key: str = Field(..., min_length=1, description="Primary dimensional or temporal axis key (e.g. 'month', 'category')")
    y_key: str = Field(..., min_length=1, description="Primary quantitative metric key (e.g. 'revenue', 'order_count')")
    y_keys: Optional[List[str]] = Field(None, description="Optional list of metric keys for multi-series charts")
    data: List[Dict[str, Any]] = Field(default_factory=list, description="Dataset records to be visualized")
    description: Optional[str] = Field(None, description="Optional analytical summary or subtitle")
    metadata: Optional[ChartMetadata] = Field(None, description="Visual and provenance metadata")

    @field_validator("chart_type")
    @classmethod
    def validate_chart_type(cls, val: str) -> str:
        """Enforces supported chart type enumeration."""
        normalized = val.strip().lower()
        if normalized not in SUPPORTED_CHART_TYPES:
            raise ValueError(
                f"Unsupported chart type '{val}'. Supported types are: {sorted(list(SUPPORTED_CHART_TYPES))}"
            )
        return normalized

    @model_validator(mode="after")
    def validate_dataset_and_keys(self) -> ChartSpec:
        """Validates key existence, numeric integrity, and dataset shape."""
        # Initialize metadata if not present
        if self.metadata is None:
            self.metadata = ChartMetadata(
                total_points=len(self.data),
                is_empty=(len(self.data) == 0),
            )
        else:
            self.metadata.total_points = len(self.data)
            self.metadata.is_empty = (len(self.data) == 0)

        # Empty dataset check: empty data is allowed, but marked in metadata
        if not self.data:
            return self

        # Determine all required y keys
        all_y_keys = [self.y_key]
        if self.y_keys:
            for yk in self.y_keys:
                if yk not in all_y_keys:
                    all_y_keys.append(yk)

        # Validate first row and all rows
        for idx, row in enumerate(self.data):
            if not isinstance(row, dict):
                raise ValueError(f"Record at index {idx} must be a dictionary, got {type(row).__name__}")

            # Check x_key existence
            if self.x_key not in row:
                available = list(row.keys())
                raise ValueError(
                    f"Record at index {idx} missing required x_key '{self.x_key}'. Available keys: {available}"
                )

            # Check all y_keys existence and numeric validity
            for yk in all_y_keys:
                if yk not in row:
                    available = list(row.keys())
                    raise ValueError(
                        f"Record at index {idx} missing required y_key '{yk}'. Available keys: {available}"
                    )

                val = row[yk]
                if val is None:
                    # Treat None as 0.0 or allow it as null data point
                    continue

                if isinstance(val, (int, float, Decimal)):
                    continue

                # If string, verify it can be converted to float
                if isinstance(val, str):
                    try:
                        float(val)
                    except ValueError:
                        raise ValueError(
                            f"Record at index {idx} key '{yk}' must be numeric, got non-numeric string '{val}'"
                        )
                else:
                    raise ValueError(
                        f"Record at index {idx} key '{yk}' must be numeric, got {type(val).__name__} ({val})"
                    )

        return self


class ChartGenerationRequest(BaseModel):
    """API request payload for generating dynamic chart specifications."""
    query: Optional[str] = Field(None, description="Natural language chart query (e.g. 'Show monthly revenue as a chart')")
    chart_type: Optional[str] = Field(None, description="Explicit override for chart type (line, bar, pie, area)")
    domain: Optional[str] = Field(None, description="Analytical domain: sales, products, customers")
    metric: Optional[str] = Field(None, description="Metric type: monthly_revenue, category_revenue, top_products")
    start_date: Optional[str] = Field(None, description="Start date filter (YYYY-MM-DD)")
    end_date: Optional[str] = Field(None, description="End date filter (YYYY-MM-DD)")
    limit: Optional[int] = Field(5, ge=1, le=50, description="Top N item limit for rankings")


class ChartValidationResult(BaseModel):
    """Output summary of chart specification validation."""
    is_valid: bool = Field(..., description="Whether the chart specification satisfies all integrity rules")
    chart_spec: Optional[ChartSpec] = Field(None, description="The validated chart specification if valid")
    error: Optional[str] = Field(None, description="Primary validation error message if invalid")
    details: Dict[str, Any] = Field(default_factory=dict, description="Detailed validation breakdown")
