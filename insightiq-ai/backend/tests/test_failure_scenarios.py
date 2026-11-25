"""Dedicated Resilience, Failure Scenarios, and Edge Case Tests for InsightIQ AI.

Covers the 10 Critical Failure Scenarios required for Phase 19 QA:
1. Missing API key
2. Invalid API key
3. LLM timeout
4. LLM rate limit
5. Database unavailable
6. Invalid date range
7. Empty dataset
8. Invalid tool arguments
9. Unsupported question
10. Malformed chart response
"""

from decimal import Decimal
import json
from unittest.mock import MagicMock, patch
import pytest
from fastapi.testclient import TestClient
from openai import (
    APIConnectionError,
    APITimeoutError,
    AuthenticationError,
    RateLimitError,
)
from pydantic import ValidationError
from sqlalchemy.exc import OperationalError

from app.database.session import get_db
from app.exceptions import (
    LLMAuthenticationError,
    LLMRateLimitError,
    LLMTimeoutError,
)
from app.llm.client import OpenAIClient
from app.llm.schemas import AnalysisDomain, MetricType
from app.llm.service import LLMService
from app.main import app
from app.schemas.charts import ChartSpec
from app.services.chart_service import generate_chart_from_query
from app.services.sales_service import get_sales_growth, get_sales_metrics
from app.tools.registry import default_tool_registry


@pytest.fixture
def client(seeded_db_session):
    """Provides a TestClient with database session overridden."""
    def override_get_db():
        yield seeded_db_session

    app.dependency_overrides[get_db] = override_get_db
    test_client = TestClient(app)
    yield test_client
    app.dependency_overrides.clear()


# -----------------------------------------------------------------------------
# Scenario 1: Missing API Key
# -----------------------------------------------------------------------------
def test_scenario_1_missing_api_key():
    """Verifies that an empty or missing API key is cleanly detected and handled."""
    client = OpenAIClient(api_key="")
    with pytest.raises(LLMAuthenticationError) as exc_info:
        client.generate_completion(messages=[{"role": "user", "content": "test"}])
    assert "OPENAI_API_KEY" in str(exc_info.value)

    # LLMService gracefully falls back without crashing
    service = LLMService(client=client)
    intent = service.parse_user_intent("What is our revenue?")
    assert intent.domain in (AnalysisDomain.SALES, AnalysisDomain.CROSS_DOMAIN)

    # Grounded response synthesis falls back to verified DB metrics
    response = service.synthesize_grounded_response(
        user_question="What is total revenue?",
        evidence_data={"get_sales_metrics": {"total_revenue": 2490.0, "total_orders": 5, "aov": 498.0}},
    )
    assert response.summary
    assert len(response.metrics_referenced) >= 1
    assert float(response.metrics_referenced[0].exact_value) == 2490.0


# -----------------------------------------------------------------------------
# Scenario 2: Invalid API Key
# -----------------------------------------------------------------------------
def test_scenario_2_invalid_api_key():
    """Verifies that 401 AuthenticationError from OpenAI maps to LLMAuthenticationError and falls back safely."""
    mock_openai = MagicMock()
    mock_openai.chat.completions.create.side_effect = AuthenticationError(
        message="Incorrect API key provided: sk-invalid-key",
        response=MagicMock(status_code=401),
        body={},
    )
    client = OpenAIClient(api_key="sk-invalid-key", client_instance=mock_openai)

    with pytest.raises(LLMAuthenticationError) as exc_info:
        client.generate_completion(messages=[{"role": "user", "content": "test"}])
    assert "Invalid or expired API key" in str(exc_info.value)

    # Service-level resilience
    service = LLMService(client=client)
    response = service.synthesize_grounded_response(
        user_question="What is total revenue?",
        evidence_data={"get_sales_metrics": {"total_revenue": 2490.0, "total_orders": 5, "aov": 498.0}},
    )
    assert "2,490.00" in response.summary


# -----------------------------------------------------------------------------
# Scenario 3: LLM Timeout
# -----------------------------------------------------------------------------
def test_scenario_3_llm_timeout():
    """Verifies that APITimeoutError from OpenAI maps to LLMTimeoutError and triggers fallback."""
    mock_openai = MagicMock()
    mock_openai.chat.completions.create.side_effect = APITimeoutError(request=MagicMock())
    client = OpenAIClient(api_key="sk-test-key", client_instance=mock_openai)

    with pytest.raises(LLMTimeoutError) as exc_info:
        client.generate_completion(messages=[{"role": "user", "content": "test"}])
    assert "timed out after" in str(exc_info.value)

    # Service-level resilience
    service = LLMService(client=client)
    response = service.synthesize_grounded_response(
        user_question="What is total revenue?",
        evidence_data={"get_sales_metrics": {"total_revenue": 2490.0, "total_orders": 5, "aov": 498.0}},
    )
    assert response.metrics_referenced[0].metric_name == "total_revenue"


