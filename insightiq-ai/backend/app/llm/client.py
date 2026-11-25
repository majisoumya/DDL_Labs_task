"""Resilient OpenAI Python SDK Client Wrapper with Timeout, Error Handling, and Secret Protection."""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional, Type, TypeVar
from openai import (
    APIConnectionError,
    APIError,
    APITimeoutError,
    AuthenticationError,
    InternalServerError,
    OpenAI,
    RateLimitError,
)
from pydantic import BaseModel, ValidationError

from app.config import settings
from app.exceptions import (
    LLMAuthenticationError,
    LLMInvalidResponseError,
    LLMProviderError,
    LLMRateLimitError,
    LLMTimeoutError,
)
from app.logging_config import get_logger

logger = get_logger("insightiq.llm.client")
T = TypeVar("T", bound=BaseModel)


class OpenAIClient:
    """Production-hardened OpenAI client wrapper for InsightIQ AI."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        timeout_seconds: Optional[int] = None,
        max_retries: Optional[int] = None,
        base_url: Optional[str] = None,
        client_instance: Optional[OpenAI] = None,
    ) -> None:
        """Initializes client with environment defaults and overrides."""
        self._raw_api_key = api_key if api_key is not None else settings.openai_api_key_str
        self.model = model or settings.OPENAI_MODEL
        self.timeout_seconds = timeout_seconds or settings.OPENAI_TIMEOUT_SECONDS
        self.max_retries = max_retries or settings.OPENAI_MAX_RETRIES
        self.base_url = base_url

        # Allow passing an existing or mocked OpenAI instance (useful for unit tests)
        if client_instance is not None:
            self._client = client_instance
        else:
            # Note: We provide placeholder string if empty to avoid SDK init crash,
            # but enforce non-empty check before any network request
            effective_key = self._raw_api_key or "sk-unconfigured-placeholder"
            self._client = OpenAI(
                api_key=effective_key,
                timeout=float(self.timeout_seconds),
                max_retries=self.max_retries,
                base_url=self.base_url,
            )

    def _ensure_api_key_valid(self) -> None:
        """Validates that a legitimate API key has been configured before making calls."""
        if not self._raw_api_key or self._raw_api_key.startswith("sk-unconfigured"):
            logger.error("Attempted LLM call without configured OPENAI_API_KEY")
            raise LLMAuthenticationError(
                "OpenAI API key is missing or not configured. Please set OPENAI_API_KEY in your environment."
            )

    def generate_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        response_format: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Generates a text completion with comprehensive error and timeout handling."""
        self._ensure_api_key_valid()
        eff_temperature = temperature if temperature is not None else settings.OPENAI_TEMPERATURE

        kwargs: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": eff_temperature,
        }
        if max_tokens is not None:
            kwargs["max_tokens"] = max_tokens
        if response_format is not None:
            kwargs["response_format"] = response_format

        try:
            logger.info("Executing OpenAI chat completion with model: %s", self.model)
            response = self._client.chat.completions.create(**kwargs)

            choice = response.choices[0]
            content = choice.message.content or ""

            if response.usage:
                logger.info(
                    "OpenAI completion succeeded. Prompt tokens: %d, Completion tokens: %d, Total: %d",
                    response.usage.prompt_tokens,
                    response.usage.completion_tokens,
                    response.usage.total_tokens,
                )

            return content

        except AuthenticationError as exc:
            logger.error("OpenAI authentication failure: %s", exc)
            raise LLMAuthenticationError("OpenAI authentication failed. Invalid or expired API key.") from exc

        except RateLimitError as exc:
            logger.warning("OpenAI rate limit or quota exceeded: %s", exc)
            raise LLMRateLimitError("OpenAI API rate limit or organization quota exceeded.") from exc

        except APITimeoutError as exc:
            logger.error("OpenAI request timed out after %ds: %s", self.timeout_seconds, exc)
            raise LLMTimeoutError(f"OpenAI API request timed out after {self.timeout_seconds} seconds.") from exc

        except APIConnectionError as exc:
            logger.error("OpenAI network connection error: %s", exc)
            raise LLMProviderError("Unable to establish network connection to OpenAI API services.") from exc

        except InternalServerError as exc:
            logger.error("OpenAI upstream 500 server error: %s", exc)
            raise LLMProviderError("OpenAI servers encountered an internal error. Please retry later.") from exc

        except APIError as exc:
            logger.error("OpenAI generic API error [%s]: %s", getattr(exc, "status_code", "N/A"), exc)
            raise LLMProviderError(f"OpenAI API error: {exc.message}") from exc

        except Exception as exc:
            logger.error("Unexpected error during LLM invocation: %s", exc, exc_info=True)
            raise LLMProviderError(f"Unexpected LLM completion error: {exc}") from exc

    def generate_structured_json(
        self,
        messages: List[Dict[str, str]],
        schema: Type[T],
        temperature: Optional[float] = None,
    ) -> T:
        """Enforces structured JSON output validated against a Pydantic schema."""
        raw_output = self.generate_completion(
            messages=messages,
            temperature=temperature,
            response_format={"type": "json_object"},
        )

        try:
            # Parse raw string and validate via Pydantic
            validated_obj = schema.model_validate_json(raw_output)
            return validated_obj
        except (json.JSONDecodeError, ValidationError) as exc:
            logger.error("Failed to parse LLM structured output into schema %s: %s", schema.__name__, exc)
            raise LLMInvalidResponseError(
                f"LLM output could not be parsed into valid {schema.__name__} schema: {exc}"
            ) from exc


# Module-level client instance cache
_default_llm_client: Optional[OpenAIClient] = None


def get_llm_client() -> OpenAIClient:
    """Returns the default cached OpenAIClient instance."""
    global _default_llm_client
    if _default_llm_client is None:
        _default_llm_client = OpenAIClient()
    return _default_llm_client
