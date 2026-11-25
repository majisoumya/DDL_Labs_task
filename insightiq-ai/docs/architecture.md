# InsightIQ AI — System Architecture & Technical Specification

## 1. Architectural Philosophy

InsightIQ AI is designed around three core principles:
1. **Mathematical Correctness & Determinism:** LLMs excel at language comprehension, context extraction, and qualitative reasoning, but fail at exact calculations and large-scale aggregations. InsightIQ AI enforces strict separation: all numerical calculations occur in PostgreSQL and deterministic Python services.
2. **Controlled Tool Calling:** Rather than exposing an open text-to-SQL interface that could execute destructive commands or hallucinate invalid schemas, the AI agent is confined to a curated registry of analytical tools.
3. **Reactive Multi-Agent Graph:** Complex analytical queries (such as investigating month-over-month revenue drops across products and customer cohorts) require multi-step reasoning. LangGraph orchestrates these steps as a directed acyclic state graph with explicit validation nodes.

---

## 2. High-Level System Architecture

```text
+-----------------------------------------------------------------------------------+
|                                  USER INTERFACE                                   |
|   +---------------------------------------+  +--------------------------------+   |
|   |         React BI Dashboard            |  |       Conversational AI        |   |
|   |  - KPI Cards (Revenue, AOV, Orders)   |  |  - Query Input & Suggestions   |   |
|   |  - Recharts (Trends, Cohorts, Bars)   |  |  - Dynamic In-chat Charts      |   |
|   |  - Interactive Date Range Filters     |  |  - Evidence & Reasoning Panel  |   |
|   +---------------------------------------+  +--------------------------------+   |
+------------------------------------------+----------------------------------------+
                                           | HTTP / REST (JSON)
                                           v
+-----------------------------------------------------------------------------------+
|                                FASTAPI BACKEND                                    |
|                                                                                   |
|  [ API Routers ] (/dashboard, /sales, /customers, /products, /chat, /insights)    |
|                                     |                                             |
|        +----------------------------+-----------------------------+               |
|        | Direct REST Calls                                        | Chat Queries  |
|        v                                                          v               |
|  +---------------------------+                      +--------------------------+  |
|  |  Deterministic Analytics  |                      |     LangGraph Agent      |  |
|  |         Services          | <------------------+ |       Orchestrator       |  |
|  |  - sales_service          |     Approved Tool    |  - Intent Understanding  |  |
|  |  - customer_service       |     Invocations      |  - Tool Selection Node   |  |
|  |  - product_service        |                      |  - Validation Node       |  |
|  |  - anomaly_service        |                      |  - Response Synthesizer  |  |
|  +---------------------------+                      +--------------------------+  |
|                |                                                  ^               |
|                | Parameterized SQLAlchemy 2.x ORM                 | LLM Calls     |
|                v                                                  v               |
|  +---------------------------+                      +--------------------------+  |
|  |   PostgreSQL 16 Database  |                      |   OpenAI API (GPT-4o)    |  |
|  |  - customers              |                      |  - Function Calling      |  |
|  |  - products               |                      |  - Structured Synthesis  |  |
|  |  - orders                 |                      +--------------------------+  |
|  |  - order_items            |                                                    |
|  +---------------------------+                                                    |
+-----------------------------------------------------------------------------------+
```

---

## 3. Component Deep Dive

### 3.1. Frontend Layer (React + Vite + Tailwind CSS + Recharts)
- **Dashboard Component:** Consumes REST endpoints to render operational KPIs (Total Revenue, Distinct Orders, Total Customers, AOV) and visual breakdowns (Monthly Revenue Line Chart, Category Distribution Bar Chart, Top Products, and Customer Acquisition Trends).
- **Chat Interface:** Provides conversational interaction with the AI Analyst. Displays conversational bubbles, execution traces (evidence panel showing tool name and query bounds), and dynamic charts directly inline.
- **Dynamic Chart Renderer:** Accepts a standard JSON specification (`{ chart_type, title, x_key, y_key, data }`) returned by backend tool calls and renders the appropriate Recharts component.

### 3.2. Backend API Layer (FastAPI)
- **Dependency Injection:** Centralized `get_db` session generator ensuring scoped database transactions.
- **Validation & Serialization:** Pydantic v2 schemas enforce strict input sanitation (date range ordering, pagination limits, filter values) and consistent output formatting.
- **CORS & Error Handlers:** Unified exception handling mapping domain errors (e.g., `DataNotFoundError`, `InvalidDateRangeException`) into standard RFC 7807 problem details.

### 3.3. Database Layer (PostgreSQL & SQLAlchemy 2.x)
- Relational schema normalized to 3NF representing an enterprise e-commerce model:
  - `customers`: Primary demographics, registration timestamp, city.
  - `products`: Catalog items, categories, current unit prices, inventory stock.
  - `orders`: Transactional headers, customer foreign key, order timestamps, statuses.
  - `order_items`: Line-item breakdown, quantities, historical unit prices at time of sale.
- Referential integrity guaranteed via foreign keys with cascade constraints where appropriate.
- Business rule enforcement:
  - Non-cancelled orders (`status NOT IN ('cancelled', 'returned')`) define revenue and order eligibility.
  - Monetary values stored using `Numeric(12, 2)` to avoid IEEE 754 floating-point inaccuracies.

### 3.4. Analytics Services (The Deterministic Engine)
- Pure Python services encapsulating SQL aggregations:
  - `sales_service.py`: Computes revenue, orders count, AOV, monthly trends, and category splits.
  - `customer_service.py`: Computes customer lifetime value, active vs. inactive accounts (default 90-day inactivity threshold), and cohort retention.
  - `product_service.py`: Identifies high-performing catalog leaders and bottom-decile products for markdown or clearance.
  - `anomaly_service.py`: Evaluates moving averages and statistical variance (Z-scores / percentage variance) to flag sudden spikes or dips.

### 3.5. AI Agent Service (LangGraph Orchestration)
The agent operates as a stateful graph:
1. **State Definition:** Maintains conversation history, user query, selected tool, tool input arguments, raw tool results, validation flags, and final synthesized response.
2. **Understand Question Node:** Normalizes query into structured intent (e.g., `SALES_SUMMARY`, `PRODUCT_PERFORMANCE`, `REVENUE_DECLINE_INVESTIGATION`, `UNSUPPORTED`).
3. **Select Tool Node:** Uses OpenAI tool-calling capabilities constrained strictly to registered analytical tools (`get_sales_metrics`, `get_monthly_revenue`, `get_top_products`, etc.).
4. **Execute Tool Node:** Executes the Python analytical function directly against PostgreSQL with parsed arguments.
5. **Validate Result Node:** Verifies that tool returned valid non-empty data without execution errors.
6. **Generate Answer Node:** LLM synthesizes an evidence-grounded textual response referencing exact values, optionally including a chart specification payload.

---

## 4. Security & Safety Guardrails

| Risk Vector | Mitigation Strategy |
| :--- | :--- |
| **SQL Injection** | Zero dynamic raw SQL string concatenation. All database queries use SQLAlchemy parameterized expressions. |
| **LLM Hallucinations** | System prompts prohibit numerical invention. The agent must cite figures returned by tools. |
| **Secret Leakage** | API keys and connection strings loaded strictly via environment variables (Pydantic BaseSettings). |
| **Privilege Escalation** | Production database credentials are configured with read-only permissions for analytical queries. |
| **Denial of Service** | Query filters enforce pagination caps (e.g., maximum limit of 50 records) and indexed timestamp queries. |
