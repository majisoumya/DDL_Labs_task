"""Dynamic Chart Generation and Validation Service for InsightIQ AI.

Produces validated, Recharts-compatible chart specifications backed strictly by actual
database analytics. Never invents or generates fake chart data points.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from app.logging_config import get_logger
from app.schemas.charts import (
    SUPPORTED_CHART_TYPES,
    ChartMetadata,
    ChartSpec,
    ChartType,
    ChartValidationResult,
)
from app.services.product_service import (
    get_highest_revenue_products,
    get_top_selling_products,
)
from app.services.sales_service import (
    get_monthly_revenue,
    get_revenue_by_category,
)

logger = get_logger("insightiq.services.charts")


def validate_chart_specification(spec_data: Dict[str, Any]) -> ChartValidationResult:
    """Validates an arbitrary chart specification dictionary against integrity rules.

    Checks:
    - Valid and supported chart_type (line, bar, pie, area)
    - Valid data shape (list of dicts)
    - Axis key existence in all data points
    - Numeric validity for value keys
    - Graceful empty dataset handling
    """
    try:
        if not isinstance(spec_data, dict):
            return ChartValidationResult(
                is_valid=False,
                error="Chart specification must be a dictionary object.",
                details={"input_type": type(spec_data).__name__},
            )

        chart_type = spec_data.get("chart_type")
        if not chart_type or str(chart_type).lower() not in SUPPORTED_CHART_TYPES:
            supported_list = sorted(list(SUPPORTED_CHART_TYPES))
            return ChartValidationResult(
                is_valid=False,
                error=(
                    f"Unsupported chart visualization '{chart_type}'. "
                    f"Supported types are: {', '.join(supported_list)}."
                ),
                details={"chart_type": chart_type, "supported_types": supported_list},
            )

        data = spec_data.get("data")
        if not isinstance(data, list):
            return ChartValidationResult(
                is_valid=False,
                error="Chart 'data' must be a list of record objects.",
                details={"data_type": type(data).__name__},
            )

        # Parse with Pydantic ChartSpec (which performs deep validation)
        spec = ChartSpec(**spec_data)
        return ChartValidationResult(
            is_valid=True,
            chart_spec=spec,
            details={"total_points": len(spec.data), "is_empty": len(spec.data) == 0},
        )

    except ValueError as exc:
        return ChartValidationResult(
            is_valid=False,
            error=str(exc),
            details={"raw_error": str(exc)},
        )
    except Exception as exc:
        logger.error("Unexpected chart validation error: %s", exc, exc_info=True)
        return ChartValidationResult(
            is_valid=False,
            error=f"Validation failed: {exc}",
            details={"exception": str(exc)},
        )


def _serialize_decimals(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Converts Decimal objects into floats for standard JSON and Recharts compatibility."""
    clean_records: List[Dict[str, Any]] = []
    for row in records:
        clean_row: Dict[str, Any] = {}
        for k, v in row.items():
            if isinstance(v, Decimal):
                clean_row[k] = float(v)
            else:
                clean_row[k] = v
        clean_records.append(clean_row)
    return clean_records


def build_monthly_revenue_chart(
    db: Session,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    chart_type: str = "line",
) -> ChartSpec:
    """Builds a validated time-series chart specification for monthly revenue."""
    norm_type = chart_type.lower()
    if norm_type not in ("line", "area", "bar"):
        norm_type = "line"

    raw_data = get_monthly_revenue(db, start_date=start_date, end_date=end_date)
    clean_data = _serialize_decimals(raw_data)

    spec = ChartSpec(
        chart_type=norm_type,
        title="Monthly Revenue",
        x_key="month",
        y_key="revenue",
        y_keys=["revenue", "units_sold"],
        data=clean_data,
        description="Chronological earned revenue trajectory (excluding cancelled/returned orders)",
        metadata=ChartMetadata(
            x_label="Month (YYYY-MM)",
            y_label="Revenue ($)",
            unit="$",
            source_tool="get_monthly_revenue",
        ),
    )
    return spec


def build_category_revenue_chart(
    db: Session,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    chart_type: str = "pie",
) -> ChartSpec:
    """Builds a validated categorical distribution chart specification (Pie or Bar)."""
    norm_type = chart_type.lower()
    if norm_type not in ("pie", "bar"):
        norm_type = "pie"

    raw_data = get_revenue_by_category(db, start_date=start_date, end_date=end_date)
    clean_data = _serialize_decimals(raw_data)

    spec = ChartSpec(
        chart_type=norm_type,
        title="Revenue by Category",
        x_key="category",
        y_key="revenue",
        data=clean_data,
        description="Share of gross revenue across merchandising categories",
        metadata=ChartMetadata(
            x_label="Category",
            y_label="Revenue ($)",
            unit="$",
            source_tool="get_revenue_by_category",
        ),
    )
    return spec


