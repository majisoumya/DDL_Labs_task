"""Security, Configuration, Logging, and Error Handling Tests for InsightIQ AI."""

import logging
from unittest.mock import MagicMock
import pytest
from fastapi import APIRouter
from fastapi.testclient import TestClient
from pydantic import SecretStr

from app.config import Settings
from app.database.session import get_db
from app.exceptions import (
    DataNotFoundError,
    DatabaseTimeoutError,
    InsightIQException,
    InvalidInputError,
    RateLimitExceededError,
    UnauthorizedAccessError,
)
from app.logging_config import CredentialFilter, configure_logging, correlation_id_ctx
from app.main import app
from app.middleware.rate_limiter import RateLimitMiddleware


# -----------------------------------------------------------------------------
# Fixtures
# -----------------------------------------------------------------------------
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
# 1. Correlation ID Tests
# -----------------------------------------------------------------------------
def test_correlation_id_auto_generation(client):
    """Verifies that an incoming request without correlation ID gets one assigned."""
    res = client.get("/")
    assert res.status_code == 200
    assert "X-Correlation-ID" in res.headers
    assert len(res.headers["X-Correlation-ID"]) > 10


def test_correlation_id_propagation_from_client(client):
    """Verifies that a client-supplied X-Correlation-ID is preserved and echoed back."""
    custom_cid = "test-corr-id-9988-aabb"
    res = client.get("/", headers={"X-Correlation-ID": custom_cid})
    assert res.status_code == 200
    assert res.headers.get("X-Correlation-ID") == custom_cid


def test_correlation_id_present_on_error_response(client):
    """Verifies that error responses include the correlation ID in both body and headers."""
    custom_cid = "error-corr-id-1234"
    res = client.get("/api/products/999999", headers={"X-Correlation-ID": custom_cid})
    assert res.status_code == 404
    assert res.headers.get("X-Correlation-ID") == custom_cid
    data = res.json()
    assert data["correlation_id"] == custom_cid
    assert data["status_code"] == 404


# -----------------------------------------------------------------------------
# 2. Secrets Protection and Settings Masking
# -----------------------------------------------------------------------------
def test_pydantic_secret_str_masking():
    """Verifies that SecretStr fields prevent plaintext password exposure in str/repr."""
    test_settings = Settings(
        OPENAI_API_KEY=SecretStr("sk-proj-supersecret1234567890abcdef"),
        POSTGRES_PASSWORD=SecretStr("db_super_secret_pw"),
    )

    # String representation must mask secret value
    assert "sk-proj-supersecret" not in str(test_settings.OPENAI_API_KEY)
    assert "db_super_secret_pw" not in str(test_settings.POSTGRES_PASSWORD)
    assert "db_super_secret_pw" not in repr(test_settings.POSTGRES_PASSWORD)

    # Explicit retrieval works
    assert test_settings.openai_api_key_str == "sk-proj-supersecret1234567890abcdef"
    assert test_settings.postgres_password_str == "db_super_secret_pw"


def test_settings_safe_dict_redaction():
    """Verifies safe_dict replaces secret keys with asterisks."""
    test_settings = Settings(
        OPENAI_API_KEY=SecretStr("sk-proj-my-secret-key-12345678"),
        POSTGRES_PASSWORD=SecretStr("my_clear_password"),
        ANALYTICS_READONLY_PASSWORD=SecretStr("readonly_pass"),
    )
    safe = test_settings.safe_dict()
    assert safe["OPENAI_API_KEY"] == "******"
    assert safe["POSTGRES_PASSWORD"] == "******"
    assert safe["ANALYTICS_READONLY_PASSWORD"] == "******"


def test_credential_filter_log_redaction():
    """Verifies CredentialFilter redacts API keys and passwords from log records."""
    cred_filter = CredentialFilter()

    # Test OpenAI API key redaction
    record1 = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="",
        lineno=1,
        msg="Calling OpenAI with key sk-proj-12345678901234567890",
        args=(),
        exc_info=None,
    )
    cred_filter.filter(record1)
    assert "sk-proj-12345678901234567890" not in record1.msg
    assert "******" in record1.msg

    # Test password redaction in log message
    record2 = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="",
        lineno=1,
        msg="Connecting to db with password: mySecretPassword123",
        args=(),
        exc_info=None,
    )
    cred_filter.filter(record2)
    assert "mySecretPassword123" not in record2.msg


