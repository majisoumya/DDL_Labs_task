"""OpenAI LLM Integration Module for InsightIQ AI."""

from __future__ import annotations

from app.llm.client import OpenAIClient, get_llm_client
from app.llm.prompts import (
    BUSINESS_ANALYST_SYSTEM_PROMPT,
    GROUNDED_SYNTHESIS_PROMPT,
    INTENT_CLASSIFIER_SYSTEM_PROMPT,
)
from app.llm.schemas import (
    AnalysisDomain,
    AnalystInsight,
    AnalystResponse,
    EntityFilter,
    EvidenceGrounding,
    InsightSeverity,
    LLMMessage,
    MetricType,
    TimeframeFilter,
    UserQueryIntent,
)
from app.llm.service import LLMService, get_llm_service

__all__ = [
    "OpenAIClient",
    "get_llm_client",
    "BUSINESS_ANALYST_SYSTEM_PROMPT",
    "INTENT_CLASSIFIER_SYSTEM_PROMPT",
    "GROUNDED_SYNTHESIS_PROMPT",
    "AnalysisDomain",
    "MetricType",
    "InsightSeverity",
    "TimeframeFilter",
    "EntityFilter",
    "UserQueryIntent",
    "EvidenceGrounding",
    "AnalystInsight",
    "AnalystResponse",
    "LLMMessage",
    "LLMService",
    "get_llm_service",
]
