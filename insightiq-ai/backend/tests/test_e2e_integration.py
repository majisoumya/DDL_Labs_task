"""Comprehensive End-to-End System Integration Tests for InsightIQ AI."""

import csv
from decimal import Decimal
import io
import pytest
from fastapi.testclient import TestClient

from app.database.session import get_db
from app.main import app
from app.services.sales_service import get_sales_metrics


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
# 1. Full Stack Ground-Truth Verification (DB -> Service -> API)
# -------------------------------------------------------------

def test_full_system_ground_truth_consistency(client, seeded_db_session):
    """Verifies that database records, service calculations, and API responses match exactly."""
    # 1. Direct Service Level (All-time dataset includes 2023 + 2024 eligible records = $2,540.00)
    sales_kpis = get_sales_metrics(seeded_db_session)
    assert Decimal(str(sales_kpis["total_revenue"])) == Decimal("2540.00")
    assert sales_kpis["total_orders"] == 6
    assert Decimal(str(sales_kpis["aov"])) == Decimal("423.33")

    # 2. Dashboard API Level
    dash_res = client.get("/api/dashboard")
    assert dash_res.status_code == 200
    dash_kpis = dash_res.json()["kpis"]
    assert Decimal(str(dash_kpis["total_revenue"])) == Decimal("2540.00")
    assert dash_kpis["total_orders"] == 6
    assert Decimal(str(dash_kpis["average_order_value"])) == Decimal("423.33")

    # 3. AI Analyst Chat API Level
    chat_res = client.post("/api/analyst/chat", json={"question": "What is our total revenue?"})
    assert chat_res.status_code == 200
    chat_data = chat_res.json()
    assert len(chat_data["tool_executions"]) >= 1

    # Extract verified metrics referenced
    metric_names = [m["metric_name"] for m in chat_data["metrics_referenced"]]
    assert "total_revenue" in metric_names
    rev_metric = next(m for m in chat_data["metrics_referenced"] if m["metric_name"] == "total_revenue")
    assert Decimal(str(rev_metric["exact_value"])) == Decimal("2540.00")


# -------------------------------------------------------------
# 2. CSV Export Endpoints (Sales, Products, Customers)
# -------------------------------------------------------------

def test_export_sales_csv_matches_database(client):
    """GET /api/export/sales-csv should generate valid CSV matching database truth."""
    res = client.get("/api/export/sales-csv")
    assert res.status_code == 200
    assert "text/csv" in res.headers["content-type"]
    assert 'filename="insightiq_sales_report.csv"' in res.headers["content-disposition"]

    content = res.text
    assert "# InsightIQ AI - Executive Sales Report" in content
    assert "2540.00" in content
    assert "Cancelled and returned orders are excluded." in content

    # Parse CSV structure
    reader = csv.reader(io.StringIO(content))
    rows = list(reader)
    # Verify monthly data rows exist (Apr 2023, Jan 2024, Feb 2024, Mar 2024)
    month_rows = [r for r in rows if len(r) == 5 and ("2024-" in r[0] or "2023-" in r[0])]
    assert len(month_rows) == 4


def test_export_products_csv(client):
    """GET /api/export/products-csv should stream catalog rankings in CSV format."""
    res = client.get("/api/export/products-csv?limit=10")
    assert res.status_code == 200
    assert "text/csv" in res.headers["content-type"]
    assert 'filename="insightiq_products_catalog.csv"' in res.headers["content-disposition"]

    content = res.text
    reader = csv.reader(io.StringIO(content))
    rows = list(reader)
    header = rows[0]
    assert header == ["Product ID", "Product Name", "Category", "Unit Price ($)", "Total Revenue ($)", "Units Sold", "Current Stock"]
    assert len(rows) >= 4  # Header + products


def test_export_customers_csv(client):
    """GET /api/export/customers-csv should stream customer cohorts in CSV format."""
    res = client.get("/api/export/customers-csv?limit=10")
    assert res.status_code == 200
    assert "text/csv" in res.headers["content-type"]
    assert 'filename="insightiq_customers_cohort.csv"' in res.headers["content-disposition"]

    content = res.text
    reader = csv.reader(io.StringIO(content))
    rows = list(reader)
    header = rows[0]
    assert header == ["Customer ID", "Name", "Email", "City", "Total Spend ($)", "Completed Orders"]
    assert len(rows) >= 3