# -----------------------------------------------------------------------------
# Scenario 4: LLM Rate Limit
# -----------------------------------------------------------------------------
def test_scenario_4_llm_rate_limit():
    """Verifies that RateLimitError from OpenAI maps to LLMRateLimitError and triggers fallback."""
    mock_openai = MagicMock()
    mock_openai.chat.completions.create.side_effect = RateLimitError(
        message="Rate limit reached for requests",
        response=MagicMock(status_code=429),
        body={},
    )
    client = OpenAIClient(api_key="sk-test-key", client_instance=mock_openai)

    with pytest.raises(LLMRateLimitError) as exc_info:
        client.generate_completion(messages=[{"role": "user", "content": "test"}])
    assert "rate limit or organization quota" in str(exc_info.value)

    # Service-level resilience
    service = LLMService(client=client)
    intent = service.parse_user_intent("Show top products")
    assert intent.domain in (AnalysisDomain.PRODUCTS, AnalysisDomain.SALES)


# -----------------------------------------------------------------------------
# Scenario 5: Database Unavailable
# -----------------------------------------------------------------------------
def test_scenario_5_database_unavailable():
    """Verifies that database connection loss results in 503 for health and 500 without leaking credentials."""
    broken_session = MagicMock()
    broken_session.execute.side_effect = OperationalError("connection refused to db.internal:5432", params={}, orig=Exception())

    def override_broken_db():
        yield broken_session

    app.dependency_overrides[get_db] = override_broken_db
    broken_client = TestClient(app, raise_server_exceptions=False)

    try:
        # 1. Health Probe returns 503 Service Unavailable
        health_res = broken_client.get("/api/health")
        assert health_res.status_code == 503
        data = health_res.json()
        assert "degraded" in str(data)

        # 2. Sales API returns RFC 7807 500 error without leaking connection string
        sales_res = broken_client.get("/api/sales/metrics")
        assert sales_res.status_code == 500
        error_body = sales_res.json()
        assert error_body["error"] == "Internal Server Error"
        assert error_body["status_code"] == 500
        assert "correlation_id" in error_body
        assert "db.internal:5432" not in error_body["detail"]
    finally:
        app.dependency_overrides.clear()


# -----------------------------------------------------------------------------
# Scenario 6: Invalid Date Range
# -----------------------------------------------------------------------------
def test_scenario_6_invalid_date_range(client):
    """Verifies validation and 400 Bad Request responses for inverted dates and bad date formats."""
    # 1. Inverted date range (start > end)
    res1 = client.get("/api/sales/metrics?start_date=2024-05-01&end_date=2024-01-01")
    assert res1.status_code == 400
    assert "cannot be greater than end_date" in res1.json()["detail"]

    # 2. Malformed date string
    res2 = client.get("/api/sales/metrics?start_date=not-a-valid-date")
    assert res2.status_code == 400
    assert "Expected ISO format" in res2.json()["detail"]

    # 3. Dashboard API date validation
    res3 = client.get("/api/dashboard?start_date=2024-12-31&end_date=2024-01-01")
    assert res3.status_code == 400
    assert "cannot be greater than end_date" in res3.json()["detail"]


# -----------------------------------------------------------------------------
# Scenario 7: Empty Dataset
# -----------------------------------------------------------------------------
def test_scenario_7_empty_dataset(empty_db_session):
    """Verifies services and endpoints handle empty database tables safely with zero division protection."""
    # 1. Sales metrics on empty database
    metrics = get_sales_metrics(empty_db_session)
    assert metrics["total_revenue"] == Decimal("0.00")
    assert metrics["total_orders"] == 0
    assert metrics["aov"] == Decimal("0.00")  # Zero division avoided

    # 2. Sales growth calculation on empty database
    growth = get_sales_growth(empty_db_session, "2024-01-01", "2024-01-31", "2024-02-01", "2024-02-28")
    assert growth["current_period"]["revenue"] == Decimal("0.00")
    assert growth["previous_period"]["revenue"] == Decimal("0.00")
    assert growth["revenue_growth_pct"] is None  # Handled safely without division by zero

    # 3. API endpoint on empty DB
    def override_empty_db():
        yield empty_db_session

    app.dependency_overrides[get_db] = override_empty_db
    empty_client = TestClient(app)
    try:
        dash_res = empty_client.get("/api/dashboard")
        assert dash_res.status_code == 200
        dash_data = dash_res.json()
        assert float(dash_data["kpis"]["total_revenue"]) == 0.0
        assert dash_data["kpis"]["total_orders"] == 0
        assert float(dash_data["kpis"]["average_order_value"]) == 0.0
        assert dash_data["monthly_trend"] == []
        assert dash_data["category_distribution"] == []
        assert dash_data["top_products"] == []
    finally:
        app.dependency_overrides.clear()


