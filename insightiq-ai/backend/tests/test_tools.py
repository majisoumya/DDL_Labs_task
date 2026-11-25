"""Unit and Integration Tests for Controlled AI Tool Calling Registry and Analytics Tools."""

from decimal import Decimal
import json
import pytest
from app.tools.registry import default_tool_registry
from app.tools.schemas import ChartType, ToolExecutionResult


# -----------------------------------------------------------------------------
# 1. Tool Registry & OpenAI Schema Definition Tests
# -----------------------------------------------------------------------------
def test_all_expected_tools_registered():
    """Verifies that all 13 core analytics and visualization tools are registered."""
    expected_tools = {
        "get_sales_metrics",
        "get_monthly_revenue",
        "get_revenue_by_category",
        "get_revenue_by_product",
        "get_sales_growth",
        "get_customer_metrics",
        "get_top_customers",
        "get_customer_order_frequency",
        "get_top_products",
        "get_low_performing_products",
        "get_product_detail",
        "get_dashboard_summary",
        "generate_chart_spec",
    }
    registered = {t.name for t in default_tool_registry.list_tools()}
    assert expected_tools.issubset(registered)


def test_openai_tool_schema_export():
    """Verifies that to_openai_tools returns valid OpenAI function calling specifications."""
    openai_tools = default_tool_registry.to_openai_tools()
    assert len(openai_tools) >= 13

    for tool in openai_tools:
        assert tool["type"] == "function"
        fn = tool["function"]
        assert "name" in fn and len(fn["name"]) > 0
        assert "description" in fn and len(fn["description"]) > 10
        assert "parameters" in fn
        params = fn["parameters"]
        assert params["type"] == "object"
        assert "properties" in params


# -----------------------------------------------------------------------------
# 2. Sales Tools Execution Tests (Deterministic Ground Truth)
# -----------------------------------------------------------------------------
def test_tool_get_sales_metrics(seeded_db_session):
    """Tests get_sales_metrics tool invocation and output formatting."""
    args = {"start_date": "2024-01-01", "end_date": "2024-03-31"}
    res = default_tool_registry.execute_tool("get_sales_metrics", args, db=seeded_db_session)

    assert isinstance(res, ToolExecutionResult)
    assert res.success is True
    assert res.error is None
    assert res.execution_time_ms > 0
    data = res.data
    assert data["total_revenue"] == 2490.00
    assert data["total_orders"] == 5
    assert data["aov"] == 498.00


def test_tool_get_monthly_revenue(seeded_db_session):
    """Tests get_monthly_revenue tool execution."""
    args = {"start_date": "2024-01-01", "end_date": "2024-03-31"}
    res = default_tool_registry.execute_tool("get_monthly_revenue", args, db=seeded_db_session)

    assert res.success is True
    assert len(res.data) == 3
    assert res.data[0]["month"] == "2024-01"
    assert res.data[0]["revenue"] == 1220.00


def test_tool_get_revenue_by_category(seeded_db_session):
    """Tests get_revenue_by_category tool execution."""
    args = {"start_date": "2024-01-01", "end_date": "2024-03-31"}
    res = default_tool_registry.execute_tool("get_revenue_by_category", args, db=seeded_db_session)
    assert res.success is True
    categories = {row["category"]: row["revenue"] for row in res.data}
    assert categories["Electronics"] == 2150.00
    assert categories["Apparel"] == 340.00


def test_tool_get_sales_growth(seeded_db_session):
    """Tests get_sales_growth tool calculating period comparison."""
    args = {
        "current_start": "2024-02-01",
        "current_end": "2024-02-29",
        "previous_start": "2024-01-01",
        "previous_end": "2024-01-31",
    }
    res = default_tool_registry.execute_tool("get_sales_growth", args, db=seeded_db_session)
    assert res.success is True
    assert res.data["current_period"]["revenue"] == 1210.00
    assert res.data["previous_period"]["revenue"] == 1220.00
    assert res.data["revenue_growth_pct"] == -0.82


def test_tool_get_dashboard_summary(seeded_db_session):
    """Tests executive dashboard summary tool."""
    res = default_tool_registry.execute_tool("get_dashboard_summary", {}, db=seeded_db_session)
    assert res.success is True
    assert "kpis" in res.data
    assert "monthly_trend" in res.data
    assert "category_distribution" in res.data


# -----------------------------------------------------------------------------
# 3. Customer Tools Execution Tests
# -----------------------------------------------------------------------------
def test_tool_get_customer_metrics(seeded_db_session):
    """Tests customer metrics tool invocation."""
    args = {"inactive_days": 90}
    res = default_tool_registry.execute_tool("get_customer_metrics", args, db=seeded_db_session)
    assert res.success is True
    data = res.data
    assert data["total_customers"] == 5
    assert data["repeat_customers"] == 1
    assert data["inactive_customers"] == 1


def test_tool_get_top_customers(seeded_db_session):
    """Tests ranking top customers with safe limit."""
    args = {"limit": 3}
    res = default_tool_registry.execute_tool("get_top_customers", args, db=seeded_db_session)
    assert res.success is True
    assert len(res.data) <= 3
    assert res.data[0]["name"] == "Alice Smith"
    assert res.data[0]["total_spend"] == 1260.00


def test_tool_get_customer_order_frequency(seeded_db_session):
    """Tests customer frequency distribution tool."""
    args = {"start_date": "2024-01-01", "end_date": "2024-03-31"}
    res = default_tool_registry.execute_tool("get_customer_order_frequency", args, db=seeded_db_session)
    assert res.success is True
    assert res.data["one_order"] == 3
    assert res.data["two_to_three"] == 1


