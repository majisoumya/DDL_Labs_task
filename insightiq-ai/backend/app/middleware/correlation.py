"""Correlation ID Middleware for Request Tracing."""

from __future__ import annotations

import uuid
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from app.logging_config import correlation_id_ctx


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """Middleware that assigns or propagates a unique correlation ID for every request."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Check incoming headers for existing correlation ID
        corr_id = (
            request.headers.get("X-Correlation-ID")
            or request.headers.get("X-Request-ID")
            or str(uuid.uuid4())
        )

        # Store in contextvar for logger access
        token = correlation_id_ctx.set(corr_id)

        try:
            response = await call_next(request)
            # Propagate back to caller
            response.headers["X-Correlation-ID"] = corr_id
            return response
        finally:
            correlation_id_ctx.reset(token)