# -----------------------------------------------------------------------------
# Scenario 8: Invalid Tool Arguments
# -----------------------------------------------------------------------------
def test_scenario_8_invalid_tool_arguments(seeded_db_session):
    """Verifies that unknown tools and invalid argument types are trapped cleanly by ToolRegistry."""
    # 1. Unknown tool rejection
    res1 = default_tool_registry.execute_tool("non_existent_analytics_tool", {}, db=seeded_db_session)
    assert res1.success is False
    assert "not an approved analytics tool" in res1.error

    # 2. Invalid date parameter format
    res2 = default_tool_registry.execute_tool("get_sales_metrics", {"start_date": "invalid-date-string"}, db=seeded_db_session)
    assert res2.success is False
    assert "Validation failed for tool 'get_sales_metrics'" in res2.error

    # 3. Exceeded integer boundary limit (> 100)
    res3 = default_tool_registry.execute_tool("get_top_products", {"limit": 99999}, db=seeded_db_session)
    assert res3.success is False
    assert "less than or equal to 100" in res3.error

    # 4. Malformed JSON string arguments
    res4 = default_tool_registry.execute_tool("get_sales_metrics", "{unquoted_bad_json: 123", db=seeded_db_session)
    assert res4.success is False
    assert "Failed to parse tool arguments as valid JSON" in res4.error


# -----------------------------------------------------------------------------
# Scenario 9: Unsupported Question
# -----------------------------------------------------------------------------
def test_scenario_9_unsupported_question(client):
    """Verifies that out-of-scope or unanswerable queries receive structured guidance without hallucination."""
    res = client.post(
        "/api/analyst/chat",
        json={"question": "What is the weather forecast for tomorrow in Tokyo?"},
    )
    assert res.status_code == 200
    data = res.json()
    assert "summary" in data
    assert isinstance(data["summary"], str)
    assert len(data["summary"]) > 0

    # Ensure zero hallucinated numerical metrics are returned
    if data.get("metrics_referenced"):
        for m in data["metrics_referenced"]:
            assert m["source"] in ("orders", "products", "customers")

    # Execution trace records workflow completion
    assert len(data["execution_trace"]) >= 1


# -----------------------------------------------------------------------------
# Scenario 10: Malformed Chart Response
# -----------------------------------------------------------------------------
def test_scenario_10_malformed_chart_response(seeded_db_session):
    """Verifies that invalid chart types, missing keys, and empty datasets are caught by Pydantic."""
    # 1. Unsupported chart type raises ValueError
    with pytest.raises(ValidationError) as exc_info1:
        ChartSpec(
            chart_type="scatter_plot_3d",
            title="Invalid Chart",
            x_key="category",
            y_key="revenue",
            data=[{"category": "Electronics", "revenue": 1000}],
        )
    assert "Unsupported chart type" in str(exc_info1.value)

    # 2. Missing required axis keys raises ValidationError
    with pytest.raises(ValidationError):
        ChartSpec(
            chart_type="bar",
            title="Missing Keys Chart",
            x_key="",  # min_length=1
            y_key="revenue",
            data=[],
        )

    # 3. Empty data sets are gracefully accepted and flagged in metadata
    empty_spec = ChartSpec(
        chart_type="bar",
        title="Empty Dataset Chart",
        x_key="category",
        y_key="revenue",
        data=[],
    )
    assert empty_spec.metadata.is_empty is True
    assert empty_spec.metadata.total_points == 0

    # 4. Service-level query for non-existent dimension returns safe empty spec
    safe_spec = generate_chart_from_query(
        query="Show sales for completely unknown department xyz",
        db=seeded_db_session,
    )
    assert isinstance(safe_spec, ChartSpec)
    assert safe_spec.chart_type in ("line", "bar", "pie", "area")