# -----------------------------------------------------------------------------
# 4. Product Tools Execution Tests
# -----------------------------------------------------------------------------
def test_tool_get_top_products_by_revenue_and_units(seeded_db_session):
    """Tests top products tool sorting by revenue vs units."""
    # By revenue
    res_rev = default_tool_registry.execute_tool(
        "get_top_products", {"sort_by": "revenue", "limit": 2}, db=seeded_db_session
    )
    assert res_rev.success is True
    assert res_rev.data[0]["product_name"] == "Pro Laptop 15"

    # By units
    res_units = default_tool_registry.execute_tool(
        "get_top_products", {"sort_by": "units", "limit": 5}, db=seeded_db_session
    )
    assert res_units.success is True
    assert len(res_units.data) >= 1


def test_tool_get_low_performing_products(seeded_db_session):
    """Tests low performing products tool detects zero-sales items."""
    res = default_tool_registry.execute_tool(
        "get_low_performing_products", {"threshold_revenue": 100.0}, db=seeded_db_session
    )
    assert res.success is True
    product_names = [p["product_name"] for p in res.data]
    assert "Zero Sales Book" in product_names


def test_tool_get_product_detail(seeded_db_session):
    """Tests granular product performance tool."""
    res = default_tool_registry.execute_tool("get_product_detail", {"product_id": 1}, db=seeded_db_session)
    assert res.success is True
    assert res.data["product_id"] == 1
    assert res.data["product_name"] == "Pro Laptop 15"
    assert res.data["revenue"] == 2000.00


# -----------------------------------------------------------------------------
# 5. Chart Visualization Tool Tests
# -----------------------------------------------------------------------------
def test_tool_generate_chart_spec():
    """Tests chart specification generator tool."""
    chart_args = {
        "chart_type": "bar",
        "title": "Revenue by Category",
        "x_key": "category",
        "y_keys": ["revenue"],
        "data": [
            {"category": "Electronics", "revenue": 2150.00},
            {"category": "Apparel", "revenue": 340.00},
        ],
        "description": "Electronics leads with 86.35% market share.",
    }
    res = default_tool_registry.execute_tool("generate_chart_spec", chart_args)
    assert res.success is True
    assert res.data["chart_type"] == "bar"
    assert res.data["title"] == "Revenue by Category"
    assert res.data["metadata"]["total_points"] == 2


def test_tool_generate_chart_spec_missing_key_error():
    """Verifies that missing x_key or y_key in data sample returns an execution error."""
    chart_args = {
        "chart_type": "line",
        "title": "Monthly Trend",
        "x_key": "non_existent_key",
        "y_keys": ["revenue"],
        "data": [{"month": "2024-01", "revenue": 1200.00}],
    }
    res = default_tool_registry.execute_tool("generate_chart_spec", chart_args)
    assert res.success is False
    assert "missing from data records" in res.error


# -----------------------------------------------------------------------------
# 6. Argument Validation & Safety Boundary Tests
# -----------------------------------------------------------------------------
def test_invalid_date_format_rejected(seeded_db_session):
    """Verifies that malformed date strings fail validation with clear errors."""
    res = default_tool_registry.execute_tool(
        "get_sales_metrics", {"start_date": "not-a-date"}, db=seeded_db_session
    )
    assert res.success is False
    assert "Invalid date format" in res.error


def test_inverted_date_range_rejected(seeded_db_session):
    """Verifies that start_date > end_date fails validation."""
    res = default_tool_registry.execute_tool(
        "get_sales_metrics",
        {"start_date": "2024-12-31", "end_date": "2024-01-01"},
        db=seeded_db_session,
    )
    assert res.success is False
    assert "cannot be greater than end_date" in res.error


def test_top_n_limits_enforced(seeded_db_session):
    """Verifies that limit must be within [1, 100]."""
    # Over maximum (limit=500 > 100)
    res_high = default_tool_registry.execute_tool(
        "get_top_customers", {"limit": 500}, db=seeded_db_session
    )
    assert res_high.success is False
    assert "less than or equal to 100" in res_high.error

    # Below minimum (limit=0 < 1)
    res_low = default_tool_registry.execute_tool(
        "get_top_customers", {"limit": 0}, db=seeded_db_session
    )
    assert res_low.success is False
    assert "greater than or equal to 1" in res_low.error


def test_unknown_tool_rejected(seeded_db_session):
    """Verifies that arbitrary or unknown tool calls are blocked."""
    res = default_tool_registry.execute_tool("execute_raw_sql", {"sql": "DROP TABLE users"}, db=seeded_db_session)
    assert res.success is False
    assert "not an approved analytics tool" in res.error


def test_json_string_argument_parsing(seeded_db_session):
    """Verifies that raw JSON string arguments from LLM tool calls parse seamlessly."""
    raw_json_str = json.dumps({"start_date": "2024-01-01", "end_date": "2024-03-31"})
    res = default_tool_registry.execute_tool("get_sales_metrics", raw_json_str, db=seeded_db_session)
    assert res.success is True
    assert res.data["total_revenue"] == 2490.00


def test_missing_database_session_rejected():
    """Verifies that analytics tools requiring DB fail cleanly if session is omitted."""
    res = default_tool_registry.execute_tool("get_sales_metrics", {})
    assert res.success is False
    assert "requires an active database session" in res.error


def test_json_serializability_guaranteed(seeded_db_session):
    """Verifies that tool results are 100% JSON serializable (no Decimals or unsupported types)."""
    res = default_tool_registry.execute_tool("get_sales_metrics", {}, db=seeded_db_session)
    assert res.success is True
    # json.dumps must not raise TypeError for Decimal
    serialized = json.dumps(res.data)
    assert isinstance(serialized, str)
