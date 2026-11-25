"""Business Intelligence LLM Service for Intent Understanding and Grounded Synthesis."""

from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional, Union
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
    MetricType,
    TimeframeFilter,
    UserQueryIntent,
)
from app.logging_config import get_logger

logger = get_logger("insightiq.llm.service")


class LLMService:
    """Orchestrates natural language intent classification and grounded analytical reasoning."""

    def __init__(self, client: Optional[OpenAIClient] = None) -> None:
        """Initializes service with an optional injected client."""
        self.client = client or get_llm_client()

    def parse_user_intent(
        self,
        question: str,
        chat_history: Optional[List[Dict[str, str]]] = None,
    ) -> UserQueryIntent:
        """Parses an unconstrained natural-language business question into a structured intent."""
        logger.info("Parsing user query intent for: '%s'", question)

        history_context = ""
        if chat_history and len(chat_history) > 0:
            recent_turns = chat_history[-6:]
            formatted = []
            for m in recent_turns:
                role = m.get("role", "user")
                content = m.get("content") or m.get("summary") or ""
                if content:
                    formatted.append(f"{role.capitalize()}: {content[:150]}")
            if formatted:
                history_context = "Recent conversation context:\n" + "\n".join(formatted) + "\n\n"

        messages = [
            {"role": "system", "content": INTENT_CLASSIFIER_SYSTEM_PROMPT},
            {"role": "user", "content": f"{history_context}Classify the following business inquiry: '{question}'"},
        ]

        try:
            intent = self.client.generate_structured_json(
                messages=messages,
                schema=UserQueryIntent,
                temperature=0.0,
            )
            logger.info(
                "Successfully parsed intent: domain=%s, metric=%s, ambiguous=%s",
                intent.domain.value,
                intent.primary_metric.value,
                intent.is_ambiguous,
            )
            return intent
        except Exception as exc:
            logger.warning("Structured intent parsing failed; applying rule-based heuristic fallback: %s", exc)
            return self._heuristic_intent_fallback(question, chat_history=chat_history)

    def synthesize_grounded_response(
        self,
        user_question: str,
        evidence_data: Union[Dict[str, Any], List[Any], str],
        chat_history: Optional[List[Dict[str, str]]] = None,
    ) -> AnalystResponse:
        """Synthesizes an executive response strictly grounded in verified database evidence.

        Guardrails enforced:
        - Numbers must match evidence exactly.
        - Zero hallucinated calculations.
        - Documented policy acknowledgement (refunds/cancellations).
        """
        logger.info("Synthesizing grounded response for: '%s'", user_question)

        formatted_evidence = (
            json.dumps(evidence_data, indent=2, default=str)
            if not isinstance(evidence_data, str)
            else evidence_data
        )

        history_context = ""
        if chat_history and len(chat_history) > 0:
            recent_turns = chat_history[-4:]
            formatted = []
            for m in recent_turns:
                role = m.get("role", "user")
                content = m.get("content") or m.get("summary") or ""
                if content:
                    formatted.append(f"{role.capitalize()}: {content[:150]}")
            if formatted:
                history_context = "PREVIOUS CONVERSATION CONTEXT:\n" + "\n".join(formatted) + "\n\n"

        user_content = f"{history_context}" + GROUNDED_SYNTHESIS_PROMPT.format(
            user_question=user_question,
            database_evidence=formatted_evidence,
        )

        messages = [
            {"role": "system", "content": BUSINESS_ANALYST_SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ]

        try:
            response = self.client.generate_structured_json(
                messages=messages,
                schema=AnalystResponse,
                temperature=0.0,
            )
            response.model_used = self.client.model
            return response
        except Exception as exc:
            logger.warning("Grounded response synthesis failed; applying rule-based evidence fallback: %s", exc)
            return self._heuristic_synthesis_fallback(user_question, evidence_data, chat_history=chat_history)

    def _heuristic_synthesis_fallback(
        self,
        user_question: str,
        evidence_data: Union[Dict[str, Any], List[Any], str],
        chat_history: Optional[List[Dict[str, str]]] = None,
    ) -> AnalystResponse:
        """Constructs a deterministic, evidence-grounded response when LLM synthesis is offline."""
        data = evidence_data if isinstance(evidence_data, dict) else {}
        insights: List[AnalystInsight] = []
        metrics: List[EvidenceGrounding] = []
        summary = "Analytical inquiry completed based on verified database records."

        # 1. Multi-Step Revenue Decline Investigation (Takes priority when multi-tool decline plan executes)
        if "investigate_revenue_decline" in data:
            inv = data["investigate_revenue_decline"]
            rev_change = inv.get("revenue_change", {})
            abs_change = float(rev_change.get("absolute_change", 0.0))
            pct_change = rev_change.get("percentage_change")
            pct_str = f"{pct_change:+.1f}%" if pct_change is not None else "0.0%"
            cats = inv.get("category_contributions", [])
            prods = inv.get("product_contributions", [])

            summary_lines = [
                f"### 🔍 Revenue Variance & Diagnostic Analysis",
                f"Sales revenue shifted from **${float(rev_change.get('previous_value', 0)):,.2f}** to **${float(rev_change.get('current_value', 0)):,.2f}**, representing an absolute variance of **${abs_change:,.2f} ({pct_str})** across comparative periods.",
                f"• **Order Volume Variance:** **{int(inv.get('order_change', {}).get('absolute_change', 0)):+d} orders**",
                f"• **Average Order Value Shift:** **${float(inv.get('aov_change', {}).get('absolute_change', 0.0)):+,.2f}**",
            ]
            if cats:
                summary_lines.append("\n### 📉 Category Waterfall Impact")
                for c in cats[:4]:
                    c_name = c.get("category")
                    c_d = float(c.get("absolute_change") or 0.0)
                    c_pct = c.get("percentage_change")
                    pct_info = f" ({c_pct:+.1f}%)" if c_pct is not None else ""
                    summary_lines.append(f"• **{c_name}**: **${c_d:+,.2f}**{pct_info}")
            if prods:
                top_p = prods[0]
                summary_lines.append(f"\n• **Primary SKU Impact:** **{top_p.get('product_name')}** contracted by **${float(top_p.get('absolute_change', 0)):+,.2f}**.")
            summary = "\n".join(summary_lines)

            eg_rev = EvidenceGrounding(
                metric_name="revenue_variance",
                exact_value=abs_change,
                source="orders",
            )
            metrics.append(eg_rev)

            for c in cats[:3]:
                c_name = c.get("category", "Category")
                c_delta = float(c.get("absolute_change") or c.get("absolute_delta") or 0.0)
                eg_c = EvidenceGrounding(
                    metric_name=f"variance_cat_{c_name}",
                    exact_value=c_delta,
                    source="category_variance",
                )
                metrics.append(eg_c)

            for p in prods[:3]:
                p_name = p.get("product_name", "SKU")
                p_delta = float(p.get("absolute_change") or p.get("absolute_delta") or 0.0)
                eg_p = EvidenceGrounding(
                    metric_name=f"variance_sku_{p_name}",
                    exact_value=p_delta,
                    source="product_variance",
                )
                metrics.append(eg_p)

            insights.append(
                AnalystInsight(
                    title="Revenue Contraction & Variance Analysis",
                    finding=f"Total sales revenue shifted by ${abs_change:,.2f} ({pct_str}) across comparative evaluation periods.",
                    evidence=metrics[:2],
                    severity=InsightSeverity.WARNING if abs_change < 0 else InsightSeverity.INFO,
                    actionable_recommendation="Examine category-level demand shifts and target high-propensity customer segments with recovery promotions.",
                )
            )

            if cats:
                top_drag = cats[0]
                top_delta = float(top_drag.get("absolute_change") or top_drag.get("absolute_delta") or 0.0)
                top_share = top_drag.get("contribution_share")
                share_str = f" ({top_share}% of variance)" if top_share else ""
                insights.append(
                    AnalystInsight(
                        title="Primary Category Variance Driver",
                        finding=f"Category '{top_drag.get('category')}' had the largest variance impact of ${top_delta:,.2f}{share_str}.",
                        evidence=[metrics[1]] if len(metrics) > 1 else [],
                        severity=InsightSeverity.WARNING if top_delta < 0 else InsightSeverity.INFO,
                        actionable_recommendation=f"Review pricing, product availability, and promotional cadence within {top_drag.get('category')}.",
                    )
                )

        # 2. Top Products / Revenue by Product
        elif "get_top_products" in data or "get_revenue_by_product" in data:
            items = data.get("get_top_products") or data.get("get_revenue_by_product") or []
            if items:
                top_item = items[0]
                top_name = str(top_item.get("product_name", "Top Product"))
                top_rev = float(top_item.get("revenue", 0.0))
                top_units = int(top_item.get("units_sold", 0))
                total_top_rev = sum(float(i.get("revenue", 0.0)) for i in items)
                
                top_bullets = [
                    f"• **{i.get('product_name')}**: **${float(i.get('revenue', 0)):,.2f}** ({int(i.get('units_sold', 0)):,} units) — *Category: {i.get('category', 'Catalog')}*"
                    for i in items[:5]
                ]
                summary = (
                    f"Top catalog performance analysis shows **'{top_name}'** leads with **${top_rev:,.2f}** in revenue "
                    f"across **{top_units:,} units sold**. The top {len(items)} products generated ${total_top_rev:,.2f} in sales.\n\n"
                    f"### 🏆 Top Revenue Generating Products\n"
                    + "\n".join(top_bullets)
                    + f"\n\n### 📊 Key Performance Insights\n"
                    f"• **Category Leader:** {top_item.get('category', 'Electronics')} accounts for the largest share of high-margin product revenue.\n"
                    f"• **Catalog Depth:** Top SKUs comprise the core revenue foundation of the retail warehouse."
                )
                for item in items[:5]:
                    p_name = str(item.get("product_name", "Item"))
                    p_rev = float(item.get("revenue", 0.0))
                    p_units = int(item.get("units_sold", 0))
                    metrics.append(
                        EvidenceGrounding(
                            metric_name=f"product_{p_name}_revenue",
                            exact_value=p_rev,
                            source="order_items",
                        )
                    )
                insights.append(
                    AnalystInsight(
                        title="Leading Revenue Generating Catalog Items",
                        finding=f"'{top_name}' is the top product with ${top_rev:,.2f} generated from {top_units:,} units sold.",
                        evidence=metrics[:2],
                        severity=InsightSeverity.POSITIVE,
                        actionable_recommendation="Ensure robust supplier replenishment and stock buffers for top-tier revenue drivers to prevent out-of-stock losses.",
                    )
                )
                if len(items) > 1:
                    second_item = items[1]
                    s_name = str(second_item.get("product_name", "Second Item"))
                    s_rev = float(second_item.get("revenue", 0.0))
                    insights.append(
                        AnalystInsight(
                            title="Catalog Concentration & Performance Spread",
                            finding=f"Second-ranked product is '{s_name}' contributing ${s_rev:,.2f}.",
                            evidence=metrics[1:3] if len(metrics) > 2 else metrics[:1],
                            severity=InsightSeverity.INFO,
                            actionable_recommendation="Promote bundled accessories or cross-sell options to capitalize on top SKU traffic.",
                        )
                    )

        # 3. Low Performing Products
        elif "get_low_performing_products" in data:
            items = data["get_low_performing_products"]
            if items:
                lowest = items[0]
                low_name = str(lowest.get("product_name", "Lowest Product"))
                low_rev = float(lowest.get("revenue", 0.0))
                low_units = int(lowest.get("units_sold", 0))
                low_bullets = [
                    f"• **{i.get('product_name')}**: **${float(i.get('revenue', 0)):,.2f}** ({int(i.get('units_sold', 0))} units sold) — *{i.get('category', 'Catalog')}*"
                    for i in items[:5]
                ]
                summary = (
                    f"Identified {len(items)} underperforming or zero-sales catalog items, "
                    f"led by '{low_name}' with ${low_rev:,.2f} in sales ({low_units} units).\n\n"
                    f"### ⚠️ Slow-Moving Catalog Items\n"
                    + "\n".join(low_bullets)
                    + f"\n\n### 📦 Inventory Recommendations\n"
                    f"Review slow-moving items for clearance markdowns, bundling with fast sellers, or adjusting procurement minimums."
                )
                for item in items[:5]:
                    p_name = str(item.get("product_name", "Item"))
                    p_rev = float(item.get("revenue", 0.0))
                    metrics.append(
                        EvidenceGrounding(
                            metric_name=f"low_perf_{p_name}_revenue",
                            exact_value=p_rev,
                            source="order_items",
                        )
                    )
                insights.append(
                    AnalystInsight(
                        title="Underperforming & Zero-Sales Catalog Analysis",
                        finding=f"Identified {len(items)} slow-moving products. Bottom SKU '{low_name}' produced only ${low_rev:,.2f}.",
                        evidence=metrics[:2],
                        severity=InsightSeverity.WARNING,
                        actionable_recommendation="Re-evaluate pricing tiers, run clearance markdown campaigns, or bundle with fast-moving inventory to reduce carrying costs.",
                    )
                )

        # 4. Top Customers
        elif "get_top_customers" in data:
            custs = data["get_top_customers"]
            if custs:
                top_c = custs[0]
                c_name = str(top_c.get("name", "Top Customer"))
                c_spend = float(top_c.get("total_spend", 0.0))
                c_orders = int(top_c.get("order_count", 0))
                total_top_spend = sum(float(c.get("total_spend", 0.0)) for c in custs)
                cust_bullets = [
                    f"• **{c.get('name')}**: **${float(c.get('total_spend', 0)):,.2f}** ({int(c.get('order_count', 0))} orders) — *{c.get('city', 'USA')}*"
                    for c in custs[:5]
                ]
                summary = (
                    f"Customer spend rankings are led by {c_name} with ${c_spend:,.2f} cumulative spend "
                    f"across {c_orders} orders. Top {len(custs)} customer accounts account for ${total_top_spend:,.2f}.\n\n"
                    f"### 👑 Top VIP Customer Accounts\n"
                    + "\n".join(cust_bullets)
                    + f"\n\n### 💡 Retention Summary\n"
                    f"• **Top Account:** **{c_name}** ({top_c.get('city', 'Active Market')}) has an average spend of **${(c_spend / c_orders if c_orders else 0):,.2f}** per order.\n"
                    f"• **High-LTV Focus:** Protecting these top accounts is vital for recurring quarterly revenue."
                )
                for c in custs[:5]:
                    name = str(c.get("name", "Customer"))
                    spend = float(c.get("total_spend", 0.0))
                    metrics.append(
                        EvidenceGrounding(
                            metric_name=f"customer_{name}_spend",
                            exact_value=spend,
                            source="customers",
                        )
                    )
                insights.append(
                    AnalystInsight(
                        title="High-Value VIP Customer Accounts",
                        finding=f"{c_name} is the top customer account with ${c_spend:,.2f} total spend over {c_orders} distinct orders.",
                        evidence=metrics[:2],
                        severity=InsightSeverity.POSITIVE,
                        actionable_recommendation="Implement a dedicated VIP concierge or loyalty tier to maximize lifetime retention of top spenders.",
                    )
                )

        # 5. Customer Order Frequency
        elif "get_customer_order_frequency" in data:
            freq = data["get_customer_order_frequency"]
            avg_orders = float(freq.get("average_orders_per_customer", 1.0))
            summary = (
                f"### 🔄 Customer Order Frequency Distribution\n"
                f"Customer order frequency averages {avg_orders:.2f} orders per registered buyer across the evaluated customer base.\n\n"
                f"• **Average Lifetime Orders:** **{avg_orders:.2f} orders/buyer**\n"
                f"• **Repeat Purchasing Rate:** Order distribution highlights repeat buyer cohorts versus single-purchase acquisition."
            )
            eg_avg = EvidenceGrounding(
                metric_name="average_orders_per_customer",
                exact_value=avg_orders,
                source="orders",
            )
            metrics.append(eg_avg)
            insights.append(
                AnalystInsight(
                    title="Customer Order Frequency Distribution",
                    finding=f"Buyers place an average of {avg_orders:.2f} orders.",
                    evidence=[eg_avg],
                    severity=InsightSeverity.INFO,
                    actionable_recommendation="Set up post-purchase lifecycle workflows to convert single-order customers into repeat buyers.",
                )
            )

        # 6. Sales Growth
        elif "get_sales_growth" in data:
            growth = data["get_sales_growth"]
            rev_pct = growth.get("revenue_growth_pct")
            curr_rev = float(growth.get("current_period", {}).get("revenue", 0.0))
            prev_rev = float(growth.get("previous_period", {}).get("revenue", 0.0))
            pct_str = f"{rev_pct:+.1f}%" if rev_pct is not None else "N/A"
            summary = (
                f"### 📊 Period-Over-Period Sales Growth\n"
                f"Period-over-period sales growth is {pct_str} (${curr_rev:,.2f} current vs ${prev_rev:,.2f} prior period).\n\n"
                f"• **Percentage Change:** **{pct_str}**\n"
                f"• **Current Period Sales:** **${curr_rev:,.2f}**\n"
                f"• **Prior Baseline Sales:** **${prev_rev:,.2f}**\n"
                f"• **Net Difference:** **${(curr_rev - prev_rev):+,.2f}**"
            )
            eg_curr = EvidenceGrounding(metric_name="current_revenue", exact_value=curr_rev, source="orders")
            eg_prev = EvidenceGrounding(metric_name="previous_revenue", exact_value=prev_rev, source="orders")
            metrics.extend([eg_curr, eg_prev])
            insights.append(
                AnalystInsight(
                    title="Sales Growth Trend Comparison",
                    finding=f"Total revenue shifted by {pct_str} comparing the current period (${curr_rev:,.2f}) to prior period (${prev_rev:,.2f}).",
                    evidence=[eg_curr, eg_prev],
                    severity=InsightSeverity.POSITIVE if (rev_pct or 0) > 0 else InsightSeverity.WARNING,
                    actionable_recommendation="Double down on top growth drivers while addressing any underlying drop in order frequency.",
                )
            )

        # 7. Dashboard Summary
        elif "get_dashboard_summary" in data:
            dash = data["get_dashboard_summary"]
            kpis = dash.get("kpis", {})
            rev = float(kpis.get("total_revenue", 0.0))
            orders = int(kpis.get("total_orders", 0))
            custs = int(kpis.get("total_customers", 0))
            aov = float(kpis.get("average_order_value", 0.0))
            summary = (
                f"### 🏢 Consolidated Business Overview\n"
                f"Consolidated business overview: Total revenue reached ${rev:,.2f} over {orders} orders "
                f"from {custs} registered customers (Average Order Value: ${aov:,.2f}).\n\n"
                f"• **Total Revenue:** **${rev:,.2f}**\n"
                f"• **Order Transactions:** **{orders:,} orders**\n"
                f"• **Customer Profiles:** **{custs:,} buyers**\n"
                f"• **Average Order Value:** **${aov:,.2f}**"
            )
            eg_rev = EvidenceGrounding(metric_name="total_revenue", exact_value=rev, source="orders")
            eg_ord = EvidenceGrounding(metric_name="total_orders", exact_value=orders, source="orders")
            eg_cust = EvidenceGrounding(metric_name="total_customers", exact_value=custs, source="customers")
            metrics.extend([eg_rev, eg_ord, eg_cust])
            insights.append(
                AnalystInsight(
                    title="Executive Performance Summary",
                    finding=f"Enterprise retail volume delivered ${rev:,.2f} in net sales across {orders} qualifying orders.",
                    evidence=[eg_rev, eg_ord],
                    severity=InsightSeverity.INFO,
                    actionable_recommendation="Maintain focus on high-margin product categories and repeat customer acquisition.",
                )
            )

        # 8. Sales Metrics
        elif "get_sales_metrics" in data:
            sm = data["get_sales_metrics"]
            rev = float(sm.get("total_revenue", 0.0))
            orders = int(sm.get("total_orders", 0))
            aov = float(sm.get("aov", 0.0))
            summary = (
                f"Total revenue reached ${rev:,.2f} across {orders} qualifying orders with an AOV of ${aov:,.2f}.\n\n"
                f"### 💵 Sales Performance Summary\n"
                f"• **Gross Sales Revenue:** **${rev:,.2f}**\n"
                f"• **Eligible Orders Placed:** **{orders:,} orders**\n"
                f"• **Average Order Value (AOV):** **${aov:,.2f}**"
            )
            eg_rev = EvidenceGrounding(metric_name="total_revenue", exact_value=rev, source="orders")
            eg_ord = EvidenceGrounding(metric_name="total_orders", exact_value=orders, source="orders")
            eg_aov = EvidenceGrounding(metric_name="aov", exact_value=aov, source="orders")
            metrics.extend([eg_rev, eg_ord, eg_aov])
            insights.append(
                AnalystInsight(
                    title="Sales Performance Overview",
                    finding=f"Total gross sales are ${rev:,.2f} over {orders} orders (average order value ${aov:,.2f}).",
                    evidence=[eg_rev, eg_ord],
                    severity=InsightSeverity.POSITIVE if rev > 0 else InsightSeverity.NEUTRAL,
                    actionable_recommendation="Continue monitoring order volume and customer acquisition channels.",
                )
            )

        # 9. Monthly Revenue
        elif "get_monthly_revenue" in data:
            mr = data["get_monthly_revenue"]
            mr_bullets = [
                f"• **{m.get('month')}**: **${float(m.get('revenue', 0)):,.2f}** ({int(m.get('order_count', 0))} orders, {int(m.get('units_sold', 0))} units)"
                for m in mr[-6:]
            ]
            summary = (
                f"Monthly revenue trend analyzed across {len(mr)} recorded calendar periods.\n\n"
                f"### 📈 Historical Monthly Revenue Trajectory\n"
                + "\n".join(mr_bullets)
            )
            for m in mr[-3:]:
                eg_m = EvidenceGrounding(metric_name=f"revenue_{m.get('month')}", exact_value=float(m.get("revenue", 0)), source="orders", time_period=str(m.get("month")))
                metrics.append(eg_m)
            insights.append(
                AnalystInsight(
                    title="Monthly Sales Trend",
                    finding=f"Historical performance comprises {len(mr)} reported months.",
                    evidence=metrics[:2],
                    severity=InsightSeverity.INFO,
                    actionable_recommendation="Use monthly seasonality patterns to project quarterly inventory demand.",
                )
            )

        # 10. Revenue by Category
        elif "get_revenue_by_category" in data:
            cats = data["get_revenue_by_category"]
            top_cat = cats[0]["category"] if cats else "N/A"
            cat_bullets = [
                f"• **{c.get('category')}**: **${float(c.get('revenue', 0)):,.2f}** ({int(c.get('units_sold', 0)):,} units)"
                for c in cats
            ]
            summary = (
                f"Category breakdown analyzed across {len(cats)} product categories led by {top_cat}.\n\n"
                f"### 🏷️ Revenue by Product Category\n"
                + "\n".join(cat_bullets)
                + f"\n\n**Leading Contributor:** **{top_cat}** represents the largest market share in the evaluated timeframe."
            )
            for c in cats:
                eg_c = EvidenceGrounding(metric_name=f"category_{c.get('category')}", exact_value=float(c.get("revenue", 0)), source="order_items")
                metrics.append(eg_c)
            insights.append(
                AnalystInsight(
                    title="Category Performance Distribution",
                    finding=f"{top_cat} is the leading revenue contributor in the evaluated timeframe.",
                    evidence=metrics[:2],
                    severity=InsightSeverity.POSITIVE,
                    actionable_recommendation="Maintain inventory depth in leading categories while optimizing low performers.",
                )
            )

        # 11. Customer Metrics
        elif "get_customer_metrics" in data:
            cm = data["get_customer_metrics"]
            tot_c = cm.get("total_customers", 0)
            rep_c = cm.get("repeat_customers", 0)
            rep_pct = (rep_c / tot_c * 100) if tot_c else 0
            summary = (
                f"Customer base includes {tot_c} total buyers, of which {rep_c} are repeat purchasing customers.\n\n"
                f"### 👥 Customer Base & Retention\n"
                f"• **Total Registered Buyers:** **{tot_c:,} customers**\n"
                f"• **Repeat Buyers (2+ orders):** **{rep_c:,} customers** ({rep_pct:.1f}% repeat rate)\n"
                f"• **Single-Order Buyers:** **{(tot_c - rep_c):,} customers**"
            )
            eg_tot = EvidenceGrounding(metric_name="total_customers", exact_value=tot_c, source="customers")
            eg_rep = EvidenceGrounding(metric_name="repeat_customers", exact_value=rep_c, source="customers")
            metrics.extend([eg_tot, eg_rep])
            insights.append(
                AnalystInsight(
                    title="Customer Loyalty & Retention",
                    finding=f"Repeat buyers account for {rep_c} of {tot_c} active customer profiles.",
                    evidence=[eg_rep],
                    severity=InsightSeverity.POSITIVE if rep_c > 0 else InsightSeverity.NEUTRAL,
                    actionable_recommendation="Implement automated post-purchase loyalty workflows to increase repeat conversion.",
                )
            )

        # General data fallback if key not explicitly recognized
        elif data:
            first_key = list(data.keys())[0]
            val = data[first_key]
            summary = f"Analytical analysis completed for '{first_key}' based on retrieved database records."
            eg_gen = EvidenceGrounding(metric_name=first_key, exact_value=str(val)[:50], source="analytical_db")
            metrics.append(eg_gen)
            insights.append(
                AnalystInsight(
                    title="Analytical Database Findings",
                    finding=f"Tool '{first_key}' produced verified database records matching your inquiry.",
                    evidence=[eg_gen],
                    severity=InsightSeverity.INFO,
                    actionable_recommendation="Explore granular category or customer dimensions for deeper analytical breakdown.",
                )
            )

        return AnalystResponse(
            question=user_question,
            summary=summary,
            insights=insights,
            metrics_referenced=metrics,
            data_limitations_noted="Figures exclude cancelled and returned orders in accordance with governance policy.",
            needs_clarification=False,
            model_used="InsightIQ Grounded Fallback",
        )

    def create_clarification_response(
        self,
        question: str,
        clarification_prompt: str,
        domain: AnalysisDomain = AnalysisDomain.GENERAL,
    ) -> AnalystResponse:
        """Constructs a deterministic clarification response for ambiguous queries."""
        return AnalystResponse(
            question=question,
            summary=(
                "Your inquiry requires additional context to provide an accurate, "
                "grounded analysis against the retail warehouse."
            ),
            insights=[
                AnalystInsight(
                    title="Clarification Required",
                    finding=clarification_prompt,
                    evidence=[],
                    severity=InsightSeverity.INFO,
                    actionable_recommendation="Please specify the desired timeframe, product category, or metric.",
                )
            ],
            metrics_referenced=[],
            needs_clarification=True,
            clarification_question=clarification_prompt,
            model_used=self.client.model,
        )

    def _heuristic_intent_fallback(
        self,
        question: str,
        chat_history: Optional[List[Dict[str, str]]] = None,
    ) -> UserQueryIntent:
        """Deterministic keyword-based intent fallback when LLM parsing is unavailable."""
        q_lower = question.lower()

        # 1. Date & Timeframe parsing
        timeframe = None
        start_date = None
        end_date = None

        # Year detection
        year_match = re.search(r"\b(202\d)\b", question)
        year = year_match.group(1) if year_match else "2024"

        # Quarter detection
        q_match = re.search(r"\b[Qq]([1-4])\b|quarter\s*([1-4])", question, re.IGNORECASE)
        if q_match:
            q_num = int(q_match.group(1) or q_match.group(2))
            if q_num == 1:
                start_date, end_date = f"{year}-01-01", f"{year}-03-31"
            elif q_num == 2:
                start_date, end_date = f"{year}-04-01", f"{year}-06-30"
            elif q_num == 3:
                start_date, end_date = f"{year}-07-01", f"{year}-09-30"
            elif q_num == 4:
                start_date, end_date = f"{year}-10-01", f"{year}-12-31"

        # Month detection
        month_map = {
            "january": ("01", "31"), "jan": ("01", "31"),
            "february": ("02", "29" if year in ("2024", "2028") else "28"), "feb": ("02", "29" if year in ("2024", "2028") else "28"),
            "march": ("03", "31"), "mar": ("03", "31"),
            "april": ("04", "30"), "apr": ("04", "30"),
            "may": ("05", "31"),
            "june": ("06", "30"), "jun": ("06", "30"),
            "july": ("07", "31"), "jul": ("07", "31"),
            "august": ("08", "31"), "aug": ("08", "31"),
            "september": ("09", "30"), "sep": ("09", "30"),
            "october": ("10", "31"), "oct": ("10", "31"),
            "november": ("11", "30"), "nov": ("11", "30"),
            "december": ("12", "31"), "dec": ("12", "31"),
        }
        for m_name, (m_num, m_last) in month_map.items():
            if re.search(r"\b" + m_name + r"\b", q_lower):
                start_date, end_date = f"{year}-{m_num}-01", f"{year}-{m_num}-{m_last}"
                break

        # Explicit ISO dates
        iso_dates = re.findall(r"\b(\d{4}-\d{2}-\d{2})\b", question)
        if len(iso_dates) >= 2:
            start_date, end_date = iso_dates[0], iso_dates[1]
        elif len(iso_dates) == 1:
            start_date = iso_dates[0]

        if start_date or end_date:
            timeframe = TimeframeFilter(start_date=start_date, end_date=end_date, granularity="month")

        # 2. Entity limit parsing
        limit_val = None
        limit_match = re.search(r"\b(?:top|bottom|first|limit)\s*(\d+)\b", q_lower)
        if limit_match:
            limit_val = int(limit_match.group(1))
        entity_filters = EntityFilter(limit=limit_val) if limit_val else None

        # 3. Chart detection
        requires_chart = any(
            w in q_lower
            for w in ["chart", "plot", "graph", "visualize", "visualization", "visual", "trend"]
        )
        preferred_chart_type = None
        for ct in ["line", "bar", "pie", "area"]:
            if ct in q_lower:
                preferred_chart_type = ct
                break

        # 4. Contextual memory resolution from chat history
        prev_domain = None
        prev_metric = None
        prev_tools = None

        if chat_history and len(chat_history) > 0:
            for msg in reversed(chat_history):
                txt = (msg.get("content") or msg.get("summary") or "").lower()
                if "product" in txt or "sku" in txt:
                    prev_domain = AnalysisDomain.PRODUCTS
                    prev_metric = MetricType.TOP_PRODUCTS
                    prev_tools = ["get_top_products"]
                    break
                elif "category" in txt:
                    prev_domain = AnalysisDomain.SALES
                    prev_metric = MetricType.CATEGORY_BREAKDOWN
                    prev_tools = ["get_revenue_by_category"]
                    break
                elif "customer" in txt or "buyer" in txt:
                    prev_domain = AnalysisDomain.CUSTOMERS
                    prev_metric = MetricType.TOP_PRODUCTS
                    prev_tools = ["get_top_customers"]
                    break
                elif "monthly" in txt or "month" in txt:
                    prev_domain = AnalysisDomain.SALES
                    prev_metric = MetricType.MONTHLY_TREND
                    prev_tools = ["get_monthly_revenue"]
                    break
                elif "revenue" in txt or "sales" in txt or "aov" in txt:
                    prev_domain = AnalysisDomain.SALES
                    prev_metric = MetricType.REVENUE
                    prev_tools = ["get_sales_metrics"]
                    break

        # Check if question is a contextual follow-up (e.g. "show as chart", "what about Q1?", "who are they?")
        is_followup = (
            requires_chart
            or any(w in q_lower for w in ["what about", "who are they", "show more", "tell me more", "how about"])
            or len(q_lower.split()) <= 4
        ) and not any(
            w in q_lower
            for w in [
                "product", "products", "item", "sku", "customer", "customers",
                "category", "categories", "monthly", "growth", "why", "decline"
            ]
        )

        # 5. Domain & metric classification
        if "why" in q_lower and any(w in q_lower for w in ["decline", "drop", "down", "decrease", "fall", "loss", "fell", "reduced", "lower"]):
            domain = AnalysisDomain.CROSS_DOMAIN
            primary_metric = MetricType.DIAGNOSTIC_DECLINE
            suggested_tools = ["investigate_revenue_decline"]
        elif any(w in q_lower for w in ["growth", "growing", "percentage change", "growth rate", "period comparison", "compare periods"]):
            domain = AnalysisDomain.SALES
            primary_metric = MetricType.GROWTH
            suggested_tools = ["get_sales_growth"]
        elif any(w in q_lower for w in ["product", "item", "sku", "catalog"]) and any(w in q_lower for w in ["low", "underperform", "zero", "worst", "least", "bottom", "slow", "dead", "lagging"]):
            domain = AnalysisDomain.PRODUCTS
            primary_metric = MetricType.LOW_PERFORMING_PRODUCTS
            suggested_tools = ["get_low_performing_products"]
        elif any(w in q_lower for w in ["product", "item", "sku", "sell", "selling", "catalog"]) and any(w in q_lower for w in ["top", "most", "best", "highest", "popular", "lead", "rank", "revenue", "generate"]):
            domain = AnalysisDomain.PRODUCTS
            primary_metric = MetricType.TOP_PRODUCTS
            suggested_tools = ["get_top_products"]
        elif "top product" in q_lower or "best seller" in q_lower or "most revenue" in q_lower:
            domain = AnalysisDomain.PRODUCTS
            primary_metric = MetricType.TOP_PRODUCTS
            suggested_tools = ["get_top_products"]
        elif any(w in q_lower for w in ["customer", "buyer", "client", "who"]) and any(w in q_lower for w in ["top", "spend", "highest", "best", "vip", "biggest", "valuable"]):
            domain = AnalysisDomain.CUSTOMERS
            primary_metric = MetricType.TOP_PRODUCTS
            suggested_tools = ["get_top_customers"]
        elif any(w in q_lower for w in ["frequency", "how often", "distribution", "bracket"]) and any(w in q_lower for w in ["order", "purchase", "customer"]):
            domain = AnalysisDomain.CUSTOMERS
            primary_metric = MetricType.ORDER_FREQUENCY
            suggested_tools = ["get_customer_order_frequency"]
        elif any(w in q_lower for w in ["customer", "buyer", "churn", "repeat", "active", "client", "retention", "loyalty"]):
            domain = AnalysisDomain.CUSTOMERS
            primary_metric = MetricType.CUSTOMER_COUNT
            suggested_tools = ["get_customer_metrics"]
        elif "category" in q_lower or "categories" in q_lower or "department" in q_lower:
            domain = AnalysisDomain.SALES
            primary_metric = MetricType.CATEGORY_BREAKDOWN
            suggested_tools = ["get_revenue_by_category"]
        elif ("month" in q_lower or "monthly" in q_lower or "trend" in q_lower or "over time" in q_lower) and ("revenue" in q_lower or "sales" in q_lower or "income" in q_lower):
            domain = AnalysisDomain.SALES
            primary_metric = MetricType.MONTHLY_TREND
            suggested_tools = ["get_monthly_revenue"]
        elif any(w in q_lower for w in ["product", "item", "sku"]):
            domain = AnalysisDomain.PRODUCTS
            primary_metric = MetricType.TOP_PRODUCTS
            suggested_tools = ["get_top_products"]
        elif any(w in q_lower for w in ["revenue", "sales", "order", "aov", "spend", "dollar", "gross", "income"]):
            domain = AnalysisDomain.SALES
            primary_metric = MetricType.REVENUE
            suggested_tools = ["get_sales_metrics"]
        elif any(w in q_lower for w in ["overview", "summary", "dashboard", "business", "performance", "kpi", "health", "how are we doing"]):
            domain = AnalysisDomain.GENERAL
            primary_metric = MetricType.UNKNOWN
            suggested_tools = ["get_dashboard_summary"]
        elif is_followup and prev_domain:
            domain = prev_domain
            primary_metric = prev_metric or MetricType.UNKNOWN
            suggested_tools = prev_tools or ["get_sales_metrics"]
        else:
            domain = AnalysisDomain.GENERAL
            primary_metric = MetricType.UNKNOWN
            suggested_tools = ["get_dashboard_summary"]

        is_ambiguous = len(question.strip().split()) < 2 and domain == AnalysisDomain.GENERAL
        clarification = (
            "Could you clarify the timeframe (e.g., Q1 2024), product category, or target metric?"
            if is_ambiguous
            else None
        )

        return UserQueryIntent(
            original_question=question,
            domain=domain,
            primary_metric=primary_metric,
            requires_data=True,
            timeframe=timeframe,
            entity_filters=entity_filters,
            is_ambiguous=is_ambiguous,
            clarification_needed=clarification,
            suggested_tools=suggested_tools,
            requires_chart=requires_chart,
            preferred_chart_type=preferred_chart_type,
        )


def get_llm_service() -> LLMService:
    """Returns a newly configured LLMService."""
    return LLMService()