# -------------------------------------------------------------
# 3. Dataset Quality & Governance Audit
# -------------------------------------------------------------

def test_system_dataset_quality_summary(client):
    """GET /api/system/quality-summary should audit entity counts and governance rules."""
    res = client.get("/api/system/quality-summary")
    assert res.status_code == 200
    data = res.json()

    assert data["status"] == "healthy"
    assert data["inventory"]["customers_count"] == 5
    assert data["inventory"]["products_count"] == 5
    assert data["inventory"]["orders_total"] == 8
    assert data["inventory"]["order_items_total"] == 11

    # Check status breakdown
    assert data["order_status_breakdown"]["completed"] == 5
    assert data["order_status_breakdown"]["pending"] == 1
    assert data["order_status_breakdown"]["cancelled"] == 1
    assert data["order_status_breakdown"]["returned"] == 1

    # Governance policy exclusions
    assert data["governance_exclusions"]["excluded_orders_count"] == 2
    assert Decimal(str(data["governance_exclusions"]["excluded_revenue_dollars"])) == Decimal("1080.00")
    assert data["data_integrity"]["referential_integrity"] == "valid"
    assert data["data_integrity"]["negative_prices_detected"] == 0


# -------------------------------------------------------------
# 4. Anomaly Detection & Business Insights
# -------------------------------------------------------------

def test_insights_anomaly_detection(client):
    """GET /api/insights/anomalies should run statistical scans across temporal sales."""
    res = client.get("/api/insights/anomalies")
    assert res.status_code == 200
    data = res.json()

    assert data["status"] == "success"
    assert "anomalies" in data
    assert isinstance(data["anomalies"], list)
    assert "executive_insights" in data
    assert isinstance(data["executive_insights"], list)


# -------------------------------------------------------------
# 5. Analytics Execution Audit History
# -------------------------------------------------------------

def test_analyst_execution_history_lifecycle(client):
    """Verifies that query executions are logged in audit history and can be cleared."""
    # 1. Clear any prior history
    del_res = client.delete("/api/analyst/history")
    assert del_res.status_code == 200

    # 2. Verify history is empty
    hist_res = client.get("/api/analyst/history")
    assert hist_res.status_code == 200
    assert len(hist_res.json()) == 0

    # 3. Execute a query
    client.post("/api/analyst/chat", json={"question": "What is our total revenue?"})

    # 4. Verify inquiry was logged
    hist_res2 = client.get("/api/analyst/history")
    assert hist_res2.status_code == 200
    records = hist_res2.json()
    assert len(records) >= 1
    latest = records[0]
    assert latest["question"] == "What is our total revenue?"
    assert latest["tools_count"] >= 1
    assert "get_sales_metrics" in latest["tools_executed"]
    assert latest["duration_ms"] >= 0.0
    assert latest["success"] is True


# -------------------------------------------------------------
# 6. Cross-System Date Filtering Consistency
# -------------------------------------------------------------

def test_cross_system_date_filtering_consistency(client):
    """Verifies that date filters produce identical results across sales, dashboard, and CSV."""
    params = {"start_date": "2024-01-01", "end_date": "2024-01-31"}

    # 1. Sales API
    sales_res = client.get("/api/sales/metrics", params=params)
    assert sales_res.status_code == 200
    assert Decimal(str(sales_res.json()["total_revenue"])) == Decimal("1220.00")
    assert sales_res.json()["total_orders"] == 2

    # 2. Dashboard API
    dash_res = client.get("/api/dashboard", params=params)
    assert dash_res.status_code == 200
    assert Decimal(str(dash_res.json()["kpis"]["total_revenue"])) == Decimal("1220.00")
    assert dash_res.json()["kpis"]["total_orders"] == 2

    # 3. CSV Export API
    csv_res = client.get("/api/export/sales-csv", params=params)
    assert csv_res.status_code == 200
    assert "1220.00" in csv_res.text
    assert "# Total Qualifying Orders,2" in csv_res.text
