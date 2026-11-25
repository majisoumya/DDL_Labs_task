# InsightIQ AI — Autonomous Business Intelligence Analyst

> **DDL Labs AI Engineer Technical Assessment Project**  
> An autonomous business intelligence platform that translates natural-language retail questions into deterministic PostgreSQL analytics, multi-step diagnostic investigations, dynamic Recharts visualizations, and evidence-grounded executive insights with zero numerical hallucinations.

---

## Table of Contents
1. [Project Overview](#1-project-overview)
2. [Business Problem](#2-business-problem)
3. [Features](#3-features)
4. [Technology Stack](#4-technology-stack)
5. [System Architecture](#5-system-architecture)
6. [Database Design](#6-database-design)
7. [Data Ingestion & Cleaning Pipeline](#7-data-ingestion--cleaning-pipeline)
8. [Business Calculation Definitions](#8-business-calculation-definitions)
9. [AI & LLM Integration](#9-ai--llm-integration)
10. [LangGraph Agent Workflow](#10-langgraph-agent-workflow)
11. [Controlled Tool Calling](#11-controlled-tool-calling)
12. [Multi-Step Diagnostic Analysis](#12-multi-step-diagnostic-analysis)
13. [Dynamic Chart Generation](#13-dynamic-chart-generation)
14. [Installation Guide](#14-installation-guide)
15. [Environment Setup](#15-environment-setup)
16. [Local Execution (Manual)](#16-local-execution-manual)
17. [Docker Execution (Containerized)](#17-docker-execution-containerized)
18. [API Documentation](#18-api-documentation)
19. [Testing & Quality Assurance](#19-testing--quality-assurance)
20. [Known Limitations & Roadmap](#20-known-limitations--roadmap)

---

## 1. Project Overview

**InsightIQ AI** is an enterprise-grade AI analytics system designed to bridge the divide between non-technical retail decision-makers and complex data warehouses. 

Traditional natural-language analytics tools suffer from severe flaws: they generate unconstrained SQL that exposes databases to SQL injection, hallucinate calculations, fail to account for business governance policies (e.g., refunds and cancellations), and collapse under complex questions like *"Why did revenue decline last month?"*.

InsightIQ AI eliminates these risks by enforcing a **strict separation of concerns**:
- **Deterministic Analytics Engine:** 100% of numerical calculations occur in PostgreSQL using parameterized SQLAlchemy ORM queries and Decimal precision.
- **Controlled Agentic Orchestration:** A LangGraph state machine translates user queries into structured plans, invoking pre-vetted Python analytics tools with Pydantic argument boundaries.
- **Evidence-Grounded Explanations:** The LLM receives verified analytical results before synthesizing text. If data does not exist, the system states so honestly.

---

## 2. Business Problem

Modern retail and e-commerce leadership teams need immediate answers to critical business questions:
- *What was our total revenue in Q1, and how does it compare to prior periods?*
- *Which product categories are driving sales volume vs. margin?*
- *Who are our repeat buyers, and what is our churn exposure?*
- *Why did revenue contract 87% between February and March 2024?*

Answering these questions typically requires submitting tickets to business intelligence teams, resulting in days of delay. When organizations deploy unconstrained text-to-SQL LLMs, they frequently encounter:
1. **Mathematical Hallucination:** Generative models fabricating sums, percentages, and order counts.
2. **Policy Blindness:** Treating cancelled or refunded transactions as earned revenue.
3. **Correlation vs. Causation Confusion:** Blaming customer churn for a revenue drop caused by stockouts of a single flagship product.
4. **Security Vulnerabilities:** Direct text-to-SQL opening databases to data deletion or credential exfiltration.

InsightIQ AI solves these challenges with mathematical determinism, transparent tool traces, and multi-step period-over-period waterfall analysis.

---

## 3. Features

### Executive BI Dashboard
- **Operational KPI Cards:** Real-time Total Revenue, Qualifying Orders, Customer Count, and Average Order Value (AOV).
- **Interactive Visualizations:** Monthly Revenue Trends (Area), Category Revenue Splits (Pie), Top 5 Products by Revenue (Bar), and Customer/Sales Velocity (Bar).
- **Date Range Filtering:** Presets (All Data, FY 2024, Q1 2024, Q2 2024) and custom date pickers.
- **Statistical Anomaly Alert Banner:** Automatically surfaces month-over-month contractions with Z-scores and one-click "Investigate with AI" triggers.
- **Audited Ground Truth Modal:** Detailed data governance breakdown showing active catalog volume, order status lifecycles, and policy-excluded revenue (\$1,080.00).
- **Streaming CSV Export:** Instant downloads for filtered sales reports, product catalog rankings, and customer cohort lists.

### AI Analyst Studio
- **Conversational Analytics:** Natural language question-answering powered by LangGraph and OpenAI (`gpt-4o-mini`).
- **Starter Inquiry Chips:** Pre-built questions spanning sales velocity, catalog leaders, customer cohorts, and diagnostic decline investigations.
- **Tool Execution Trace Panel:** Transparent drawer showing executed tool names, sanitized arguments, duration in milliseconds, and status badges.
- **Grounded Evidence Panel:** Explicitly distinguishes **Verified Ground-Truth Metrics**, **Factual Insights**, **Strategic Recommendations**, and **Documented Governance Caveats**.
- **Dynamic In-Chat Charts:** Automatic generation and rendering of interactive Recharts visualizations within chat responses.
- **Audit History Drawer:** Slide-over audit log tracking query latencies, executed tools, and one-click query re-run triggers.
- **Zero-Hallucination Fallback:** Resilient rule-based synthesis engine ensuring accurate metrics are returned even during upstream LLM outages or missing API keys.

---

## 4. Technology Stack

| Layer | Technologies | Purpose |
| :--- | :--- | :--- |
| **Backend Framework** | Python 3.11, FastAPI | High-performance asynchronous REST API with OpenAPI documentation |
| **Database & ORM** | PostgreSQL 16, SQLAlchemy 2.x | ACID-compliant relational data warehouse with strict foreign keys and indexes |
| **Data Processing** | Pandas 2.2, NumPy | Automated profiling, dirty data cleaning, validation, and ingestion pipelines |
| **Agent Orchestration** | LangGraph, LangChain Core | Directed acyclic state graph orchestrating intent classification and tool execution |
| **LLM Integration** | OpenAI Python SDK 1.x (`gpt-4o-mini`) | Structured intent classification, tool calling, and grounded response synthesis |
| **Validation & Schemas** | Pydantic v2, Pydantic-Settings | Strict validation of API payloads, tool boundaries, and chart specifications |
| **Frontend Framework** | React 18, Vite 5 | Reactive single-page application with modular component architecture |
| **Styling & Icons** | Tailwind CSS 3.4, Lucide React | Modern executive SaaS design with professional slate/navy color palette |
| **Data Visualizations** | Recharts 2.12 | Interactive SVG charts (Line, Area, Bar, Pie) with custom tooltips |
| **Testing & QA** | Pytest, FastAPI TestClient, Vitest | 271 automated unit, integration, and failure scenario tests (100% pass rate) |
| **Containerization** | Docker, Docker Compose, Nginx Alpine | Multi-stage container orchestration with automated DB seeding and health checks |

---

## 5. System Architecture

InsightIQ AI is built around a layered architecture enforcing strict separation between language models and database operations:

```
+-----------------------------------------------------------------------------------+
|                                  USER INTERFACE                                   |
|   +---------------------------------------+  +--------------------------------+   |
|   |         React BI Dashboard            |  |       AI Analyst Studio        |   |
|   |  - KPI Cards (Revenue, AOV, Orders)   |  |  - Conversational Chat Input   |   |
|   |  - Recharts (Trends, Cohorts, Bars)   |  |  - Tool Execution Status Panel |   |
|   |  - Date Filtering & CSV Export        |  |  - Grounded Evidence Panel     |   |
|   |  - Anomaly Alert Banner               |  |  - Dynamic In-Chat Charts      |   |
|   +---------------------------------------+  +--------------------------------+   |
+------------------------------------------+----------------------------------------+
                                           | HTTP / REST (JSON)
                                           v
+-----------------------------------------------------------------------------------+
|                                FASTAPI BACKEND                                    |
|                                                                                   |
|  [ API Routers ] (/dashboard, /sales, /customers, /products, /analyst, /export)   |
|                                     |                                             |
|        +----------------------------+-----------------------------+               |
|        | Direct REST Calls                                        | Chat Inquiries|
|        v                                                          v               |
|  +---------------------------+                      +--------------------------+  |
|  |  Deterministic Analytics  |                      |     LangGraph Agent      |  |
|  |         Services          | <------------------+ |       Orchestrator       |  |
|  |  - sales_service          |     Approved Tool    |  - Question Understanding|  |
|  |  - customer_service       |     Invocations      |  - Tool Selection Node   |  |
|  |  - product_service        |                      |  - Execution & Validation|  |
|  |  - anomaly_service        |                      |  - Grounded Synthesis    |  |
|  +---------------------------+                      +--------------------------+  |
|                |                                                  ^               |
|                | Parameterized SQLAlchemy 2.x ORM                 | LLM Calls     |
|                v                                                  v               |
|  +---------------------------+                      +--------------------------+  |
|  |   PostgreSQL 16 Database  |                      |    OpenAI API (GPT-4o)   |  |
|  |  - customers              |                      |  - Intent Classification |  |
|  |  - products               |                      |  - Structured Synthesis  |  |
|  |  - orders                 |                      +--------------------------+  |
|  |  - order_items            |                                                    |
|  +---------------------------+                                                    |
+-----------------------------------------------------------------------------------+
```

Detailed architectural diagrams, sequence flows, and component specs are in [docs/architecture.md](docs/architecture.md).

---

## 6. Database Design

The data warehouse conforms to Third Normal Form (3NF) across four core entities:

```mermaid
erDiagram
    CUSTOMERS ||--o{ ORDERS : "places (1:N)"
    ORDERS ||--|{ ORDER_ITEMS : "contains (1:N)"
    PRODUCTS ||--o{ ORDER_ITEMS : "included_in (1:N)"

    CUSTOMERS {
        int customer_id PK
        string name
        string email UK
        string city
        timestamp created_at
    }

    PRODUCTS {
        int product_id PK
        string product_name
        string category
        numeric price
        int stock
    }

    ORDERS {
        int order_id PK
        int customer_id FK
        timestamp order_date
        string status
        numeric total_amount
    }

    ORDER_ITEMS {
        int item_id PK
        int order_id FK
        int product_id FK
        int quantity
        numeric unit_price
    }
```

- **Indexes:** Composite index `(order_date, status)` on `orders` for temporal filtering; composite index `(order_id, product_id)` on `order_items`; unique index on `customers.email`.
- **Integrity Constraints:** Foreign keys enforce `ON DELETE CASCADE` for order items and `ON DELETE RESTRICT` for products with sales history. Check constraints enforce non-negative prices and positive quantities.

Complete column types and constraints are documented in [docs/data_dictionary.md](docs/data_dictionary.md).

---

## 7. Data Ingestion & Cleaning Pipeline

The automated ingestion pipeline (`app.data_processing.ingestion`) processes raw retail CSV files through five validation stages:
1. **Schema Inspection & Profiling:** Validates column names, data types, null counts, and candidate primary keys.
2. **Type Coercion & Normalization:** Parses ISO-8601 dates, strips whitespace, lowercases emails, and converts currency strings into exact Decimals.
3. **Data Cleaning Rules:** Excludes corrupt rows (negative prices or zero quantities) and deduplicates line items.
4. **Referential Integrity Validation:** Verifies all `customer_id` and `product_id` foreign keys exist before order ingestion.
5. **Idempotent Ingestion:** Safely upserts records without duplicating rows across successive runs.

Run the pipeline via CLI:
```bash
python scripts/ingest_data.py --data-dir data/raw --db-url postgresql://insightiq_user:insightiq_password@localhost:5432/insightiq_db
```

---

## 8. Business Calculation Definitions

All business metrics are codified with strict mathematical definitions:

- **Order Eligibility:**
  $$\text{Qualifying Orders} = \{o \in \text{Orders} \mid \text{status}(o) \notin (\text{'cancelled'}, \text{'returned'})\StatusCode\}$$
  *Cancelled and returned orders are strictly excluded from revenue, order counts, and AOV calculations.*
- **Total Revenue:**
  $$\text{Total Revenue} = \sum_{i \in \text{OrderItems of Qualifying Orders}} (\text{quantity}_i \times \text{unit\_price}_i)$$
- **Average Order Value (AOV):**
  $$\text{AOV} = \frac{\text{Total Revenue}}{\text{Count of Distinct Qualifying Orders}} \quad (\text{yields } \$0.00 \text{ if orders} = 0)$$
- **Period-over-Period Growth:**
  $$\text{Growth \%} = \left( \frac{\text{Metric}_{\text{current}} - \text{Metric}_{\text{previous}}}{\text{Metric}_{\text{previous}}} \right) \times 100 \quad (\text{yields } \text{None} \text{ if previous} = 0)$$
- **Repeat Customer Rate:**
  $$\text{Repeat Rate \%} = \left( \frac{\text{Customers with } \ge 2 \text{ completed orders}}{\text{Customers with } \ge 1 \text{ completed order}} \right) \times 100$$

---

## 9. AI & LLM Integration

The OpenAI client is encapsulated in `app.llm.client.OpenAIClient`:
- **Model:** Configurable via `OPENAI_MODEL` environment variable (defaults to `gpt-4o-mini`).
- **Timeout & Retries:** Strict 30-second timeout with exponential backoff on transient network failures.
- **Exception Mapping:** Upstream OpenAI exceptions map to domain exceptions:
  - `AuthenticationError` $\to$ `LLMAuthenticationError (401)`
  - `RateLimitError` $\to$ `LLMRateLimitError (429)`
  - `APITimeoutError` $\to$ `LLMTimeoutError (504)`
- **System Prompt Guardrails:** Business analyst instructions explicitly forbid:
  - Inventing numerical results or datasets.
  - Pretending failed queries succeeded.
  - Generating unsupported causal assertions without analytical backing.

---

## 10. LangGraph Agent Workflow

Conversational intelligence is orchestrated using a stateful directed graph (`app.agents.graph`):

```mermaid
flowchart TD
    Start([User Question]) --> Understand[1. Understand Question Node]
    Understand --> CheckAmbiguous{Is Ambiguous?}
    CheckAmbiguous -- Yes --> Clarify[Generate Clarification]
    CheckAmbiguous -- No --> Select[2. Select Tools Node]
    Select --> Execute[3. Execute Tools Node]
    Execute --> Validate[4. Validate Results Node]
    Validate --> CheckValid{Valid Data?}
    CheckValid -- Error --> HandleErr[Error Handling Node]
    CheckValid -- Success --> Generate[5. Generate Answer Node]
    Clarify --> End([Return Response])
    HandleErr --> End
    Generate --> End
```

- **Loop Prevention:** `MAX_AGENT_STEPS = 5` is enforced in `routing.py`. Runaway execution is impossible.
- **Trace Persistence:** Every node records timestamped execution duration in milliseconds into `state["execution_trace"]`.

---

## 11. Controlled Tool Calling

The agent can only invoke tools pre-registered in `app.tools.registry.ToolRegistry`:
- `get_sales_metrics`: Returns revenue, orders, and AOV for date ranges.
- `get_monthly_revenue`: Monthly revenue trends and order counts.
- `get_revenue_by_category`: Category distribution and revenue percentages.
- `get_top_products`: Products ranked by revenue and units sold.
- `get_low_performing_products`: Bottom-performing or zero-sales SKUs.
- `get_top_customers`: High-value customer accounts and spend.
- `get_customer_metrics`: Total buyers, repeat buyers, and retention rates.
- `investigate_revenue_decline`: Multi-step period-over-period diagnostic waterfall.
- `generate_chart_spec`: Structured Recharts visualization generator.

All tool arguments are validated against strict Pydantic schemas enforcing date formats and integer limits ($\le 100$).

---

## 12. Multi-Step Diagnostic Analysis

When a user asks: *"Why did revenue decline last month?"*, the system executes an automated investigation pipeline (`app.agents.investigations.revenue_decline`):
1. **Timeframe Resolution:** Resolves current month (`2024-03`) and comparative baseline (`2024-02`).
2. **Gross Variance Isolation:** Computes absolute and percentage changes in Revenue, Orders, and AOV.
3. **Category Contribution Waterfall:** Breaks down revenue changes across merchandise categories.
4. **SKU-Level Driver Ranking:** Identifies the exact products accounting for the largest share of the contraction.
5. **Customer Activity Cross-Check:** Differentiates customer churn from order-size reductions.
6. **Correlation vs. Causation Guard:** Generates evidence-backed statements distinguishing proven data drops from unproven hypotheses.

---

## 13. Dynamic Chart Generation

The system supports on-demand dynamic chart generation for line, bar, pie, and area charts:
- **Contract Schema:** Standardized Pydantic `ChartSpec`:
  ```json
  {
    "chart_type": "line",
    "title": "Monthly Revenue Trend",
    "x_key": "month",
    "y_key": "revenue",
    "data": [
      { "month": "2024-01", "revenue": 1220.00 },
      { "month": "2024-02", "revenue": 1210.00 },
      { "month": "2024-03", "revenue": 60.00 }
    ],
    "metadata": { "unit": "$", "total_points": 3 }
  }
  ```
- **Validation:** Enforces supported types, non-empty axis keys, numeric integrity, and empty dataset flags.
- **Frontend Renderer:** `DynamicChart.jsx` renders interactive Recharts charts with responsive containers and custom tooltips.

---

## 14. Installation Guide

### Prerequisites
- **Python:** 3.11 or higher
- **Node.js:** 20.x or higher & npm
- **Database:** PostgreSQL 16 (or Docker for containerized run)
- **OpenAI API Key:** For conversational features (optional; heuristic fallback works without it)

---

## 15. Environment Setup

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd insightiq-ai
   ```

2. Copy the environment configuration:
   ```bash
   cp .env.example .env
   ```

3. Configure `.env`:
   ```ini
   # General
   ENVIRONMENT=development
   DEBUG=True
   APP_PORT=8000
   
   # PostgreSQL Connection
   POSTGRES_USER=insightiq_user
   POSTGRES_PASSWORD=insightiq_password
   POSTGRES_DB=insightiq_db
   POSTGRES_HOST=localhost
   POSTGRES_PORT=5432
   DATABASE_URL=postgresql://insightiq_user:insightiq_password@localhost:5432/insightiq_db
   
   # OpenAI Configuration
   OPENAI_API_KEY=your-openai-api-key-here
   OPENAI_MODEL=gpt-4o-mini
   
   # Frontend URL
   VITE_API_URL=http://localhost:8000
   ```

---

## 16. Local Execution (Manual)

### Step 1: Backend Setup
```bash
# Navigate to backend directory
cd backend

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run database ingestion & seeding
python ../scripts/ingest_data.py --data-dir ../data/raw

# Start FastAPI development server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
*Backend API Docs will be live at `http://localhost:8000/docs`.*

### Step 2: Frontend Setup
```bash
# Open a new terminal and navigate to frontend directory
cd frontend

# Install Node dependencies
npm install

# Start Vite development server
npm run dev
```
*Frontend UI will be live at `http://localhost:5173`.*

---

## 17. Docker Execution (Containerized)

To start the complete multi-container stack (PostgreSQL, Backend, Frontend) with a single command:

```bash
# Build and start all services in detached mode
docker-compose up -d --build
```

### Container Endpoints:
- **Frontend Dashboard & Chat:** `http://localhost:3000`
- **FastAPI Interactive Swagger Docs:** `http://localhost:8000/docs`
- **PostgreSQL Database:** `localhost:5432`

### Tear Down:
```bash
# Stop containers and preserve persistent database volume
docker-compose down

# Stop containers and wipe database volume for clean reset
docker-compose down -v
```

---

## 18. API Documentation

Interactive Swagger documentation is available at `/docs` and ReDoc at `/redoc`.

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/health` | Health probe checking database connectivity (returns 503 if DB disconnected). |
| `GET` | `/api/dashboard` | Consolidated executive BI payload (KPIs, trends, category splits, catalog leaders). |
| `GET` | `/api/sales/metrics` | Total revenue, qualifying orders, and AOV (supports date filtering). |
| `GET` | `/api/sales/monthly` | Monthly revenue trends and order volumes. |
| `GET` | `/api/sales/categories` | Revenue breakdown and percentage distribution by product category. |
| `GET` | `/api/sales/growth` | Period-over-period comparative growth percentages. |
| `GET` | `/api/products/top` | Catalog leaders ranked by revenue or units sold. |
| `GET` | `/api/products/low-performing` | Underperforming and zero-sales products. |
| `GET` | `/api/customers/metrics` | Customer counts, repeat buyers, and repeat customer rate. |
| `GET` | `/api/customers/top` | High-value customer accounts ranked by spend. |
| `GET` | `/api/insights/anomalies` | Statistical anomaly detection with Z-scores and executive alerts. |
| `GET` | `/api/system/quality-summary` | Data governance audit, status lifecycles, and policy exclusions. |
| `GET` | `/api/export/sales-csv` | Streaming CSV export of sales metrics and monthly trends. |
| `GET` | `/api/export/products-csv` | Streaming CSV export of product catalog rankings. |
| `GET` | `/api/export/customers-csv` | Streaming CSV export of customer cohorts. |
| `GET` | `/api/analyst/suggestions` | Suggested business questions for chat interface. |
| `POST` | `/api/analyst/chat` | AI Analyst conversational endpoint executing LangGraph workflows. |
| `GET` | `/api/analyst/history` | Analytics execution audit history. |
| `DELETE` | `/api/analyst/history` | Clear analytics execution audit history. |

---

## 19. Testing & Quality Assurance

InsightIQ AI includes 271 automated tests across the backend and frontend:

### Running Backend Tests (Pytest)
```bash
python -m pytest backend/tests -v -o "pythonpath=backend"
```
*Result: 215 passed across 19 test modules (100% pass rate).*

### Running Dedicated Failure Scenarios Suite
```bash
python -m pytest backend/tests/test_failure_scenarios.py -v -o "pythonpath=backend"
```
*Result: 10 passed across 10 critical failure scenarios.*

### Running Frontend Tests (Vitest)
```bash
npm --prefix "frontend" test -- --run
```
*Result: 56 passed across 10 test suites (100% pass rate).*

### Verifying Production Frontend Build
```bash
npm --prefix "frontend" run build
```
*Result: Vite production bundle built cleanly in ~11s.*

Complete test methodology and audit findings are documented in [docs/testing_report.md](docs/testing_report.md).

---

## 20. Known Limitations & Roadmap

As documented in [docs/known_limitations.md](docs/known_limitations.md):
- **In-Memory Audit Buffer:** Execution history (`/api/analyst/history`) resides in an in-memory buffer and resets on process restart. Production roadmap includes migrating to a persistent PostgreSQL audit table.
- **Single Currency:** Calculations assume unified USD (`$`). Multi-currency transactions require an exchange rate table.
- **Distributed Rate Limiting:** Rate limiting uses an in-memory sliding window; horizontal scaling across multiple pods recommends Redis backing.

---

## License & Evaluation Notice

This project was developed for the **DDL Labs AI Engineer Technical Assessment**. All code, database schemas, and AI agent architectures are designed for enterprise evaluation.
