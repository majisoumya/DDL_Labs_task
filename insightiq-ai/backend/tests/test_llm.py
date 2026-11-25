"""Unit Tests for OpenAI LLM Client, Structured Schemas, and Service (Mocked)."""

import json
from unittest.mock import MagicMock, patch
import pytest
from openai import (
    APIConnectionError,
    APIError,
    APITimeoutError,
    AuthenticationError,
    InternalServerError,
    RateLimitError,
)
from pydantic import BaseModel

from app.exceptions import (
    LLMAuthenticationError,
    LLMInvalidResponseError,
    LLMProviderError,
    LLMRateLimitError,
    LLMTimeoutError,
)
from app.llm.client import OpenAIClient
from app.llm.prompts import (
    BUSINESS_ANALYST_SYSTEM_PROMPT,
    INTENT_CLASSIFIER_SYSTEM_PROMPT,
)
from app.llm.schemas import (
    AnalysisDomain,
    AnalystInsight,
    AnalystResponse,
    EvidenceGrounding,
    InsightSeverity,
    MetricType,
    UserQueryIntent,
)
from app.llm.service import LLMService


# -----------------------------------------------------------------------------
# Fixtures & Helpers
# -----------------------------------------------------------------------------
def make_mock_openai_response(content: str, prompt_tokens: int = 50, completion_tokens: int = 100):
    """Constructs a mock response matching OpenAI SDK completion structure."""
    mock_resp = MagicMock()
    mock_choice = MagicMock()
    mock_choice.message.content = content
    mock_resp.choices = [mock_choice]
    mock_resp.usage.prompt_tokens = prompt_tokens
    mock_resp.usage.completion_tokens = completion_tokens
    mock_resp.usage.total_tokens = prompt_tokens + completion_tokens
    return mock_resp


# -----------------------------------------------------------------------------
# 1. Client Configuration & Initialization Tests
# -----------------------------------------------------------------------------
def test_client_initialization_defaults():
    """Verifies client initializes with configurable model and settings."""
    client = OpenAIClient(api_key="sk-test-mock-key-12345", model="gpt-4o-mini", timeout_seconds=25)
    assert client.model == "gpt-4o-mini"
    assert client.timeout_seconds == 25
    assert client.max_retries == 2


def test_client_raises_when_api_key_missing():
    """Verifies that attempting calls without an API key raises LLMAuthenticationError."""
    client = OpenAIClient(api_key="")
    with pytest.raises(LLMAuthenticationError) as exc_info:
        client.generate_completion(messages=[{"role": "user", "content": "hello"}])
    assert "OPENAI_API_KEY" in str(exc_info.value)


# -----------------------------------------------------------------------------
# 2. Successful Completions & Structured JSON
# -----------------------------------------------------------------------------
def test_generate_completion_success():
    """Verifies standard chat completion returns string content."""
    mock_openai = MagicMock()
    mock_openai.chat.completions.create.return_value = make_mock_openai_response("InsightIQ analysis ready.")

    client = OpenAIClient(api_key="sk-valid-mock-key", client_instance=mock_openai)
    result = client.generate_completion(messages=[{"role": "user", "content": "What is total revenue?"}])

    assert result == "InsightIQ analysis ready."
    mock_openai.chat.completions.create.assert_called_once()
    call_kwargs = mock_openai.chat.completions.create.call_args.kwargs
    assert call_kwargs["model"] == client.model
    assert len(call_kwargs["messages"]) == 1


def test_generate_structured_json_success():
    """Verifies structured JSON output validated against Pydantic model."""
    class DummyMetric(BaseModel):
        metric_name: str
        value: float

    json_payload = json.dumps({"metric_name": "Total Revenue", "value": 2490.00})
    mock_openai = MagicMock()
    mock_openai.chat.completions.create.return_value = make_mock_openai_response(json_payload)

    client = OpenAIClient(api_key="sk-valid-mock-key", client_instance=mock_openai)
    metric = client.generate_structured_json(
        messages=[{"role": "user", "content": "Get metric"}],
        schema=DummyMetric,
    )

    assert isinstance(metric, DummyMetric)
    assert metric.metric_name == "Total Revenue"
    assert metric.value == 2490.00


def test_generate_structured_json_invalid_schema_raises():
    """Verifies that non-conforming JSON raises LLMInvalidResponseError."""
    class DummyMetric(BaseModel):
        metric_name: str
        value: float

    # Invalid: value cannot be string 'not-a-number'
    invalid_json = json.dumps({"metric_name": "Revenue", "value": "not-a-number"})
    mock_openai = MagicMock()
    mock_openai.chat.completions.create.return_value = make_mock_openai_response(invalid_json)

    client = OpenAIClient(api_key="sk-valid-mock-key", client_instance=mock_openai)
    with pytest.raises(LLMInvalidResponseError) as exc_info:
        client.generate_structured_json(
            messages=[{"role": "user", "content": "Get metric"}],
            schema=DummyMetric,
        )
    assert "could not be parsed" in str(exc_info.value)


