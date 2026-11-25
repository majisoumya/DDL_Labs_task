"""In-Memory Rate Limiting Middleware."""

from __future__ import annotations

import time
from collections import defaultdict, deque
from typing import Deque, Dict
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.config import settings
from app.logging_config import correlation_id_ctx


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Sliding-window in-memory rate limiter per client IP address."""

    EXEMPT_PATHS = {"/health", "/api/health", "/docs", "/redoc", "/openapi.json", "/"}

    def __init__(self, app, max_requests: int = 120, window_seconds: int = 60) -> None:
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.clients: Dict[str, Deque[float]] = defaultdict(deque)

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if not settings.RATE_LIMIT_ENABLED or request.url.path in self.EXEMPT_PATHS:
            return await call_next(request)

        # Identify client IP
        client_ip = request.client.host if request.client else "unknown"
        now = time.time()
        client_history = self.clients[client_ip]

        # Evict timestamps outside sliding window
        while client_history and client_history[0] <= (now - self.window_seconds):
            client_history.popleft()

        # Check limit
        if len(client_history) >= self.max_requests:
            retry_after = int(self.window_seconds - (now - client_history[0])) + 1
            corr_id = correlation_id_ctx.get() or "N/A"
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Rate Limit Exceeded",
                    "detail": f"Maximum of {self.max_requests} requests per {self.window_seconds}s exceeded.",
                    "status_code": 429,
                    "correlation_id": corr_id,
                },
                headers={"Retry-After": str(max(retry_after, 1))},
            )

        client_history.append(now)
        return await call_next(request)
