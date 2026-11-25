"""Application Configuration and Environment Settings for InsightIQ AI."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

# Determine base project directory (where .env resides)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    """Centralized, hardened Pydantic application settings."""

    model_config = SettingsConfigDict(
        env_file=str(PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # General Environment
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    LOG_LEVEL: str = "INFO"
    CORS_ORIGINS: Union[str, List[str]] = ["http://localhost:5173", "http://localhost:3000"]

    # PostgreSQL Database Connection
    DATABASE_URL: str = Field(
        default="postgresql://insightiq_user:insightiq_password@localhost:5432/insightiq_db",
        description="Full connection string for SQLAlchemy",
    )
    POSTGRES_USER: str = "insightiq_user"
    POSTGRES_PASSWORD: SecretStr = Field(
        default=SecretStr("insightiq_password"),
        description="Database user password (protected)",
    )
    POSTGRES_DB: str = "insightiq_db"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432

    # Read-Only Database Role (for AI analytics queries)
    ANALYTICS_READONLY_USER: str = "insightiq_readonly"
    ANALYTICS_READONLY_PASSWORD: SecretStr = Field(
        default=SecretStr("readonly_pass"),
        description="Restricted read-only credentials for analytical workloads",
    )
    ANALYTICS_DATABASE_URL: Optional[str] = None

    # Connection Pool & Timeout Settings
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_POOL_RECYCLE: int = 1800
    DB_POOL_PRE_PING: bool = True
    DB_CONNECT_TIMEOUT_SECONDS: int = 10
    DB_COMMAND_TIMEOUT_SECONDS: int = 30

    # OpenAI API & LLM Settings
    OPENAI_API_KEY: SecretStr = Field(
        default=SecretStr(""),
        description="OpenAI API authentication token (protected)",
    )
    OPENAI_MODEL: str = "gpt-4o-mini"
    OPENAI_TIMEOUT_SECONDS: int = 30
    OPENAI_MAX_RETRIES: int = 2
    OPENAI_TEMPERATURE: float = 0.0

    # Rate Limiting Settings
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_MAX_REQUESTS: int = 120  # Max requests per window
    RATE_LIMIT_WINDOW_SECONDS: int = 60  # Sliding window in seconds

    @property
    def cors_origins_list(self) -> List[str]:
        """Returns CORS origins as a sanitized list of strings."""
        if isinstance(self.CORS_ORIGINS, list):
            return self.CORS_ORIGINS
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    @property
    def openai_api_key_str(self) -> str:
        """Retrieves raw OpenAI API key for API client usage."""
        return self.OPENAI_API_KEY.get_secret_value()

    @property
    def postgres_password_str(self) -> str:
        """Retrieves raw PostgreSQL password."""
        return self.POSTGRES_PASSWORD.get_secret_value()

    def safe_dict(self) -> Dict[str, Any]:
        """Exports settings dictionary with sensitive credentials masked."""
        raw = self.model_dump()
        masked = {}
        for k, v in raw.items():
            if isinstance(v, SecretStr) or "password" in k.lower() or "secret" in k.lower() or "key" in k.lower():
                masked[k] = "******"
            else:
                masked[k] = v
        return masked


settings = Settings()
