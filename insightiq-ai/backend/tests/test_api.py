"""Integration tests for FastAPI REST API endpoints using TestClient."""

from decimal import Decimal
import pytest
from fastapi.testclient import TestClient

from app.database.session import get_db
from app.main import app


@pytest.fixture
def client(seeded_db_session):
    """Provides a FastAPI TestClient with the get_db dependency overridden by the seeded session."""
    def override_get_db():
        yield seeded_db_session

    app.dependency_overrides[get_db] = override_get_db
    test_client = TestClient(app)
    yield test_client
    app.dependency_overrides.clear()


# -------------------------------------------------------------
# 1. Health Endpoints
# -------------------------------------------------------------

def test_health_check_endpoints(client):
    res_root = client.get("/health")
    assert res_root.status_code == 200
    assert res_root.json()["status"] == "ok"
    assert res_root.json()["database"] == "connected"

    res_api = client.get("/api/health")
    assert res_api.status_code == 200
    assert res_api.json()["status"] == "ok"


def test_root_metadata_endpoint(client):
    res = client.get("/")
    assert res.status_code == 200
    data = res.json()
    assert data["name"] == "InsightIQ AI API"
    assert data["status"] == "online"


# -------------------------------------------------------------
# 2. Dashboard Endpoint
# -------------------------------------------------------------

def test_get_dashboard_summary_endpoint(client):
    res = client.get("/api/dashboard?start_date=2024-01-01&end_date=2024-03-31")
    assert res.status_code == 200
    data = res.json()

    assert "kpis" in data
    assert Decimal(str(data["kpis"]["total_revenue"])) == Decimal("2490.00")
    assert data["kpis"]["total_orders"] == 5
    assert Decimal(str(data["kpis"]["average_order_value"])) == Decimal("498.00")

    assert "customer_summary" in data
    assert "monthly_trend" in data
    assert len(data["monthly_trend"]) == 3
    assert "category_distribution" in data
    assert len(data["category_distribution"]) == 2
    assert "top_products" in data
    assert len(data["top_products"]) <= 5


# -------------------------------------------------------------
# 3. Sales Endpoints
# -------------------------------------------------------------

def test_sales_metrics_endpoint(client):
    res = client.get("/api/sales/metrics?start_date=2024-01-01&end_date=2024-03-31")
    assert res.status_code == 200
    data = res.json()
    assert Decimal(str(data["total_revenue"])) == Decimal("2490.00")
    assert data["total_orders"] == 5
    assert Decimal(str(data["aov"])) == Decimal("498.00")


def test_sales_monthly_endpoint(client):
    res = client.get("/api/sales/monthly?start_date=2024-01-01&end_date=2024-03-31")
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 3
    assert data[0]["month"] == "2024-01"
    assert Decimal(str(data[0]["revenue"])) == Decimal("1220.00")


def test_sales_categories_endpoint(client):
    res = client.get("/api/sales/categories?start_date=2024-01-01&end_date=2024-03-31")
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 2
    assert data[0]["category"] == "Electronics"
    assert Decimal(str(data[0]["revenue"])) == Decimal("2150.00")


def test_sales_products_endpoint(client):
    res = client.get("/api/sales/products?limit=2&start_date=2024-01-01&end_date=2024-03-31")
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 2
    assert data[0]["product_id"] == 1
    assert Decimal(str(data[0]["revenue"])) == Decimal("2000.00")


def test_sales_growth_endpoint(client):
    res = client.get(
        "/api/sales/growth?current_start=2024-02-01&current_end=2024-02-29&previous_start=2024-01-01&previous_end=2024-01-31"
    )
    assert res.status_code == 200
    data = res.json()
    assert "current_period" in data
    assert "previous_period" in data
    assert data["revenue_growth_pct"] == pytest.approx(-0.82, rel=1e-2)


# -------------------------------------------------------------
# 4. Product Endpoints
# -------------------------------------------------------------

def test_products_top_endpoint(client):
    # Sort by revenue
    res_rev = client.get("/api/products/top?limit=3&sort_by=revenue&start_date=2024-01-01&end_date=2024-03-31")
    assert res_rev.status_code == 200
    data_rev = res_rev.json()
    assert len(data_rev) == 3
    assert data_rev[0]["product_id"] == 1
    assert Decimal(str(data_rev[0]["revenue"])) == Decimal("2000.00")

    # Sort by units
    res_units = client.get("/api/products/top?limit=3&sort_by=units&start_date=2024-01-01&end_date=2024-03-31")
    assert res_units.status_code == 200
    data_units = res_units.json()
    assert len(data_units) == 3
    assert data_units[0]["product_id"] == 4
    assert data_units[0]["units_sold"] == 5


def test_products_low_performing_endpoint(client):
    res = client.get("/api/products/low-performing?limit=3&start_date=2024-01-01&end_date=2024-03-31")
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 3
    # P5 (Book) has 0 revenue
    assert data[0]["product_id"] == 5
    assert Decimal(str(data[0]["revenue"])) == Decimal("0.00")


def test_product_detail_endpoint(client):
    res = client.get("/api/products/1?start_date=2024-01-01&end_date=2024-03-31")
    assert res.status_code == 200
    data = res.json()
    assert data["product_id"] == 1
    assert data["product_name"] == "Pro Laptop 15"
    assert data["units_sold"] == 2
    assert Decimal(str(data["revenue"])) == Decimal("2000.00")


def test_product_detail_not_found(client):
    res = client.get("/api/products/9999")
    assert res.status_code == 404
    assert "not found" in res.json()["detail"].lower()


# -------------------------------------------------------------
# 5. Customer Endpoints
# -------------------------------------------------------------

def test_customer_metrics_endpoint(client):
    res = client.get("/api/customers/metrics?start_date=2024-01-01&end_date=2024-03-31&inactive_days=90")
    assert res.status_code == 200
    data = res.json()
    assert data["total_customers"] == 5
    assert data["repeat_customers"] == 1
    assert data["inactive_customers"] == 1


def test_customer_top_endpoint(client):
    res = client.get("/api/customers/top?limit=2&start_date=2024-01-01&end_date=2024-03-31")
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 2
    assert data[0]["customer_id"] == 1
    assert data[0]["name"] == "Alice Smith"
    assert Decimal(str(data[0]["total_spend"])) == Decimal("1260.00")


def test_customer_frequency_endpoint(client):
    res = client.get("/api/customers/frequency?start_date=2024-01-01&end_date=2024-03-31")
    assert res.status_code == 200
    data = res.json()
    assert data["one_order"] == 3
    assert data["two_to_three"] == 1
    assert data["average_orders_per_customer"] == 1.25


# -------------------------------------------------------------
# 6. Request Validation & Error Handling
# -------------------------------------------------------------

def test_inverted_date_range_validation_error(client):
    # start_date > end_date
    res = client.get("/api/sales/metrics?start_date=2024-12-31&end_date=2024-01-01")
    assert res.status_code == 400
    assert "cannot be greater than" in res.json()["detail"]


def test_malformed_date_format_validation_error(client):
    res = client.get("/api/sales/metrics?start_date=not-a-valid-date")
    assert res.status_code == 400
    assert "Invalid start_date format" in res.json()["detail"]


def test_pydantic_query_param_validation(client):
    # limit must be >= 1
    res_neg_limit = client.get("/api/products/top?limit=-1")
    assert res_neg_limit.status_code == 422

    # sort_by must match regex ^(revenue|units)$
    res_invalid_sort = client.get("/api/products/top?sort_by=invalid_field")
    assert res_invalid_sort.status_code == 422