# -----------------------------------------------------------------------------
# 3. Stack Trace Suppression & Safe 500 Responses
# -----------------------------------------------------------------------------
def test_internal_server_error_suppresses_stack_trace():
    """Verifies that an unhandled internal exception does not leak tracebacks to the client."""
    safe_client = TestClient(app, raise_server_exceptions=False)
    test_router = APIRouter()

    @test_router.get("/test-internal-crash")
    def crash_endpoint():
        raise RuntimeError("Sensitive internal database connection trace: /var/secrets/key.pem failed")

    app.include_router(test_router)

    try:
        res = safe_client.get("/test-internal-crash")
        assert res.status_code == 500
        data = res.json()
        assert data["error"] == "Internal Server Error"
        assert data["detail"] == "An unexpected server error occurred."
        assert data["status_code"] == 500
        assert "correlation_id" in data
        assert "RuntimeError" not in str(data)
        assert "/var/secrets" not in str(data)
    finally:
        # Unregister test route
        app.routes[:] = [r for r in app.routes if getattr(r, "path", None) != "/test-internal-crash"]


# -----------------------------------------------------------------------------
# 4. Standardized Domain Exception Handlers
# -----------------------------------------------------------------------------
def test_domain_exception_handling(client):
    """Tests custom domain exception mapping into standard RFC 7807 responses."""
    test_router = APIRouter()

    @test_router.get("/test-domain-error")
    def domain_error_endpoint(error_type: str):
        if error_type == "not_found":
            raise DataNotFoundError("Product with ID 999 not found.")
        elif error_type == "invalid_input":
            raise InvalidInputError("Threshold cannot be negative.")
        elif error_type == "timeout":
            raise DatabaseTimeoutError("Query execution exceeded 30s limit.")
        elif error_type == "rate_limit":
            raise RateLimitExceededError("Rate limit threshold crossed.")
        elif error_type == "unauthorized":
            raise UnauthorizedAccessError("Missing authentication token.")
        raise InsightIQException("Generic domain failure", status_code=502)

    app.include_router(test_router)

    try:
        # 404
        r404 = client.get("/test-domain-error?error_type=not_found")
        assert r404.status_code == 404
        assert r404.json()["error"] == "DataNotFoundError"
        assert r404.json()["detail"] == "Product with ID 999 not found."

        # 400
        r400 = client.get("/test-domain-error?error_type=invalid_input")
        assert r400.status_code == 400
        assert r400.json()["error"] == "InvalidInputError"

        # 504
        r504 = client.get("/test-domain-error?error_type=timeout")
        assert r504.status_code == 504
        assert r504.json()["error"] == "DatabaseTimeoutError"

        # 429
        r429 = client.get("/test-domain-error?error_type=rate_limit")
        assert r429.status_code == 429
        assert r429.json()["error"] == "RateLimitExceededError"

        # 401
        r401 = client.get("/test-domain-error?error_type=unauthorized")
        assert r401.status_code == 401
        assert r401.json()["error"] == "UnauthorizedAccessError"

        # 502
        r502 = client.get("/test-domain-error?error_type=other")
        assert r502.status_code == 502
        assert r502.json()["error"] == "InsightIQException"
    finally:
        app.routes[:] = [r for r in app.routes if getattr(r, "path", None) != "/test-domain-error"]


# -----------------------------------------------------------------------------
# 5. Rate Limiter Middleware Unit Tests
# -----------------------------------------------------------------------------
def test_rate_limiter_blocks_burst_traffic():
    """Directly tests RateLimitMiddleware behavior under burst conditions."""
    from fastapi import FastAPI
    from starlette.responses import PlainTextResponse

    mock_app = FastAPI()

    @mock_app.get("/ping")
    def ping():
        return PlainTextResponse("pong")

    # Add rate limiter with tight limit of 3 requests per 60s
    mock_app.add_middleware(RateLimitMiddleware, max_requests=3, window_seconds=60)
    mock_client = TestClient(mock_app)

    # First 3 requests must succeed
    for _ in range(3):
        res = mock_client.get("/ping")
        assert res.status_code == 200

    # 4th request must return 429
    res4 = mock_client.get("/ping")
    assert res4.status_code == 429
    data = res4.json()
    assert data["error"] == "Rate Limit Exceeded"
    assert data["status_code"] == 429
    assert "Retry-After" in res4.headers
