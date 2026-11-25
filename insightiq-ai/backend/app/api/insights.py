"""FastAPI Router for AI Business Insights and Anomaly Detection."""

from __future__ import annotations

from typing import Any, Dict, List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.logging_config import get_logger
from app.services.anomaly_service import (
    detect_category_anomalies,
    detect_monthly_revenue_anomalies,
    scan_all_anomalies,
)
from app.services.insight_service import generate_executive_insights

logger = get_logger("insightiq.api.insights")

insights_router = APIRouter(prefix="/insights", tags=["Insights & Anomalies"])


@insights_router.get(
    "/anomalies",
    status_code=status.HTTP_200_OK,
    summary="Scan and Retrieve Revenue & Category Anomalies",
    description="Detects statistical outliers, steep percentage drops, and category contractions across transactional history.",
)
def get_revenue_anomalies(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Scans historical data for statistical variances, drops, and category shifts."""
    logger.info("Executing comprehensive anomaly scan")

    all_anomalies = scan_all_anomalies(db)
    serialized_anomalies = [a.model_dump() for a in all_anomalies]

    # Generate executive insights based on verified anomalies and metrics
    executive_insights = generate_executive_insights(db)

    return {
        "status": "success",
        "anomaly_count": len(all_anomalies),
        "anomalies": serialized_anomalies,
        "executive_insights": [i.model_dump() for i in executive_insights],
        "has_critical_anomalies": any(a.severity.value in ["high", "critical"] for a in all_anomalies),
    }