def build_top_products_chart(
    db: Session,
    limit: int = 5,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    sort_by: str = "revenue",
    chart_type: str = "bar",
) -> ChartSpec:
    """Builds a validated ranked bar chart specification for top products."""
    norm_type = chart_type.lower()
    if norm_type not in ("bar", "line"):
        norm_type = "bar"

    if sort_by == "units":
        raw_data = get_top_selling_products(db, limit=limit, start_date=start_date, end_date=end_date)
        y_key = "units_sold"
        y_label = "Units Sold"
        unit = "units"
    else:
        raw_data = get_highest_revenue_products(db, limit=limit, start_date=start_date, end_date=end_date)
        y_key = "revenue"
        y_label = "Revenue ($)"
        unit = "$"

    clean_data = _serialize_decimals(raw_data)

    spec = ChartSpec(
        chart_type=norm_type,
        title=f"Top {limit} Products by {sort_by.capitalize()}",
        x_key="product_name",
        y_key=y_key,
        data=clean_data,
        description=f"Catalog leaders ranked by cumulative {sort_by}",
        metadata=ChartMetadata(
            x_label="Product Name",
            y_label=y_label,
            unit=unit,
            source_tool="get_top_products",
        ),
    )
    return spec


def build_sales_trend_chart(
    db: Session,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    chart_type: str = "bar",
) -> ChartSpec:
    """Builds a validated chart spec showing customer orders and unit volume trends over time."""
    norm_type = chart_type.lower()
    if norm_type not in ("bar", "line", "area"):
        norm_type = "bar"

    raw_data = get_monthly_revenue(db, start_date=start_date, end_date=end_date)
    clean_data = _serialize_decimals(raw_data)

    spec = ChartSpec(
        chart_type=norm_type,
        title="Customer Orders & Sales Volume Trend",
        x_key="month",
        y_key="order_count",
        y_keys=["order_count", "units_sold"],
        data=clean_data,
        description="Monthly order frequency and product units fulfilled",
        metadata=ChartMetadata(
            x_label="Month (YYYY-MM)",
            y_label="Orders / Units",
            unit="orders",
            source_tool="get_monthly_revenue",
        ),
    )
    return spec


def generate_chart_from_query(
    db: Session,
    query: str,
    chart_type_override: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: Optional[int] = 5,
) -> ChartSpec:
    """Understands natural-language chart inquiries and dispatches to appropriate actual data queries.

    Handles prompts such as:
    - 'Show monthly revenue as a chart.'
    - 'Show top five products by revenue.'
    - 'Compare revenue by category.'
    """
    q_lower = query.strip().lower()

    # Detect unsupported visualization formats
    unsupported_types = ["scatter", "heatmap", "bubble", "radar", "3d", "candlestick", "tree", "treemap"]
    for ut in unsupported_types:
        if ut in q_lower:
            raise ValueError(
                f"Visualization format '{ut}' is not currently supported. "
                f"Please choose from supported formats: line, bar, pie, area."
            )

    # 1. Monthly Revenue Query
    if ("month" in q_lower or "trend" in q_lower or "time" in q_lower) and ("revenue" in q_lower or "sale" in q_lower):
        target_chart_type = chart_type_override or ("area" if "area" in q_lower else "line")
        return build_monthly_revenue_chart(
            db=db,
            start_date=start_date,
            end_date=end_date,
            chart_type=target_chart_type,
        )

    # 2. Category Comparison Query
    if "category" in q_lower or "categories" in q_lower:
        target_chart_type = chart_type_override or ("bar" if "bar" in q_lower else "pie")
        return build_category_revenue_chart(
            db=db,
            start_date=start_date,
            end_date=end_date,
            chart_type=target_chart_type,
        )

    # 3. Top Products Query
    if "product" in q_lower or "products" in q_lower or "item" in q_lower or "sku" in q_lower:
        # Extract limit if user specified number (e.g., 'top 5', 'top five', 'top 10')
        req_limit = limit or 5
        number_matches = re.findall(r"\b(?:top\s*)?(\d+)\b", q_lower)
        if number_matches:
            try:
                extracted = int(number_matches[0])
                if 1 <= extracted <= 25:
                    req_limit = extracted
            except ValueError:
                pass
        elif "five" in q_lower:
            req_limit = 5
        elif "three" in q_lower:
            req_limit = 3
        elif "ten" in q_lower:
            req_limit = 10

        sort_by = "units" if ("unit" in q_lower or "volume" in q_lower or "quantity" in q_lower) else "revenue"
        target_chart_type = chart_type_override or "bar"
        return build_top_products_chart(
            db=db,
            limit=req_limit,
            start_date=start_date,
            end_date=end_date,
            sort_by=sort_by,
            chart_type=target_chart_type,
        )

    # Default fallback: Monthly Revenue Trend
    target_chart_type = chart_type_override or "line"
    return build_monthly_revenue_chart(
        db=db,
        start_date=start_date,
        end_date=end_date,
        chart_type=target_chart_type,
    )
