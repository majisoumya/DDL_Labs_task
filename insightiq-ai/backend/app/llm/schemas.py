"""Structured Pydantic Schemas for LLM Intent Understanding, Insights, and Responses."""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Literal, Optional, Union
from pydantic import BaseModel, Field


# -----------------------------------------------------------------------------
# 1. Domain & Metric Enums
# -----------------------------------------------------------------------------
class AnalysisDomain(str, Enum):
    """Business analytical domain categories."""
    SALES = "sales"
    CUSTOMERS = "customers"
    PRODUCTS = "products"
    CROSS_DOMAIN = "cross_domain"
    GENERAL = "general"


class MetricType(str, Enum):
    """Specific measurable business indicators."""
    REVENUE = "revenue"
    ORDERS = "orders"
    AOV = "aov"
    GROWTH = "growth"
    MONTHLY_TREND = "monthly_trend"
    CATEGORY_BREAKDOWN = "category_breakdown"
    CUSTOMER_COUNT = "customer_count"
    REPEAT_RATE = "repeat_rate"
    INACTIVE_CUSTOMERS = "inactive_customers"
    ORDER_FREQUENCY = "order_frequency"
    TOP_PRODUCTS = "top_products"
    LOW_PERFORMING_PRODUCTS = "low_performing_products"
    PRODUCT_SALES_QTY = "product_sales_qty"
    DIAGNOSTIC_DECLINE = "diagnostic_decline"
    UNKNOWN = "unknown"


class InsightSeverity(str, Enum):
    """Categorization of insight business importance."""
    INFO = "info"
    POSITIVE = "positive"
    WARNING = "warning"
    CRITICAL = "critical"


# -----------------------------------------------------------------------------
# 2. Query Understanding & Intent Schemas
# -----------------------------------------------------------------------------
class TimeframeFilter(BaseModel):
    """Extracted temporal parameters from natural language input."""
    start_date: Optional[str] = Field(None, description="Start date in YYYY-MM-DD format")
    end_date: Optional[str] = Field(None, description="End date in YYYY-MM-DD format")
    granularity: Optional[str] = Field("month", description="Aggregation granularity (e.g. day, month, year)")


class EntityFilter(BaseModel):
    """Extracted dimensional filters from user queries."""
    categories: List[str] = Field(default_factory=list, description="Target product categories")
    product_names: List[str] = Field(default_factory=list, description="Target product names or IDs")
    cities: List[str] = Field(default_factory=list, description="Target customer cities")
    limit: Optional[int] = Field(None, description="Requested top/bottom item limit")


class UserQueryIntent(BaseModel):
    """Structured interpretation of natural language user query."""
    original_question: str = Field(..., description="Original user prompt")
    domain: AnalysisDomain = Field(..., description="Target business domain")
    primary_metric: MetricType = Field(..., description="Primary metric requested")
    requires_data: bool = Field(True, description="Whether database query/tools are needed to answer")
    timeframe: Optional[TimeframeFilter] = Field(None, description="Extracted time filters")
    entity_filters: Optional[EntityFilter] = Field(None, description="Extracted categorical or entity filters")
    is_ambiguous: bool = Field(False, description="Whether the question lacks sufficient specificity")
    clarification_needed: Optional[str] = Field(None, description="Question to ask if ambiguous")
    suggested_tools: List[str] = Field(default_factory=list, description="Recommended analytics tools to invoke")
    requires_chart: bool = Field(False, description="Whether the user explicitly requested a chart or visualization")
    preferred_chart_type: Optional[str] = Field(None, description="Preferred chart type if mentioned (line, bar, pie, area)")


# -----------------------------------------------------------------------------
# 3. Grounded Evidence & Insight Schemas
# -----------------------------------------------------------------------------
class EvidenceGrounding(BaseModel):
    """Specific verifiable metric data point backing an insight."""
    metric_name: str = Field(..., description="Name of the metric (e.g. Total Revenue, AOV)")
    exact_value: Union[float, int, str] = Field(..., description="Deterministic numeric value returned by database")
    source: str = Field(..., description="Service or database query source")
    time_period: Optional[str] = Field(None, description="Applicable timeframe for this metric")


class AnalystInsight(BaseModel):
    """A single factual, evidence-backed finding."""
    title: str = Field(..., description="Concise insight title")
    finding: str = Field(..., description="Specific finding derived strictly from provided evidence")
    evidence: List[EvidenceGrounding] = Field(default_factory=list, description="Factual metrics supporting finding")
    severity: InsightSeverity = Field(default=InsightSeverity.INFO, description="Business impact level")
    actionable_recommendation: Optional[str] = Field(None, description="Strategic executive recommendation")


class AnalystResponse(BaseModel):
    """Complete structured response generated by InsightIQ AI Analyst."""
    question: str = Field(..., description="Original user question")
    summary: str = Field(..., description="Executive summary grounded strictly in provided evidence")
    insights: List[AnalystInsight] = Field(default_factory=list, description="Detailed evidence-backed findings")
    metrics_referenced: List[EvidenceGrounding] = Field(default_factory=list, description="All data points cited")
    needs_clarification: bool = Field(False, description="True if query could not be answered unambiguously")
    clarification_question: Optional[str] = Field(None, description="Clarification prompt for user if needed")
    data_limitations_noted: Optional[str] = Field(
        None, description="Documented policies applied (e.g. refund/cancellation exclusions)"
    )
    chart_spec: Optional[Dict[str, Any]] = Field(
        None, description="Structured Recharts-compatible chart specification if requested or generated"
    )
    model_used: str = Field(default="", description="OpenAI model utilized")
    tokens_used: Optional[int] = Field(None, description="Total tokens consumed")


# -----------------------------------------------------------------------------
# 4. Message Schemas for LLM Communication
# -----------------------------------------------------------------------------
class LLMMessage(BaseModel):
    """Standard message representation for chat completions."""
    role: Literal["system", "user", "assistant"]
    content: str
