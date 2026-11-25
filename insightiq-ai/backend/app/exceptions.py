"""Domain Exceptions for InsightIQ AI."""

from __future__ import annotations


class InsightIQException(Exception):
    """Base domain exception for all InsightIQ AI errors."""
    def __init__(self, message: str, status_code: int = 500) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class InvalidInputError(InsightIQException):
    """Raised when request payload or query parameters fail validation."""
    def __init__(self, message: str) -> None:
        super().__init__(message=message, status_code=400)


class DataNotFoundError(InsightIQException):
    """Raised when a requested resource or dataset entity does not exist."""
    def __init__(self, message: str) -> None:
        super().__init__(message=message, status_code=404)


class DatabaseTimeoutError(InsightIQException):
    """Raised when an analytical database query exceeds execution timeout limits."""
    def __init__(self, message: str = "Database query timed out.") -> None:
        super().__init__(message=message, status_code=504)


class RateLimitExceededError(InsightIQException):
    """Raised when a client IP exceeds request rate thresholds."""
    def __init__(self, message: str = "Rate limit exceeded. Please try again later.") -> None:
        super().__init__(message=message, status_code=429)


class UnauthorizedAccessError(InsightIQException):
    """Raised when credentials or authentication tokens are invalid or missing."""
    def __init__(self, message: str = "Unauthorized access.") -> None:
        super().__init__(message=message, status_code=401)


class LLMAuthenticationError(InsightIQException):
    """Raised when the OpenAI API rejects authentication credentials."""
    def __init__(self, message: str = "OpenAI API authentication failed. Verify OPENAI_API_KEY.") -> None:
        super().__init__(message=message, status_code=401)


class LLMRateLimitError(InsightIQException):
    """Raised when OpenAI API rate limits or quota thresholds are exceeded."""
    def __init__(self, message: str = "OpenAI API rate limit or quota exceeded.") -> None:
        super().__init__(message=message, status_code=429)


class LLMTimeoutError(InsightIQException):
    """Raised when an OpenAI API request exceeds configured timeout limits."""
    def __init__(self, message: str = "OpenAI API request timed out.") -> None:
        super().__init__(message=message, status_code=504)


class LLMProviderError(InsightIQException):
    """Raised when OpenAI service is unavailable or encounters server errors."""
    def __init__(self, message: str = "OpenAI API service encountered an unexpected error.") -> None:
        super().__init__(message=message, status_code=502)


class LLMInvalidResponseError(InsightIQException):
    """Raised when the LLM output violates required JSON schemas or formats."""
    def __init__(self, message: str = "LLM response did not adhere to the required output schema.") -> None:
        super().__init__(message=message, status_code=502)
