"""Health Check Endpoint."""

from __future__ import annotations

from typing import Any, Dict
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import settings
from app.database.session import get_db

router = APIRouter(tags=["System Health"])


@router.get("/health", status_code=status.HTTP_200_OK)
@router.get("/api/health", status_code=status.HTTP_200_OK)
def get_system_health(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Probes application health and database connectivity."""
    db_status = "connected"
    try:
        db.execute(text("SELECT 1"))
    except Exception as exc:
        db_status = f"disconnected: {exc}"
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"status": "degraded", "environment": settings.ENVIRONMENT, "database": db_status},
        )

    return {
        "status": "ok",
        "environment": settings.ENVIRONMENT,
        "database": db_status,
    }