# -----------------------------------------------------------------------------
# 3. Error Handling & Provider Fault Tolerance Tests
# -----------------------------------------------------------------------------
def test_handle_authentication_error():
    """Verifies openai.AuthenticationError maps to LLMAuthenticationError."""
    mock_openai = MagicMock()
    mock_req = MagicMock()
    mock_openai.chat.completions.create.side_effect = AuthenticationError(
        message="Invalid API Key provided",
        response=MagicMock(status_code=401),
        body={},
    )

    client = OpenAIClient(api_key="sk-invalid-key", client_instance=mock_openai)
    with pytest.raises(LLMAuthenticationError) as exc_info:
        client.generate_completion(messages=[{"role": "user", "content": "test"}])
    assert "Invalid or expired API key" in str(exc_info.value)


def test_handle_rate_limit_error():
    """Verifies openai.RateLimitError maps to LLMRateLimitError."""
    mock_openai = MagicMock()
    mock_openai.chat.completions.create.side_effect = RateLimitError(
        message="Rate limit reached for requests",
        response=MagicMock(status_code=429),
        body={},
    )

    client = OpenAIClient(api_key="sk-valid-key", client_instance=mock_openai)
    with pytest.raises(LLMRateLimitError) as exc_info:
        client.generate_completion(messages=[{"role": "user", "content": "test"}])
    assert "rate limit or organization quota" in str(exc_info.value)


def test_handle_timeout_error():
    """Verifies openai.APITimeoutError maps to LLMTimeoutError."""
    mock_openai = MagicMock()
    mock_req = MagicMock()
    mock_openai.chat.completions.create.side_effect = APITimeoutError(request=mock_req)

    client = OpenAIClient(api_key="sk-valid-key", client_instance=mock_openai)
    with pytest.raises(LLMTimeoutError) as exc_info:
        client.generate_completion(messages=[{"role": "user", "content": "test"}])
    assert "timed out after" in str(exc_info.value)


def test_handle_connection_error():
    """Verifies openai.APIConnectionError maps to LLMProviderError."""
    mock_openai = MagicMock()
    mock_req = MagicMock()
    mock_openai.chat.completions.create.side_effect = APIConnectionError(request=mock_req)

    client = OpenAIClient(api_key="sk-valid-key", client_instance=mock_openai)
    with pytest.raises(LLMProviderError) as exc_info:
        client.generate_completion(messages=[{"role": "user", "content": "test"}])
    assert "Unable to establish network connection" in str(exc_info.value)


def test_handle_internal_server_error():
    """Verifies openai.InternalServerError maps to LLMProviderError."""
    mock_openai = MagicMock()
    mock_openai.chat.completions.create.side_effect = InternalServerError(
        message="Upstream OpenAI 500 error",
        response=MagicMock(status_code=500),
        body={},
    )

    client = OpenAIClient(api_key="sk-valid-key", client_instance=mock_openai)
    with pytest.raises(LLMProviderError) as exc_info:
        client.generate_completion(messages=[{"role": "user", "content": "test"}])
    assert "internal error" in str(exc_info.value)


# -----------------------------------------------------------------------------
# 4. Natural-Language Intent Understanding Service Tests
# -----------------------------------------------------------------------------
def test_parse_user_intent_sales_domain():
    """Verifies natural language query parses into structured sales intent."""
    intent_data = {
        "original_question": "What was our total revenue in Q1 2024?",
        "domain": "sales",
        "primary_metric": "revenue",
        "requires_data": True,
        "timeframe": {
            "start_date": "2024-01-01",
            "end_date": "2024-03-31",
            "granularity": "month",
        },
        "entity_filters": {"categories": [], "product_names": [], "cities": [], "limit": None},
        "is_ambiguous": False,
        "clarification_needed": None,
        "suggested_tools": ["get_sales_metrics"],
    }

    mock_client = MagicMock(spec=OpenAIClient)
    mock_client.generate_structured_json.return_value = UserQueryIntent.model_validate(intent_data)

    service = LLMService(client=mock_client)
    intent = service.parse_user_intent("What was our total revenue in Q1 2024?")

    assert intent.domain == AnalysisDomain.SALES
    assert intent.primary_metric == MetricType.REVENUE
    assert intent.timeframe.start_date == "2024-01-01"
    assert intent.timeframe.end_date == "2024-03-31"
    assert not intent.is_ambiguous
    assert "get_sales_metrics" in intent.suggested_tools


