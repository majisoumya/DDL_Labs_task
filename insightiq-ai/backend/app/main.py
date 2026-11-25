"""Main FastAPI Application Entrypoint for InsightIQ AI."""

from __future__ import annotations

from contextlib import asynccontextmanager
import logging
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import (
    analyst_router,
    charts_router,
    customers_router,
    dashboard_router,
    export_router,
    health_router,
    insights_router,
    products_router,
    sales_router,
    system_router,
)
from app.config import settings
from app.exceptions import InsightIQException
from app.logging_config import configure_logging, correlation_id_ctx, get_logger
from app.middleware import CorrelationIdMiddleware, RateLimitMiddleware

# -----------------------------------------------------------------------------
# Structured Application Logging
# -----------------------------------------------------------------------------
configure_logging(settings.LOG_LEVEL)
logger = get_logger("insightiq.api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initializes database schema if missing on application startup."""
    try:
        from app.database.session import init_db
        init_db()
        logger.info("Database schema verified and tables created if missing.")
    except Exception as exc:
        logger.warning("Database schema auto-initialization deferred or failed: %s", exc)
    yield


app = FastAPI(
    title="InsightIQ AI — Autonomous Business Intelligence API",
    description=(
        "Production-ready REST API translating natural-language business questions "
        "and enterprise data warehouses into deterministic, grounded analytics and insights."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# -----------------------------------------------------------------------------
# Middleware Stack (Execution order: CorrelationId -> RateLimit -> CORS -> Router)
# -----------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    RateLimitMiddleware,
    max_requests=settings.RATE_LIMIT_MAX_REQUESTS,
    window_seconds=settings.RATE_LIMIT_WINDOW_SECONDS,
)

app.add_middleware(CorrelationIdMiddleware)


# -----------------------------------------------------------------------------
# Standardized Exception Handlers (RFC 7807 Aligned with Correlation IDs)
# -----------------------------------------------------------------------------
@app.exception_handler(InsightIQException)
async def domain_exception_handler(request: Request, exc: InsightIQException) -> JSONResponse:
    """Handles domain-specific business exceptions with clean status codes."""
    cid = correlation_id_ctx.get() or "N/A"
    logger.warning("Domain exception at %s [%s]: %s", request.url.path, exc.status_code, exc.message)
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.__class__.__name__,
            "detail": exc.message,
            "status_code": exc.status_code,
            "correlation_id": cid,
        },
        headers={"X-Correlation-ID": cid},
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handles FastAPI/Pydantic request validation errors without leaking internals."""
    cid = correlation_id_ctx.get() or "N/A"
    error_messages = []
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error.get("loc", []))
        msg = error.get("msg", "Invalid value")
        error_messages.append(f"{field}: {msg}")
    detail_str = "; ".join(error_messages) if error_messages else "Request validation failed."

    logger.warning("Request validation error at %s (cid: %s): %s", request.url.path, cid, detail_str)
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "ValidationError",
            "detail": detail_str,
            "status_code": 422,
            "correlation_id": cid,
        },
        headers={"X-Correlation-ID": cid},
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Standardizes FastAPI HTTPExceptions into uniform JSON format."""
    cid = correlation_id_ctx.get() or "N/A"
    detail_content = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": "HTTPException",
            "detail": detail_content,
            "status_code": exc.status_code,
            "correlation_id": cid,
        },
        headers={"X-Correlation-ID": cid},
    )


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError) -> JSONResponse:
    """Translates standard Python ValueErrors into clean HTTP 400 responses."""
    cid = correlation_id_ctx.get() or "N/A"
    logger.warning("Bad request (ValueError) at %s (cid: %s): %s", request.url.path, cid, exc)
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "error": "Bad Request",
            "detail": str(exc),
            "status_code": 400,
            "correlation_id": cid,
        },
        headers={"X-Correlation-ID": cid},
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catches unhandled server exceptions, logs full traceback internally, and returns safe 500."""
    cid = correlation_id_ctx.get() or "N/A"
    logger.error("Unhandled server exception at %s (cid: %s): %s", request.url.path, cid, exc, exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal Server Error",
            "detail": "An unexpected server error occurred.",
            "status_code": 500,
            "correlation_id": cid,
        },
        headers={"X-Correlation-ID": cid},
    )


# -----------------------------------------------------------------------------
# Router Registration
# -----------------------------------------------------------------------------
# Health endpoints available at root and /api
app.include_router(health_router)

# Analytics domain routers mounted under /api prefix
app.include_router(dashboard_router, prefix="/api")
app.include_router(sales_router, prefix="/api")
app.include_router(products_router, prefix="/api")
app.include_router(customers_router, prefix="/api")
app.include_router(charts_router, prefix="/api")
app.include_router(analyst_router, prefix="/api")
app.include_router(export_router, prefix="/api")
app.include_router(system_router, prefix="/api")
app.include_router(insights_router, prefix="/api")


@app.get("/", include_in_schema=False)
def root_redirect():
    """Root entrypoint returning API metadata."""
    return {
        "name": "InsightIQ AI API",
        "version": "1.0.0",
        "status": "online",
        "documentation": "/docs",
    }
