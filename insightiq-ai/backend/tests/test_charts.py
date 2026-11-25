"""Comprehensive Backend Test Suite for Dynamic Chart Generation and Validation."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.database.session import get_db
from app.main import app
from app.schemas.charts import (
    ChartMetadata,
    ChartSpec,
    ChartType,
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


# -----------------------------------------------------------------------------
# 1. Chart Specification Schema Validation Unit Tests
# -----------------------------------------------------------------------------
def test_valid_chart_spec_creation():
    """Verifies that a valid chart specification passes validation."""
    data = [
        {"month": "2024-01", "revenue": 1000.0, "units": 10},
        {"month": "2024-02", "revenue": 1500.50, "units": 15},
    ]
    spec = ChartSpec(
        chart_type="line",
        title="Monthly Revenue Trend",
        x_key="month",
        y_key="revenue",
        y_keys=["revenue", "units"],
        data=data,
    )
    assert spec.chart_type == "line"
    assert spec.title == "Monthly Revenue Trend"
    assert len(spec.data) == 2
    assert spec.metadata.total_points == 2
    assert spec.metadata.is_empty is False


def test_chart_spec_unsupported_type_raises():
    """Verifies that invalid or unsupported chart types are rejected."""
    with pytest.raises(ValueError, match="Unsupported chart type 'scatter'"):
        ChartSpec(
            chart_type="scatter",
            title="Scatter Chart",
            x_key="x",
            y_key="y",
            data=[{"x": 1, "y": 2}],
        )


def test_chart_spec_missing_x_key_raises():
    """Verifies that a missing x_key in data records is rejected."""
    data = [{"wrong_key": "2024-01", "revenue": 100.0}]
    with pytest.raises(ValueError, match="missing required x_key 'month'"):
        ChartSpec(
            chart_type="bar",
            title="Revenue",
            x_key="month",
            y_key="revenue",
            data=data,
        )


def test_chart_spec_missing_y_key_raises():
    """Verifies that a missing y_key in data records is rejected."""
    data = [{"month": "2024-01", "wrong_metric": 100.0}]
    with pytest.raises(ValueError, match="missing required y_key 'revenue'"):
        ChartSpec(
            chart_type="bar",
            title="Revenue",
            x_key="month",
            y_key="revenue",
            data=data,
        )


def test_chart_spec_non_numeric_y_value_raises():
    """Verifies that non-numeric values in quantitative keys are rejected."""
    data = [
        {"month": "2024-01", "revenue": 100.0},
        {"month": "2024-02", "revenue": "NOT_A_NUMBER"},
    ]
    with pytest.raises(ValueError, match="must be numeric"):
        ChartSpec(
            chart_type="line",
            title="Revenue",
            x_key="month",
            y_key="revenue",
            data=data,
        )


def test_chart_spec_numeric_string_conversion():
    """Verifies that string representations of numbers are safely accepted."""
    data = [{"month": "2024-01", "revenue": "1250.75"}]
    spec = ChartSpec(
        chart_type="line",
        title="Revenue",
        x_key="month",
        y_key="revenue",
        data=data,
    )
    assert len(spec.data) == 1
    assert spec.data[0]["revenue"] == "1250.75"


def test_chart_spec_empty_dataset_handling():
    """Verifies that an empty dataset is valid and flagged with is_empty=True."""
    spec = ChartSpec(
        chart_type="bar",
        title="Empty Bar Chart",
        x_key="category",
        y_key="revenue",
        data=[],
    )
    assert spec.data == []
    assert spec.metadata.is_empty is True
    assert spec.metadata.total_points == 0


def test_validate_chart_specification_helper():
    """Tests the standalone validation helper function."""
    valid_payload = {
        "chart_type": "pie",
        "title": "Category Revenue",
        "x_key": "category",
        "y_key": "revenue",
        "data": [{"category": "Electronics", "revenue": 500.0}],
    }
    res = validate_chart_specification(valid_payload)
    assert res.is_valid is True
    assert res.chart_spec.chart_type == "pie"

    # Unsupported visualization
    invalid_type = {**valid_payload, "chart_type": "radar"}
    res_bad = validate_chart_specification(invalid_type)
    assert res_bad.is_valid is False
    assert "Unsupported chart visualization 'radar'" in res_bad.error

    # Missing required keys
    invalid_keys = {**valid_payload, "data": [{"cat": "Electronics", "rev": 500.0}]}
    res_missing = validate_chart_specification(invalid_keys)
    assert res_missing.is_valid is False
    assert "missing required x_key" in res_missing.error


# -----------------------------------------------------------------------------
# 2. Database Analytics Chart Service Integration Tests
# -----------------------------------------------------------------------------
def test_build_monthly_revenue_chart(seeded_db_session):
    """Verifies monthly revenue chart generation against actual test warehouse data."""
    chart = build_monthly_revenue_chart(seeded_db_session, chart_type="line")
    assert chart.chart_type == "line"
    assert chart.title == "Monthly Revenue"
    assert chart.x_key == "month"
    assert chart.y_key == "revenue"
    assert len(chart.data) >= 3

    # Ground truth reference checks (Jan: 1220, Feb: 1210, Mar: 60)
    months = [r["month"] for r in chart.data]
    assert "2024-01" in months
    assert "2024-02" in months
    assert "2024-03" in months

    # Validate numbers are floats, not Decimals
    for r in chart.data:
        assert isinstance(r["revenue"], float)
        assert r["revenue"] >= 0.0


def test_build_category_revenue_chart(seeded_db_session):
    """Verifies category revenue chart generation (pie format)."""
    chart = build_category_revenue_chart(seeded_db_session, chart_type="pie")
    assert chart.chart_type == "pie"
    assert chart.title == "Revenue by Category"
    assert chart.x_key == "category"
    assert chart.y_key == "revenue"
    assert len(chart.data) >= 2

    categories = [r["category"] for r in chart.data]
    assert "Electronics" in categories
    assert "Apparel" in categories


def test_build_top_products_chart(seeded_db_session):
    """Verifies ranked bar chart generation for top products."""
    chart = build_top_products_chart(seeded_db_session, limit=5, sort_by="revenue")
    assert chart.chart_type == "bar"
    assert "Top 5 Products" in chart.title
    assert chart.x_key == "product_name"
    assert chart.y_key == "revenue"
    assert len(chart.data) <= 5

    # Check units sort option
    chart_units = build_top_products_chart(seeded_db_session, limit=3, sort_by="units")
    assert chart_units.y_key == "units_sold"
    assert len(chart_units.data) <= 3


def test_generate_chart_from_query_monthly(seeded_db_session):
    """Verifies natural language dispatch for 'Show monthly revenue as a chart.'"""
    chart = generate_chart_from_query(seeded_db_session, query="Show monthly revenue as a chart.")
    assert chart.chart_type in ("line", "area")
    assert chart.x_key == "month"
    assert chart.y_key == "revenue"
    assert len(chart.data) >= 3


def test_generate_chart_from_query_category(seeded_db_session):
    """Verifies natural language dispatch for 'Compare revenue by category.'"""
    chart = generate_chart_from_query(seeded_db_session, query="Compare revenue by category.")
    assert chart.chart_type in ("pie", "bar")
    assert chart.x_key == "category"
    assert chart.y_key == "revenue"
    assert len(chart.data) >= 2


def test_generate_chart_from_query_top_products(seeded_db_session):
    """Verifies natural language dispatch for 'Show top five products by revenue.'"""
    chart = generate_chart_from_query(seeded_db_session, query="Show top five products by revenue.")
    assert chart.chart_type == "bar"
    assert chart.x_key == "product_name"
    assert chart.y_key == "revenue"
    assert len(chart.data) <= 5


def test_generate_chart_from_query_unsupported_visualization(seeded_db_session):
    """Verifies graceful rejection of unsupported visualization formats."""
    with pytest.raises(ValueError, match="Visualization format 'scatter' is not currently supported"):
        generate_chart_from_query(seeded_db_session, query="Show a scatter plot of revenue vs orders")

    with pytest.raises(ValueError, match="Visualization format '3d' is not currently supported"):
        generate_chart_from_query(seeded_db_session, query="Generate a 3D surface plot of products")


# -----------------------------------------------------------------------------
# 3. FastAPI Chart REST Endpoints Integration Tests
# -----------------------------------------------------------------------------
@pytest.fixture
def client(seeded_db_session):
    """Provides a FastAPI TestClient with the get_db dependency overridden by the seeded session."""
    def override_get_db():
        yield seeded_db_session

    app.dependency_overrides[get_db] = override_get_db
    test_client = TestClient(app, raise_server_exceptions=False)
    yield test_client
    app.dependency_overrides.clear()


def test_api_get_monthly_revenue_chart(client):
    """Tests GET /api/charts/monthly-revenue endpoint."""
    resp = client.get("/api/charts/monthly-revenue?chart_type=line")
    assert resp.status_code == 200
    data = resp.json()
    assert data["chart_type"] == "line"
    assert data["x_key"] == "month"
    assert data["y_key"] == "revenue"
    assert isinstance(data["data"], list)
    assert len(data["data"]) > 0


def test_api_get_category_revenue_chart(client):
    """Tests GET /api/charts/category-revenue endpoint."""
    resp = client.get("/api/charts/category-revenue?chart_type=pie")
    assert resp.status_code == 200
    data = resp.json()
    assert data["chart_type"] == "pie"
    assert data["x_key"] == "category"
    assert data["y_key"] == "revenue"
    assert len(data["data"]) > 0


def test_api_get_top_products_chart(client):
    """Tests GET /api/charts/top-products endpoint."""
    resp = client.get("/api/charts/top-products?limit=3&sort_by=revenue")
    assert resp.status_code == 200
    data = resp.json()
    assert data["chart_type"] == "bar"
    assert data["x_key"] == "product_name"
    assert data["y_key"] == "revenue"
    assert len(data["data"]) <= 3


def test_api_generate_chart_from_query(client):
    """Tests POST /api/charts/generate endpoint with natural language query."""
    resp = client.post(
        "/api/charts/generate",
        json={"query": "Show monthly revenue as a chart."},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["chart_type"] in ("line", "area")
    assert data["x_key"] == "month"
    assert data["y_key"] == "revenue"


def test_api_generate_chart_unsupported_query(client):
    """Tests POST /api/charts/generate with unsupported chart format."""
    resp = client.post(
        "/api/charts/generate",
        json={"query": "Draw a heatmap of customer transactions."},
    )
    assert resp.status_code == 400
    assert "not currently supported" in resp.json()["detail"]


def test_api_validate_chart_endpoint(client):
    """Tests POST /api/charts/validate endpoint."""
    valid_payload = {
        "chart_type": "bar",
        "title": "Category Sales",
        "x_key": "category",
        "y_key": "revenue",
        "data": [{"category": "Books", "revenue": 120.0}],
    }
    resp = client.post("/api/charts/validate", json=valid_payload)
    assert resp.status_code == 200
    assert resp.json()["is_valid"] is True

    invalid_payload = {
        "chart_type": "radar",
        "title": "Bad Radar",
        "x_key": "category",
        "y_key": "revenue",
        "data": [{"category": "Books", "revenue": 120.0}],
    }
    resp_bad = client.post("/api/charts/validate", json=invalid_payload)
    assert resp_bad.status_code == 200
    assert resp_bad.json()["is_valid"] is False
    assert "Unsupported chart visualization" in resp_bad.json()["error"]


def test_build_sales_trend_chart(seeded_db_session):
    """Verifies customer orders & sales trend chart specification."""
    chart = build_sales_trend_chart(seeded_db_session, chart_type="bar")
    assert chart.chart_type == "bar"
    assert "Customer Orders & Sales Volume Trend" in chart.title
    assert chart.x_key == "month"
    assert chart.y_key == "order_count"
    assert "units_sold" in chart.y_keys
    assert len(chart.data) >= 3


def test_api_get_sales_trend_chart(client):
    """Tests GET /api/charts/sales-trend endpoint."""
    resp = client.get("/api/charts/sales-trend?chart_type=bar")
    assert resp.status_code == 200
    data = resp.json()
    assert data["chart_type"] == "bar"
    assert data["x_key"] == "month"
    assert data["y_key"] == "order_count"
    assert len(data["data"]) >= 3
