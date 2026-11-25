# InsightIQ AI — Demonstration Script & Video Presentation Guide

**Target Audience:** DDL Labs Technical Assessment Evaluators  
**Application URL:** `http://localhost:3000` (Frontend) | `http://localhost:8000/docs` (Backend API Docs)  
**Estimated Run Time:** 5–7 Minutes

---

## Demonstration Sequence Overview

| Step # | Scene | User Action / Query | Expected Output & Feature Highlighted |
| :-: | :--- | :--- | :--- |
| **01** | **Application Launch** | Run `docker-compose up -d --build` or local dev servers. | Health checks pass, PostgreSQL seeds, FastAPI starts on `:8000`, React starts on `:3000`. |
| **02** | **Executive Dashboard** | Navigate to `http://localhost:3000`. | 4 KPI Cards (Revenue, Orders, Customers, AOV), 4 Recharts charts, Anomaly Alert Banner, Audited Ground Truth badge. |
| **03** | **Revenue Query** | In AI Analyst Studio (`/analyst`), ask: *"What is our total revenue?"* | Agent executes `get_sales_metrics`. Answers with exact database value (\$2,490.00 for 2024), citing 5 qualifying orders. |
| **04** | **Tool Execution Audit** | Click "Tool Execution Trace" accordion. | Displays executed tool (`get_sales_metrics`), sanitized arguments, duration in milliseconds, and status badge. |
| **05** | **Catalog Leader Query** | Ask: *"Which products generate the most revenue?"* | Agent calls `get_top_products`. Returns Pro Laptop 15 (\$2,000.00) and Premium Hoodie (\$320.00) with unit metrics. |
| **06** | **Diagnostic Question** | Ask: *"Why did revenue decline last month?"* | Agent initiates multi-step diagnostic workflow across periods. |
| **07** | **Multi-Step Waterfall** | Inspect Evidence Panel findings. | Period-over-period waterfall analysis: isolates category contraction (Electronics drop) and SKU driver (Laptop sales drop), not correlation. |
| **08** | **Dynamic Chart Request** | Ask: *"Show monthly revenue as a chart."* | Agent executes `generate_chart_spec` with `get_monthly_revenue` data. |
| **09** | **Rendered Chart** | Observe inline dynamic chart in chat bubble. | Interactive Recharts area/line chart with custom tooltips, formatted currency axis, and hover highlights. |
| **10** | **Unsupported Query** | Ask: *"What is the weather forecast for tomorrow in Tokyo?"* | Agent detects out-of-scope domain. Politely clarifies analytical scope with zero fabricated numbers. |
| **11** | **Input Validation & Safety** | Test date filter with inverted range (e.g., `2024-12-31` to `2024-01-01`). | Application rejects inverted range with clean 400 Bad Request error banner without crashing or leaking traces. |

---

## Detailed Step-by-Step Narration Script

### Scene 1: Starting the Application (0:00 - 0:45)
- **Visual:** Terminal split screen.
- **Narration:**
  > *"Welcome to InsightIQ AI, an autonomous business intelligence analyst that translates enterprise e-commerce databases into deterministic, evidence-grounded insights. To start the application, we run `docker-compose up --build`. The container orchestrator starts PostgreSQL 16 with a persistent volume, waits for the health check to pass, runs the automated data cleaning and ingestion pipeline, boots our FastAPI backend, and serves our React 18 production frontend via Nginx."*

### Scene 2: The Executive BI Dashboard (0:45 - 1:30)
- **Visual:** Browser opens `http://localhost:3000`.
- **Narration:**
  > *"Here is the InsightIQ AI executive dashboard. At the top, we see our operational KPIs: Total Revenue, Total Orders, Total Customers, and Average Order Value. Notice that every figure matches our database truth—cancelled and returned orders are strictly excluded in accordance with our documented governance policies. Above the KPIs, our statistical anomaly detection engine has detected a revenue contraction between February and March 2024, surfacing a high-severity alert banner with a direct one-click link to investigate."*

### Scene 3 & 4: AI Analyst Revenue Question & Tool Audit (1:30 - 2:30)
- **Visual:** Click "AI Analyst" in sidebar (`/analyst`).
- **Action:** Type *"What is our total revenue?"* and click Send.
- **Narration:**
  > *"Let's switch to the AI Analyst Studio. Notice we are greeted by suggested business questions and an audit drawer. We submit 'What is our total revenue?'. Within milliseconds, the LangGraph agent parses the user intent, selects the approved `get_sales_metrics` tool, queries PostgreSQL, and validates the result. In the response, we see our executive summary and an Evidence Panel separating verified ground-truth metrics from recommendations. Expanding the Tool Execution Trace, we see the exact tool name, sanitized parameters, execution duration, and success status."*

### Scene 5: Top Products Query (2:30 - 3:15)
- **Action:** Type *"Which products generate the most revenue?"*
- **Narration:**
  > *"Next, we ask: 'Which products generate the most revenue?'. The agent selects `get_top_products`. It returns our catalog leaders: the Pro Laptop 15 generating \$2,000.00 across 2 units sold, followed by the Premium Hoodie. Notice that zero sales book products are properly identified, and there are no fabricated numbers."*

### Scene 6 & 7: Multi-Step Revenue Decline Diagnostic (3:15 - 4:15)
- **Action:** Click the suggested chip or type: *"Why did revenue decline last month?"*
- **Narration:**
  > *"Now for the core assessment inquiry: 'Why did revenue decline last month?'. Instead of asking the LLM to guess, LangGraph executes a multi-step investigation pipeline: it resolves the comparative calendar periods, calculates revenue, orders, and AOV across both windows, and conducts category and SKU-level waterfall analysis. The evidence panel proves that the revenue drop was driven by an 87.5% contraction in Electronics orders—specifically zero Pro Laptop purchases in March—rather than an across-the-board customer churn."*

### Scene 8 & 9: Dynamic Chart Generation (4:15 - 5:00)
- **Action:** Type: *"Show monthly revenue as a chart."*
- **Narration:**
  > *"InsightIQ AI can also generate interactive visualizations on demand. When we ask: 'Show monthly revenue as a chart', the backend generates a strictly validated Pydantic `ChartSpec` and sends it to the frontend. Here, React dynamically renders an interactive Recharts visualization inline within the message thread. Hovering over any data point reveals audited monthly metrics."*

### Scene 10: Unsupported Question Handling (5:00 - 5:30)
- **Action:** Type: *"What is the weather forecast for tomorrow in Tokyo?"*
- **Narration:**
  > *"Next, we test system boundaries with an out-of-scope query: 'What is the weather forecast for tomorrow in Tokyo?'. Unlike unconstrained chatbots that fabricate answers, the agent identifies that the query lies outside the retail analytics domain, acknowledges its boundaries, and guides the user back to valid business inquiries without hallucinating."*

### Scene 11: Data Governance & Invalid Input Handling (5:30 - 6:00)
- **Visual:** Click "Audited Ground Truth" badge in header to open Data Quality Modal.
- **Action:** Set inverted date range in toolbar (`2024-12-31` to `2024-01-01`).
- **Narration:**
  > *"Finally, clicking the 'Audited Ground Truth' badge in the header opens our Dataset Quality & Governance Modal, displaying complete referential integrity audits, transaction lifecycle breakdowns, and quarantined volume. If a user enters an inverted date range where start date exceeds end date, the API traps the error, returning a clean 400 Bad Request with an actionable error banner. InsightIQ AI provides enterprise reliability from database to chat bubble."*
