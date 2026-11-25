"""Waterfall Contribution and Variance Decomposition for Revenue Investigations."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from app.agents.investigations.comparison import safe_percentage_change


class CategoryContribution(BaseModel):
    """Variance analysis of a product category's contribution to overall revenue change."""
    category: str = Field(..., description="Product category name")
    current_revenue: float = Field(..., description="Revenue generated in current period")
    previous_revenue: float = Field(..., description="Revenue generated in baseline period")
    absolute_change: float = Field(..., description="Current minus previous revenue")
    percentage_change: Optional[float] = Field(None, description="Percentage growth/contraction")
    contribution_share: float = Field(
        ..., description="Percentage of total overall revenue variance explained by this category"
    )
    is_decline: bool = Field(..., description="True if category revenue decreased")


class ProductContribution(BaseModel):
    """Item-level variance analysis identifying SKU drivers of revenue change."""
    product_id: int = Field(..., description="Unique product identifier")
    product_name: str = Field(..., description="Catalog product name")
    category: str = Field(..., description="Associated product category")
    current_revenue: float = Field(..., description="Product revenue in current period")
    previous_revenue: float = Field(..., description="Product revenue in previous period")
    current_units: int = Field(..., description="Units sold in current period")
    previous_units: int = Field(..., description="Units sold in previous period")
    absolute_change: float = Field(..., description="Revenue delta (current - previous)")
    percentage_change: Optional[float] = Field(None, description="Percentage revenue change")
    units_change: int = Field(..., description="Volume delta in units sold")
    is_decline: bool = Field(..., description="True if product revenue decreased")


class CustomerActivityComparison(BaseModel):
    """Customer acquisition, buyer count, and cohort engagement variance."""
    current_active_buyers: int = Field(..., description="Distinct customers who purchased in current period")
    previous_active_buyers: int = Field(..., description="Distinct customers who purchased in previous period")
    buyer_delta: int = Field(..., description="Change in active buyer count")
    current_new_customers: int = Field(..., description="New customers acquired in current period")
    previous_new_customers: int = Field(..., description="New customers acquired in previous period")
    observations: List[str] = Field(default_factory=list, description="Factual observations on customer behavior")


def analyze_category_contributions(
    current_categories: List[Dict[str, Any]],
    previous_categories: List[Dict[str, Any]],
    total_revenue_delta: float,
) -> List[CategoryContribution]:
    """Computes category-level waterfall contributions to the overall revenue delta."""
    curr_map = {row["category"]: float(row["revenue"]) for row in current_categories}
    prev_map = {row["category"]: float(row["revenue"]) for row in previous_categories}
    all_categories = sorted(list(set(curr_map.keys()) | set(prev_map.keys())))

    contributions: List[CategoryContribution] = []

    for cat in all_categories:
        c_rev = round(curr_map.get(cat, 0.0), 2)
        p_rev = round(prev_map.get(cat, 0.0), 2)
        abs_change = round(c_rev - p_rev, 2)
        pct_change = safe_percentage_change(c_rev, p_rev)

        # Contribution share: percentage of overall delta attributable to this category
        if total_revenue_delta != 0.0:
            share = round((abs_change / total_revenue_delta) * 100.0, 2)
        else:
            share = 0.0

        contributions.append(
            CategoryContribution(
                category=cat,
                current_revenue=c_rev,
                previous_revenue=p_rev,
                absolute_change=abs_change,
                percentage_change=pct_change,
                contribution_share=share,
                is_decline=abs_change < 0,
            )
        )

    # Sort by absolute change ascending (most severe contractions first)
    contributions.sort(key=lambda x: x.absolute_change)
    return contributions


def analyze_product_contributions(
    current_products: List[Dict[str, Any]],
    previous_products: List[Dict[str, Any]],
    limit: int = 10,
) -> List[ProductContribution]:
    """Computes SKU-level revenue and volume shifts between two periods."""
    curr_map = {row["product_id"]: row for row in current_products}
    prev_map = {row["product_id"]: row for row in previous_products}
    all_ids = set(curr_map.keys()) | set(prev_map.keys())

    product_contribs: List[ProductContribution] = []

    for pid in all_ids:
        c_row = curr_map.get(pid, {})
        p_row = prev_map.get(pid, {})

        name = c_row.get("product_name") or p_row.get("product_name") or f"Product #{pid}"
        cat = c_row.get("category") or p_row.get("category") or "Unknown"

        c_rev = round(float(c_row.get("revenue", 0.0)), 2)
        p_rev = round(float(p_row.get("revenue", 0.0)), 2)
        c_units = int(c_row.get("units_sold", 0))
        p_units = int(p_row.get("units_sold", 0))

        abs_change = round(c_rev - p_rev, 2)
        pct_change = safe_percentage_change(c_rev, p_rev)
        units_delta = c_units - p_units

        product_contribs.append(
            ProductContribution(
                product_id=pid,
                product_name=name,
                category=cat,
                current_revenue=c_rev,
                previous_revenue=p_rev,
                current_units=c_units,
                previous_units=p_units,
                absolute_change=abs_change,
                percentage_change=pct_change,
                units_change=units_delta,
                is_decline=abs_change < 0,
            )
        )

    # Sort by absolute change ascending (largest drops first)
    product_contribs.sort(key=lambda x: x.absolute_change)
    return product_contribs[:limit]


def analyze_customer_activity(
    current_metrics: Dict[str, Any],
    previous_metrics: Dict[str, Any],
    current_orders: int,
    previous_orders: int,
) -> CustomerActivityComparison:
    """Analyzes customer cohort dynamics and active buyer count fluctuations."""
    curr_new = int(current_metrics.get("new_customers", 0))
    prev_new = int(previous_metrics.get("new_customers", 0))

    # Active buyers approximated from unique order buyers or metrics
    curr_buyers = int(current_metrics.get("total_customers", 0))
    prev_buyers = int(previous_metrics.get("total_customers", 0))
    buyer_delta = current_orders - previous_orders

    observations: List[str] = []
    if previous_orders > 0 and current_orders < previous_orders:
        pct_drop = round(((previous_orders - current_orders) / previous_orders) * 100.0, 1)
        observations.append(f"Total eligible orders decreased by {pct_drop}% (from {previous_orders} to {current_orders}).")

    if curr_new < prev_new:
        observations.append(f"New customer acquisitions fell from {prev_new} to {curr_new}.")
    elif curr_new > prev_new:
        observations.append(f"New customer acquisitions increased from {prev_new} to {curr_new}.")

    return CustomerActivityComparison(
        current_active_buyers=curr_buyers,
        previous_active_buyers=prev_buyers,
        buyer_delta=buyer_delta,
        current_new_customers=curr_new,
        previous_new_customers=prev_new,
        observations=observations,
    )