def test_parse_user_intent_customer_domain():
    """Verifies customer queries correctly identify CUSTOMERS domain."""
    intent_data = {
        "original_question": "Who are our top 5 customers by spend?",
        "domain": "customers",
        "primary_metric": "customer_count",
        "requires_data": True,
        "timeframe": None,
        "entity_filters": {"categories": [], "product_names": [], "cities": [], "limit": 5},
        "is_ambiguous": False,
        "clarification_needed": None,
        "suggested_tools": ["get_top_customers"],
    }

    mock_client = MagicMock(spec=OpenAIClient)
    mock_client.generate_structured_json.return_value = UserQueryIntent.model_validate(intent_data)

    service = LLMService(client=mock_client)
    intent = service.parse_user_intent("Who are our top 5 customers by spend?")

    assert intent.domain == AnalysisDomain.CUSTOMERS
    assert intent.entity_filters.limit == 5
    assert "get_top_customers" in intent.suggested_tools


def test_parse_user_intent_ambiguous_query():
    """Verifies ambiguous questions identify need for clarification."""
    intent_data = {
        "original_question": "How are sales doing?",
        "domain": "sales",
        "primary_metric": "revenue",
        "requires_data": True,
        "timeframe": None,
        "entity_filters": None,
        "is_ambiguous": True,
        "clarification_needed": "Please specify the time period (e.g., Q1 2024) or target metric.",
        "suggested_tools": ["get_dashboard_summary"],
    }

    mock_client = MagicMock(spec=OpenAIClient)
    mock_client.generate_structured_json.return_value = UserQueryIntent.model_validate(intent_data)

    service = LLMService(client=mock_client)
    intent = service.parse_user_intent("How are sales doing?")

    assert intent.is_ambiguous is True
    assert intent.clarification_needed is not None


def test_heuristic_intent_fallback():
    """Verifies that heuristic fallback operates when LLM completion throws an error."""
    mock_client = MagicMock(spec=OpenAIClient)
    mock_client.generate_structured_json.side_effect = LLMProviderError("LLM unavailable")

    service = LLMService(client=mock_client)
    intent = service.parse_user_intent("Show me top products in Electronics")

    assert intent.domain == AnalysisDomain.PRODUCTS
    assert intent.requires_data is True
    assert "get_top_products" in intent.suggested_tools


# -----------------------------------------------------------------------------
# 5. Grounded Analytical Synthesis Tests
# -----------------------------------------------------------------------------
def test_synthesize_grounded_response_success():
    """Verifies that synthesis generates structured AnalystResponse backed by evidence."""
    mock_evidence = {
        "total_revenue": 2490.00,
        "total_orders": 5,
        "average_order_value": 498.00,
        "period": "2024-01-01 to 2024-03-31",
    }

    mock_analyst_response = AnalystResponse(
        question="What was our total revenue in Q1 2024?",
        summary="Total revenue for Q1 2024 reached $2,490.00 across 5 eligible orders with an AOV of $498.00.",
        insights=[
            AnalystInsight(
                title="Q1 Revenue Performance",
                finding="Revenue totaled $2,490.00 across 5 completed and pending orders.",
                evidence=[
                    EvidenceGrounding(
                        metric_name="Total Revenue",
                        exact_value=2490.00,
                        source="get_sales_metrics",
                        time_period="2024-01-01 to 2024-03-31",
                    )
                ],
                severity=InsightSeverity.POSITIVE,
                actionable_recommendation="Maintain inventory in top performing categories.",
            )
        ],
        metrics_referenced=[
            EvidenceGrounding(
                metric_name="Total Revenue",
                exact_value=2490.00,
                source="get_sales_metrics",
            )
        ],
        needs_clarification=False,
        data_limitations_noted="Cancelled and refunded orders were excluded per corporate policy.",
        model_used="gpt-4o-mini",
    )

    mock_client = MagicMock(spec=OpenAIClient)
    mock_client.model = "gpt-4o-mini"
    mock_client.generate_structured_json.return_value = mock_analyst_response

    service = LLMService(client=mock_client)
    res = service.synthesize_grounded_response(
        user_question="What was our total revenue in Q1 2024?",
        evidence_data=mock_evidence,
    )

    assert isinstance(res, AnalystResponse)
    assert res.summary.startswith("Total revenue for Q1 2024 reached $2,490.00")
    assert len(res.insights) == 1
    assert res.insights[0].evidence[0].exact_value == 2490.00
    assert "Cancelled and refunded orders were excluded" in res.data_limitations_noted
    assert res.model_used == "gpt-4o-mini"


def test_create_clarification_response():
    """Verifies creation of deterministic clarification responses."""
    mock_client = MagicMock(spec=OpenAIClient)
    mock_client.model = "gpt-4o-mini"
    service = LLMService(client=mock_client)

    res = service.create_clarification_response(
        question="How are products?",
        clarification_prompt="Please specify if you want top-selling, low-performing, or category-specific products.",
    )

    assert res.needs_clarification is True
    assert res.clarification_question is not None
    assert len(res.insights) == 1
    assert res.insights[0].title == "Clarification Required"
