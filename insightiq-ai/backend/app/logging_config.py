"""Structured Application Logging with Correlation IDs and Secret Redaction."""

from __future__ import annotations

import logging
import re
from contextvars import ContextVar
from typing import Optional

# Context variable holding the correlation ID for the active request thread/task
correlation_id_ctx: ContextVar[Optional[str]] = ContextVar("correlation_id", default=None)

# Regular expressions and replacements for detecting and redacting sensitive credentials
SENSITIVE_PATTERNS = [
    (re.compile(r"sk-[a-zA-Z0-9_-]{20,}", re.IGNORECASE), "sk-******"),
    (re.compile(r"(password[\"']?\s*[:=]\s*[\"']?)([^\"'\s,]+)", re.IGNORECASE), r"\1******"),
    (re.compile(r"(bearer\s+)([a-zA-Z0-9._-]{20,})", re.IGNORECASE), r"\1******"),
]


class CredentialFilter(logging.Filter):
    """Logging filter that redacts API keys, tokens, and passwords from log records."""

    def filter(self, record: logging.LogRecord) -> bool:
        # Inject correlation ID into record
        record.correlation_id = correlation_id_ctx.get() or "N/A"

        # Redact message if string
        if isinstance(record.msg, str):
            record.msg = self._redact(record.msg)

        # Redact args if present
        if record.args:
            if isinstance(record.args, dict):
                record.args = {k: self._redact(str(v)) if isinstance(v, str) else v for k, v in record.args.items()}
            elif isinstance(record.args, (list, tuple)):
                record.args = tuple(self._redact(str(a)) if isinstance(a, str) else a for a in record.args)

        return True

    def _redact(self, text: str) -> str:
        for pattern, replacement in SENSITIVE_PATTERNS:
            text = pattern.sub(replacement, text)
        return text


def configure_logging(log_level: str = "INFO") -> None:
    """Configures root and application loggers with structured formatting."""
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))

    # Remove existing handlers to avoid duplicate log lines
    for h in list(root_logger.handlers):
        root_logger.removeHandler(h)

    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [cid:%(correlation_id)s] [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)
    handler.addFilter(CredentialFilter())
    root_logger.addHandler(handler)


def get_logger(name: str) -> logging.Logger:
    """Retrieves a logger configured with structured filtering."""
    return logging.getLogger(name)
