"""Pydantic Schemas for Customer Analytics Endpoints."""

from __future__ import annotations

from decimal import Decimal
from pydantic import BaseModel, Field


class CustomerMetricsResponse(BaseModel):
    """Customer cohort and engagement metrics."""
    total_customers: int = Field(..., description="Total distinct registered customers")
    new_customers: int = Field(..., description="Customers whose first eligible order fell in the period")
    repeat_customers: int = Field(..., description="Customers with 2 or more eligible orders")
    inactive_customers: int = Field(..., description="Customers with no eligible order in the last 90 days")


class TopCustomerItem(BaseModel):
    """Individual high-value customer record."""
    customer_id: int
    name: str
    email: str
    city: str
    total_spend: Decimal = Field(..., description="Cumulative revenue from this customer")
    order_count: int = Field(..., description="Total eligible orders placed by this customer")


class CustomerOrderFrequencyResponse(BaseModel):
    """Distribution of order frequencies across customers."""
    one_order: int
    two_to_three: int
    four_to_five: int
    six_plus: int
    average_orders_per_customer: float
