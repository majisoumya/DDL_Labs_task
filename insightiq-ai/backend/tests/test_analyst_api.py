"""Integration tests for AI Business Analyst Chat API endpoints."""

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
# 1. Suggestions Endpoint Tests
# -------------------------------------------------------------

def test_get_analyst_suggestions(client):
    """GET /api/analyst/suggestions should return a curated list of starter queries."""
    res = client.get("/api/analyst/suggestions")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert len(data) >= 5
    assert "What is our total revenue?" in data
    assert "Why did revenue decline last month?" in data


# -------------------------------------------------------------
# 2. Chat Query Tests
# -------------------------------------------------------------

def test_chat_total_revenue_query(client):
    """POST /api/analyst/chat with total revenue question should execute tool and return grounded response."""
    payload = {
        "question": "What is our total revenue?",
        "chat_history": []
    }
    res = client.post("/api/analyst/chat", json=payload)
    assert res.status_code == 200
    data = res.json()

    assert data["question"] == "What is our total revenue?"
    assert data["summary"] is not None
    assert len(data["summary"]) > 0
    assert isinstance(data["insights"], list)
    assert isinstance(data["metrics_referenced"], list)
    assert isinstance(data["tool_executions"], list)
    assert len(data["tool_executions"]) >= 1

    # Check that tool execution details are present and sanitized
    executed_tools = [te["tool_name"] for te in data["tool_executions"]]
    assert any(tool in executed_tools for tool in ["get_sales_metrics", "get_total_revenue"])

    for te in data["tool_executions"]:
        assert te["success"] is True
        assert te["error"] is None
        # Assert database sessions or connection credentials are not exposed
        assert "db" not in te["arguments"]
        assert "session" not in te["arguments"]

    # Check execution trace
    assert isinstance(data["execution_trace"], list)
    assert len(data["execution_trace"]) >= 1
    assert any(trace.get("node") in ["execute_tools", "select_tools", "generate_answer"] for trace in data["execution_trace"])


def test_chat_revenue_decline_diagnostic(client):
    """POST /api/analyst/chat with diagnostic question should trigger investigation workflow."""
    payload = {
        "question": "Why did revenue decline last month?",
        "chat_history": []
    }
    res = client.post("/api/analyst/chat", json=payload)
    assert res.status_code == 200
    data = res.json()

    assert data["question"] == "Why did revenue decline last month?"
    assert len(data["summary"]) > 0
    assert len(data["insights"]) >= 1

    # Verify diagnostic decline tool was executed
    executed_tools = [te["tool_name"] for te in data["tool_executions"]]
    assert "investigate_revenue_decline" in executed_tools

    # Verify insights contain variance or contribution findings
    insights_text = " ".join([
        (i["finding"] if isinstance(i, dict) else str(i)) for i in data["insights"]
    ]).lower()
    combined_text = (data["summary"] + " " + insights_text).lower()
    assert any(term in combined_text for term in ["revenue", "decline", "change", "variance", "investigation"])


def test_chat_chart_query(client):
    """POST /api/analyst/chat asking for a chart should return structured chart specification."""
    payload = {
        "question": "Show monthly revenue as a chart.",
        "chat_history": []
    }
    res = client.post("/api/analyst/chat", json=payload)
    assert res.status_code == 200
    data = res.json()

    assert data["chart_spec"] is not None
    assert "chart_type" in data["chart_spec"]
    assert "title" in data["chart_spec"]
    assert "data" in data["chart_spec"]
    assert isinstance(data["chart_spec"]["data"], list)
    assert len(data["chart_spec"]["data"]) > 0


def test_chat_with_history(client):
    """POST /api/analyst/chat should accept conversation history context."""
    payload = {
        "question": "Which products generate the most revenue?",
        "chat_history": [
            {"role": "user", "content": "What is our total revenue?"},
            {"role": "assistant", "content": "Total revenue is $1,270.00 across 3 orders."}
        ]
    }
    res = client.post("/api/analyst/chat", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "products" in data["question"].lower()
    assert len(data["tool_executions"]) >= 1


def test_chat_validation_errors(client):
    """POST /api/analyst/chat should reject invalid questions with 422."""
    # Empty question string
    res = client.post("/api/analyst/chat", json={"question": ""})
    assert res.status_code == 422

    # Whitespace only question
    res = client.post("/api/analyst/chat", json={"question": "   "})
    assert res.status_code == 422

    # Missing question field
    res = client.post("/api/analyst/chat", json={})
    assert res.status_code == 422
