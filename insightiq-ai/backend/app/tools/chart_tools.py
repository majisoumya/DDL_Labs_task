"""Interactive Chart Specification Tool for React / Recharts Visualization."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict
from app.tools.registry import default_tool_registry
from app.tools.schemas import GenerateChartSpecInput


@default_tool_registry.register(
    name="generate_chart_spec",
    description="Generates a structured visualization specification for rendering dynamic business charts (line, bar, pie, or area) in the user interface.",
    input_schema=GenerateChartSpecInput,
    requires_db=False,
)
def tool_generate_chart_spec(args: GenerateChartSpecInput) -> Dict[str, Any]:
    """Validates and packages dataset records into a standardized chart spec."""
    # Verify that x_key and y_keys exist in the provided data sample
    if args.data:
        sample_keys = set(args.data[0].keys())
        if args.x_key not in sample_keys:
            raise ValueError(f"x_key '{args.x_key}' is missing from data records. Available: {list(sample_keys)}")
        keys_to_check = args.y_keys or ([args.y_key] if args.y_key else [])
        for yk in keys_to_check:
            if yk not in sample_keys:
                raise ValueError(f"y_key '{yk}' is missing from data records. Available: {list(sample_keys)}")

    primary_y = args.y_key or (args.y_keys[0] if args.y_keys else "value")

    return {
        "chart_type": args.chart_type.value,
        "title": args.title,
        "x_key": args.x_key,
        "y_key": primary_y,
        "y_keys": args.y_keys or [primary_y],
        "data": args.data,
        "description": args.description,
        "metadata": {
            "total_points": len(args.data),
            "generated_at": datetime.now(timezone.utc).isoformat(),
        },
    }
