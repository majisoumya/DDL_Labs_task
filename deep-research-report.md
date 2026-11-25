# InsightIQ AI — Implementation Playbook  

**Project:** InsightIQ AI — Your Autonomous AI Business Intelligence Analyst (DDL Labs Technical Assessment)  

```text
You are my senior AI engineering development partner.

We are building InsightIQ AI, an AI-powered Business Intelligence Analyst for the DDL Labs AI Engineer technical assessment.

YOUR DEVELOPMENT RULES:

1. Follow the 20 phases in the specified order.  
2. Work on only one phase at a time.  
3. Read the complete implementation playbook before starting.  
4. Inspect the current repository before making changes.  
5. Never destroy working code without a clear reason.  
6. Never implement fake or hardcoded analytics.  
7. Never invent dataset values.  
8. Never expose API keys or credentials.  
9. Never allow unrestricted LLM-generated SQL.  
10. Keep backend business logic separate from API routes.  
11. Keep frontend components reusable.  
12. Follow Python and React best practices.  
13. Write meaningful tests.  
14. Run relevant tests after implementation.  
15. Fix failures before declaring a phase complete.  
16. Explain important architectural decisions.  
17. Document assumptions.  
18. Maintain a project progress file.  
19. Do not skip required assessment features.  
20. Do not move to the next phase without explicit approval.

IMPORTANT WORKFLOW:

For each phase:
A. Inspect the existing implementation.  
B. Explain the work to be performed.  
C. Create or modify files.  
D. Implement the feature.  
E. Run tests.  
F. Fix discovered issues.  
G. Update documentation.  
H. Summarize the completed work.  
I. Show the exact commands to verify it.  
J. List remaining issues.

You are responsible for helping me build a real, working application, not merely generating code snippets.
```  

## 1. Project Master Specification  

### Project Vision  
 InsightIQ AI is an AI-driven business intelligence system where LLM-powered agents collaborate to analyze structured data. The image above symbolizes the synergy between human analysts and autonomous AI agents. Multi-agent AI systems have been shown to outperform single-agent models on complex tasks. We will design a multi-agent LLM framework that allows specialized AI components to query data, calculate metrics, and provide insights securely and reliably.  

**Product Name:** InsightIQ AI  
**Tagline:** Your Autonomous AI Business Intelligence Analyst  
**Mission:** Build a production-ready AI application that translates natural-language business questions into data-driven insights, visualizations and recommendations.  

### Technology Stack  
- **Language:** Python 3.11+ (for backend and AI tools)  
- **Data & ML:** Pandas, NumPy, Scikit-learn (for preprocessing and anomaly detection)  
- **Database:** PostgreSQL (with SQLAlchemy ORM)  
- **Backend:** FastAPI (REST API with Pydantic validation)  
- **AI/LLM:** OpenAI API (GPT-4/GPT-3.5) for natural language; LangGraph for agent workflows  
- **Agents/Orchestration:** LangGraph (multi-agent workflows), OpenAI function-calling (for tool invocation)  
- **Frontend:** React.js with Vite, Tailwind CSS for styling, Recharts for charts  
- **Testing:** Pytest (backend), Vitest + React Testing Library (frontend)  
- **Deployment:** Docker & Docker Compose  
- **Version Control:** Git (GitHub repository)  

These technologies were chosen to match the job description and ensure a robust, maintainable, and testable application.

### Architecture Overview  
The system is divided into frontend and backend layers. The **React frontend** provides a dashboard and chat interface for users to ask questions and view analytics. It communicates via HTTP to the **FastAPI backend**. The backend has two main components:  
- **Analytics Service:** Python functions and SQL (via SQLAlchemy) perform all actual data calculations (sales, customers, products).  
- **AI Agent Service (LangGraph):** Orchestrates LLM calls and controlled tool invocations.  

The agent’s workflow (managed by LangGraph) ensures the LLM only selects from **approved tools** (Python analytics functions) to get real data. For example, for a question about revenue, the LLM will trigger a `get_sales_metrics` tool; the backend will run SQL to fetch the real revenue, then the LLM uses that factual number to generate an answer. This keeps all numerical results grounded in the database.  

All business logic (calculations of revenue, AOV, etc.) is implemented in Python/SQL, not in the LLM. The LLM is used for understanding questions, selecting tools, chaining multi-step queries, and phrasing answers. This separation ensures correctness and security.

### Database Design  
Use PostgreSQL with these tables:  

- **customers** (`customer_id` PK, name, email, city, created_at)  
- **products** (`product_id` PK, product_name, category, price (Decimal), stock)  
- **orders** (`order_id` PK, customer_id FK, order_date (timestamp), status)  
- **order_items** (`item_id` PK, order_id FK, product_id FK, quantity (int), unit_price (Decimal)`)  

Relationships:  
- `orders.customer_id` → `customers.customer_id`  
- `order_items.order_id` → `orders.order_id`  
- `order_items.product_id` → `products.product_id`  

Business rules (to document and implement consistently):  
- **Revenue:** Sum of (`quantity * unit_price`) for all order_items of non-cancelled orders.  
- **Orders:** Count of distinct, eligible orders.  
- **AOV (Average Order Value):** `revenue / eligible_orders`.  
- **Top Products:** Ranked by revenue.  
- **Low-Performing Products:** Define by low sales/revenue threshold (e.g., bottom 10%).  
- **Total Customers:** Count of distinct customers.  
- **Repeat Customers:** Customers with ≥2 eligible orders.  
- **New Customers:** Customers whose first eligible order is within the query period.  
- **Inactive Customers:** Customers with no purchases in the last *X* days (configurable, default 90).  

Explicitly handle order status: Define which statuses count as cancelled/refunded (e.g. “cancelled”, “returned”) and exclude them from revenue. Document this policy in README.

## 2. Development Phases  

### Phase 1 – Project Initialization  
**Objective:** Establish the project skeleton and repository.  

**Tasks:**  
- Inspect the existing workspace (if any).  
- Create root directory `insightiq-ai/`.  
- Create subdirectories: `backend/`, `frontend/`, `data/raw/`, `data/processed/`, `docs/`, `scripts/`, `docker/`.  
- Create `README.md` with project overview (briefly outline the vision and structure).  
- Create `.gitignore` (ignore `__pycache__`, `node_modules`, `.env`, `.env.local`, `docker-compose.override.yml`).  
- Create `.env.example` (placeholders for API keys, DB URLs).  
- Document the stack and architecture in `docs/architecture.md`.  
- Create `docs/PROJECT_PROGRESS.md` to track phase completion.  

**Acceptance Criteria:**  
- The directory structure is correct.  
- README.md, .gitignore, .env.example exist with basic content.  
- No real secrets in code or env files.  
- `docs/PROJECT_PROGRESS.md` initialized.

```text
Implement PHASE 1: Project Initialization

- Inspect current directory structure (if any).
- Propose and create a clean project layout:
  ```
  insightiq-ai/
    backend/
    frontend/
    data/
      raw/
      processed/
    docs/
    scripts/
    docker/
    README.md
    .gitignore
    .env.example
    docker-compose.yml
  ```
- Set up empty README with project title and summary.
- Add .gitignore (Python, Node, VSCode, etc.).
- Create .env.example with placeholders (e.g. OPENAI_API_KEY=, DATABASE_URL=).
- In docs/, add architecture.md describing the architecture textually.
- Initialize docs/PROJECT_PROGRESS.md (with at least Phase 1 entry).

Deliverables:
- Confirmation of created folders/files.
- README content with project summary.
- .gitignore entries (Python caches, node_modules, env files).
- .env.example template.
- docs/PROJECT_PROGRESS.md tracking Phase 1.
- Commands: `ls` and `tree` outputs to verify structure.

Important: Do not write any business logic yet.
Do not proceed to the next phase without approval.
```

### Phase 2 – Dataset Inspection and Profiling  
**Objective:** Explore the provided dataset (or create sample data) to understand its structure.  

**Tasks:**  
- Locate any provided CSV/Excel files in `data/raw/`. If none are provided, create a synthetic retail dataset with columns matching the model above (include example orders, items, customers).  
- Use Pandas to read the data. Check row/column counts, data types.  
- Identify missing values, duplicates, inconsistent entries.  
- Check date formats and convert to timestamp if needed.  
- Validate numeric fields (price ≥0, quantity ≥0).  
- Determine primary keys: likely `order_id`, `item_id`, `product_id`, `customer_id`.  
- Document findings in `docs/data_quality_report.md`: list issues found, missing values count, any corrections needed.  

**Acceptance Criteria:**  
- Raw data is not modified.  
- `docs/data_quality_report.md` clearly summarizes schema, data issues, and decisions (e.g. dropping duplicates).  
- If synthetic data is created, it is clearly labeled and realistic.  
- Provide sample code/test showing profiling results (e.g. counts, nulls).

```text
Implement PHASE 2: Dataset Inspection and Profiling

- Check for any files in data/raw/. If present, inspect them.
- Write a profiling script (Pandas) in backend/app/data_processing/profiler.py:
  - Load CSV/Excel.
  - Print shape, columns, data types.
  - Count missing values and duplicates per column.
  - Identify potential keys (unique count vs. total).
- Output results to docs/data_quality_report.md.
- Document any column name differences (e.g. 'cust_id' vs 'customer_id').
- Include lines showing handling of bad data (e.g. dropping a row or converting formats).
- Add pytest for profiling functions (e.g. with a small test CSV).
- Summarize findings in data_quality_report.md.

Important: Do not alter raw files. Keep raw data intact.
Do not proceed to next phase without approval.
```

### Phase 3 – Database Schema (PostgreSQL + SQLAlchemy)  
**Objective:** Define the database models and set up PostgreSQL connection.  

**Tasks:**  
- In `backend/`, configure SQLAlchemy (use `.env` for DATABASE_URL).  
- Create models in `backend/app/database/models/`: `customer.py`, `product.py`, `order.py`, `order_item.py`.  
- Define columns/types based on data inspection. Use `Numeric` or `Decimal` for prices.  
- Set up primary/foreign keys and relationships. Add any needed indexes (e.g. on order_date).  
- Create `session.py` to manage connections, `base.py` for declarative base.  
- Ensure environment variables are used (e.g. via Pydantic settings).  

**Acceptance Criteria:**  
- Models reflect inspected data schema exactly (correct column names/types).  
- Relationships (`ForeignKey` and `relationship`) are set up.  
- Database tables can be created without errors.
- Connection info is not hardcoded.  

```text
Implement PHASE 3: Database Schema with SQLAlchemy

- Configure SQLAlchemy 2.x in backend/app/database/:
  - base.py: declarative base class.
  - connection.py: read DATABASE_URL from settings, create engine.
  - session.py: sessionmaker with engine.
- Under models/ directory, define:
  - customer.py: Customer model.
  - product.py: Product model.
  - order.py: Order model.
  - order_item.py: OrderItem model.
- Use Column types: Integer, String, Numeric (for money), DateTime.
- Define PKs and FKs. Use relationship() where appropriate.
- Add a UniqueConstraint if needed (e.g. on a business key).
- In `app/config.py` (or settings), parse DATABASE_URL from .env (via Pydantic BaseSettings).
- Test: Create tables by running a quick script or using Alembic. Alternatively, include a unit test verifying one can add and query a simple record.
- Document any differences from plan (if raw data had different names).

Important: Do not insert sample data here. Focus on structure only.
Do not proceed until models are correct and tested.
```

### Phase 4 – Data Cleaning and Ingestion  
**Objective:** Build a pipeline to load and clean raw data into PostgreSQL.  

**Tasks:**  
- Write ETL scripts (Pandas + SQLAlchemy) under `backend/app/data_processing/`: `cleaner.py`, `validators.py`, `ingestion.py`.  
- Map raw columns to our model fields (document any renaming).  
- Cleaning steps: trim whitespace, fix data types, drop or impute missing values (with business rules, e.g. drop rows with null IDs).  
- Validate data: no negative prices/qty, dates valid. Log or collect bad rows for review.  
- Use transactions: each table load should be atomic.  
- Avoid duplicates: if ingestion is re-run, it should upsert or skip existing records (e.g. use `ON CONFLICT DO NOTHING`).  
- After loading, output summary: rows read, inserted, rejected.  

**Acceptance Criteria:**  
- Raw CSVs remain unchanged.  
- No data is silently lost without logging.  
- Running the ingestion twice does not duplicate data.  
- Provide an `ingest_data.py` script (or use `scripts/ingest_data.py`) to run the pipeline.  
- Include tests for cleaning functions (e.g. validating a bad row gets caught).  

```text
Implement PHASE 4: Data Cleaning and Ingestion

- Create data_processing/cleaner.py and validators.py:
  - Functions to clean column names, strip strings, convert types.
  - Functions to check date formats and numeric ranges.
- Create data_processing/ingestion.py:
  - Read each source file with Pandas.
  - Clean and validate data row by row.
  - Use SQLAlchemy session to insert rows into tables.
  - Use session.merge() or ON CONFLICT to avoid duplicates.
  - Commit only after all rows processed (or use bulk insert with transaction).
- Provide a script scripts/ingest_data.py that calls ingestion code.
- Logging:
  - Print counts: total rows, valid rows, invalid rows.
  - Print examples of any dropped data.
- Tests:
  - Use pytest to test cleaning logic (e.g. missing values lead to ValueError).
  - Simulate inserting duplicate to ensure it’s skipped gracefully.
- Document any assumptions (e.g. if a customer ID is missing, drop order).

Important: Do not hardcode file paths. Use config or detect files in data/raw.
Proceed only after verifying database tables are correctly populated.
```

### Phase 5 – Core Business Analytics Engine  
**Objective:** Implement all required analytics calculations in Python/SQL, independent of any AI.  

**Tasks:**  
- In `backend/app/services/`, implement analytics services:
  - `sales_service.py`: total revenue, total orders, AOV, monthly revenue, revenue by category, revenue by product, growth calculations.
  - `customer_service.py`: total customers, new customers (in date range), repeat customers, inactive customers, top customers by revenue.
  - `product_service.py`: top-selling products, low-performing products, category revenue breakdown.
- Each function should take date range or filters as needed.
- Use SQLAlchemy for queries (avoid loading full tables into Pandas if possible). Parameterize all queries to prevent SQL injection.
- Handle edge cases (e.g. zero orders -> AOV=0).  
- Return results in Python data structures (dicts or lists) with clear keys.  

**Acceptance Criteria:**  
- No use of LLM or AI here – all numbers are computed from the database.  
- Write docstrings for each function explaining inputs/outputs.  
- Create unit tests comparing these functions against known SQL results or test fixtures.
- Example: `get_sales_metrics()` should return exact revenue matching a manual SUM query.

```text
Implement PHASE 5: Core Business Analytics Engine

- Create services in backend/app/services/:
    - analytics_service.py (optional coordinator)
    - sales_service.py
    - customer_service.py
    - product_service.py
- Sales metrics:
    - `get_sales_metrics(start_date, end_date)`: returns {revenue, orders, aov}.
    - `get_monthly_revenue(start_date, end_date)`: list of {month, revenue}.
    - `get_revenue_by_category(start_date, end_date)`: {category: revenue}.
    - `get_top_products(limit)`: top N products by revenue.
- Customer metrics:
    - `get_customer_metrics(start_date, end_date)`: {total_customers, new_customers, repeat_customers, inactive_customers}.
    - `get_top_customers(limit)`: top N customers by revenue.
- Product metrics:
    - `get_low_performing_products(limit)`: bottom N products by revenue (or unit sales).
- Use SQLAlchemy ORM or Core queries. Ensure numeric precision with Decimal.
- Use `func.sum()`, `func.count()` etc. in queries.
- Handle missing data: if no orders, metrics = 0.
- Tests:
    - Use pytest with controlled data to verify each metric.
    - Include tests for revenue calculation against a direct SQL SUM.
- Documentation:
    - Clearly mention how refunds/cancellations are excluded (e.g., `status != 'cancelled'` in filters).
    - Document inactive threshold (90 days default).
```

### Phase 6 – Analytics Verification Tests  
**Objective:** Validate that the analytics functions are correct and robust.  

**Tasks:**  
- Develop deterministic test cases with known outputs. Use small in-memory databases or test database.  
- Test each metric function thoroughly:
  - Total revenue, order count, AOV (including division-by-zero).  
  - Monthly aggregation (correct grouping by month).  
  - Category/product revenue splits.  
  - New/repeat/inactive customer logic (simulate various signup and order dates).  
  - Top-N queries return correct ordering and slicing.  
- Edge cases: empty dataset (should return zeros/empty lists), invalid date ranges (handle or error), all orders cancelled (revenue=0).  
- Use raw SQL queries (or a separate independent calculation) in tests to verify results.  
- Ensure 100% coverage of important logic.  

**Acceptance Criteria:**  
- All analytics functions have corresponding pytest cases.  
- Tests fail if logic is wrong (no sneaky float rounding errors, use Decimal and int where appropriate).  
- Demonstrate one complex scenario where revenue declines or spikes and check calculations.

```text
Implement PHASE 6: Analytics Verification

- Create pytest fixtures for synthetic data scenarios (e.g., 5 customers, 10 orders).
- Tests for `get_sales_metrics`:
    - Compute revenue and order count manually and compare.
- Tests for `get_monthly_revenue`:
    - Ensure correct revenue per month is returned.
- Tests for `get_revenue_by_category`:
    - Compare sums per category.
- Tests for `get_top_products` and `get_low_performing_products`.
- Tests for customer metrics:
    - Example: 5 customers, 3 with repeat orders, 1 new in range, 1 inactive. Verify outputs.
- Include a test for cancelled order:
    - Insert an order with status 'cancelled'; verify it is excluded from revenue and order count.
- Run `pytest` and fix any discrepancies found.
```

### Phase 7 – FastAPI Backend APIs  
**Objective:** Expose the analytics via a RESTful API.  

**Tasks:**  
- Initialize a FastAPI app in `backend/app/main.py`.  
- Create API routers in `backend/app/api/`: `health.py`, `dashboard.py`, `sales.py`, `products.py`, `customers.py`, `chat.py`.  
- Define Pydantic schemas in `backend/app/schemas/` for inputs and outputs.  
- Required endpoints:  
  - `GET /health` – returns status.  
  - `GET /dashboard` – returns KPI summary (total revenue, orders, customers, AOV for a default period).  
  - `GET /sales/metrics?start=&end=` – detailed sales metrics.  
  - `GET /sales/monthly?start=&end=` – monthly revenue.  
  - `GET /sales/categories?start=&end=` – revenue by category.  
  - `GET /products/top?limit=` – top products.  
  - `GET /customers/metrics?start=&end=` – customer metrics.  
  - `GET /customers/top?limit=` – top customers.  
  - `POST /chat` – user question (to LLM agent).  
  - `POST /charts` – request a chart by providing data or specification.  

- Use dependency injection for DB session. Return validated models.  
- Add CORS middleware for the React app origin.  
- Use proper HTTP status codes and error responses.  

**Acceptance Criteria:**  
- Each API endpoint calls the corresponding service function and returns real data.  
- Use FastAPI TestClient for testing each route (e.g. a get to `/sales/metrics` returns the correct JSON with a sample DB).  
- Schema validation should reject invalid inputs.  

```text
Implement PHASE 7: FastAPI Backend APIs

- Set up main FastAPI app:
    - Include `app.include_router(...)` for each API module.
    - Configure CORS (allow localhost frontend).
- In `backend/app/api/`, create:
    - health.py: `GET /health` returns {"status": "ok"}.
    - sales.py: endpoints for /sales/metrics, /sales/monthly, /sales/categories.
    - products.py: /products/top.
    - customers.py: /customers/metrics, /customers/top.
    - dashboard.py: aggregates multiple metrics.
    - chat.py: `/api/chat` for AI questions.
- In `backend/app/schemas/`, define Pydantic models for request/response:
    - e.g. SalesMetricsResponse, CustomerMetricsResponse, ChartRequest, ChatRequest, ChatResponse.
- Each route should:
    - Parse query parameters (dates, limits).
    - Call the corresponding service function.
    - Return JSON via Pydantic model.
- Error handling:
    - Return 400 for validation errors, 500 for server errors.
- Testing:
    - Use FastAPI TestClient (as in ) to simulate API calls.
    - Example: test `/sales/metrics` returns expected JSON keys and values.
- Performance:
    - Ensure that heavy queries (e.g. monthly aggregation) are handled efficiently (use indexes).
```

### Phase 8 – Configuration, Logging, and Security  
**Objective:** Harden the backend and improve maintainability.  

**Tasks:**  
- Centralize settings using Pydantic `BaseSettings` (e.g. in `app/config.py`), loading from environment.  
- Implement structured logging (e.g. Python `logging` with timestamps and log levels).  
- Add correlation/request IDs if needed (for traceability).  
- Set timeouts for DB queries and OpenAI API calls (via HTTPX/OpenAI config).  
- Use FastAPI exception handlers: raise domain errors in services and catch them to return HTTP errors (per ).  
- Implement input validation: e.g. date range sanity (start ≤ end), limits (e.g. max 100).  
- Rate limiting (optional) or ensure idempotency of POST requests.  
- Ensure database user has read-only privileges for analytics (do not use superuser!).  
- Review dependencies for security (no open re-directions, no OS command execution).  
- Ensure the API key and secrets are only in environment, not logged or in code.  

**Acceptance Criteria:**  
- Secrets (OpenAI key, DB URL) are not in source (check with `env.example`).  
- Invalid requests produce clear error messages (consistent JSON).  
- Add unit tests for exception cases (e.g. invalid date => HTTP 400).  
- Document security measures in README or docs.

```text
Implement PHASE 8: Configuration, Logging, and Security

- Use Pydantic settings (e.g. class `Settings(BaseSettings)`) for all config (openai_key, db_url, timeouts).
- Logging:
    - Configure a logger with JSON or plain format.
    - Log key actions (e.g. tool execution, ingestion summary).
- Error handling:
    - Define custom exceptions (e.g. `DataNotFound`, `InvalidQuery`).
    - Add `@app.exception_handler` for them to return JSON error (per ).
- Validate inputs:
    - If start_date > end_date, return 400.
    - If limit > allowed (e.g. 50), clamp or error.
- Security:
    - Remove or disable the interactive Swagger UI if needed for production.
    - Ensure all SQLAlchemy queries use parameters.
- Tests:
    - Simulate missing/invalid environment variable (should error).
    - Mock OpenAI to force a timeout and check handling.
    - Test for invalid endpoint usage and expect JSON error.
```

### Phase 9 – OpenAI LLM Integration  
**Objective:** Add the LLM layer to interpret questions.  

**Tasks:**  
- Install and configure OpenAI Python SDK.  
- Create `backend/app/llm/` module with:  
  - `client.py`: wraps OpenAI API calls (includes retries and timeouts).  
  - `prompts.py`: define system prompts and few-shot examples for the business domain. E.g. instruct the model to use tools, not to hallucinate.  
  - `schemas.py`: Pydantic models for LLM function responses and chat format.  
  - `service.py`: a function that takes user question, calls the LLM, and returns a parsed response (tool call request or final answer).  

- System Prompt example: "You are a business intelligence assistant. Use the provided functions to fetch real data. Never invent facts or numbers. If a question is out of scope, say so."  
- Use OpenAI function-calling: Define JSON schema for allowed tools (see next phase).  
- Handle errors: missing OpenAI key, rate limit, etc.  

**Acceptance Criteria:**  
- LLM client can be called without errors (test with a simple prompt).  
- System prompt is tested to ensure it instructs correctly (mock response).  
- Validate that the LLM output schema matches expectation (e.g. `{ "name": "get_sales_metrics", "arguments": {...} }`).  
- Add unit tests by mocking OpenAI responses to simulate function calls.  

```text
Implement PHASE 9: OpenAI LLM Integration

- Set up OpenAI client (backend/app/llm/client.py):
    - Load OPENAI_API_KEY from env.
    - Configure model (e.g. gpt-4) and timeouts.
    - Provide a function `call_llm(messages, functions=None)` that returns parsed JSON.
    - Handle common errors (invalid auth, rate limit) and raise descriptive exceptions.
- In prompts.py:
    - Define a strong system prompt: e.g. “You are InsightIQ AI, an analyst. You must use the approved tools for analytics. Do not guess; rely only on real data from tools.”
    - Include a couple of examples (Q→structured answer).
- In schemas.py:
    - Define models for possible function calls (name/arguments) and final answers.
- In service.py:
    - Implement a function `ask_llm(question: str)`:
        1. Send the system prompt + user question to OpenAI.
        2. Receive the model output (which may request a function).
        3. Return the content or parsed function name/arguments.
- Testing:
    - Use pytest with monkeypatch to simulate OpenAI returning a JSON with a function call.
    - Verify that our service passes the correct prompt and handles the function response.
```

### Phase 10 – Controlled Analytics Tool Calling  
**Objective:** Define the approved “tools” that the AI agent can invoke (these call our analytics functions).  

**Tasks:**  
- Create `backend/app/tools/registry.py` to map tool names to functions.  
- For each analytics function from Phase 5, create a corresponding tool handler, e.g. in `sales_tools.py`, `customer_tools.py`, `product_tools.py`:  
  - Define the function schema (Pydantic) for inputs (dates, limits).  
  - The tool function should parse inputs, call the analytics service, and return JSONable results.  
- Include a generic `generate_chart` tool that takes chart type and data to produce a chart (data only, actual drawing on frontend).  
- In registry, list each tool with: `{"name": "...", "description": "..."}`, and link to the handler function.  
- Validate arguments: use Pydantic models to enforce date formats and limit bounds.  
- Ensure that unknown tools or invalid args result in a clear error (caught by agent).  

**Acceptance Criteria:**  
- The LLM (via function-calling) can invoke each tool and get real data.  
- Tools enforce input validation and return structured output.  
- Examples:
  - If LLM returns name=`get_sales_metrics`, arguments=`{"start_date": "2023-01-01", "end_date": "2023-01-31"}`, our code calls sales_service and returns `{"revenue":..., "orders":..., "aov":...}`.  
- Write tests: mock LLM calling an approved tool with args, verify correct output or error.  

```text
Implement PHASE 10: Controlled Analytics Tool Calling

- Create backend/app/tools/:
    - registry.py: keeps a dict of {tool_name: ToolFunction}.
    - sales_tools.py, customer_tools.py, product_tools.py, chart_tools.py.
    - In each, define Pydantic models for inputs. For example, a SalesMetricsInput with start_date and end_date.
    - Each tool function:
        - Validates its arguments.
        - Calls the corresponding service (e.g. sales_service.get_sales_metrics).
        - Returns a dict (or Pydantic schema) with results.
- Example tool entry:
    ```
    {
      "name": "get_sales_metrics",
      "description": "Returns total revenue, orders, and AOV for a given date range.",
      "parameters": { ... JSON schema for args ... }
    }
    ```
- Register tools:
    - In registry.py, register each tool by name.
    - The LLM will only be allowed to call these.
- Generate Chart tool:
    - E.g. name: `generate_chart`, inputs: type (e.g. "line"), data array, x_key, y_key.
    - Returns a chart specification object.
- Tests:
    - Test valid input => expected data.
    - Test invalid date format => error.
    - Test unknown tool request (should be handled by agent).
```

### Phase 11 – LangGraph Agent Workflow  
 The architectural diagram above visualizes an autonomous AI system built from modular components. Each cube represents an agent or tool, mirroring how LangGraph implements multi-agent workflows by connecting specialized agents in a graph. This graph-based design allows us to coordinate multiple LLM-powered agents that collaborate step-by-step in a controlled manner.  

**Objective:** Implement the LLM-driven agent using LangGraph to process questions and invoke tools.  

**Tasks:**  
- Use LangGraph to build the agent workflow in `backend/app/agents/`. Key files: `graph.py`, `nodes.py`, `state.py`, `prompts.py`.  
- Define states (question, tool selection, execution, answer).  
- Nodes:  
  - **Question understanding:** Identify intent and required data.  
  - **Tool selector:** Choose which approved tool(s) to call.  
  - **Tool executor:** Actually invoke the Python function and get results.  
  - **Result validator:** Check if tool results are valid (e.g., non-empty, no errors).  
  - **Answer generator:** Format the final answer using the LLM (with factual data).  
  - **Error handler:** For unsupported queries or failures.  
- Configure the agent to allow multiple sequential tool calls if needed (e.g. first get sales metrics, then additional details).  
- Ensure the agent stops after a “final answer” node or on max iterations.  
- Use typed state and messages in LangGraph to pass data between nodes.  
- Important: The LLM should not generate SQL; it should only follow edges to approved tool nodes.  

**Acceptance Criteria:**  
- A natural-language question flows through the graph and returns a structured answer.  
- Use pytest to simulate the graph:
  - Provide a question, mock tool outputs, and verify the path.
  - Test an unsupported question (e.g. “What is the weather?”) returns a polite rejection.  
- Include execution tracing to log which tools were called.  

```text
Implement PHASE 11: LangGraph AI Analyst

- In backend/app/agents/, create:
    - state.py: define the LangGraph State (with fields like question, tool_name, tool_args, tool_result, answer).
    - nodes.py: define Node functions (e.g. understand_question, select_tool, call_tool, validate_result, generate_answer).
    - graph.py: assemble the LangGraph workflow linking these nodes.
    - prompts.py: any specialized prompts for agent (could reuse system prompt from Phase 9).
- Graph flow (simplified):
    Start -> UnderstandQuestion -> SelectTool -> CallTool -> ValidateResult -> (if more info needed, loop back to SelectTool) -> GenerateAnswer -> End
- Selection logic:
    - Match intent to tool (using LLM or rule).
    - If multiple steps needed (e.g. revenue drop analysis), allow looping.
- Validation:
    - If a tool returns no data, route to an explanation node (e.g. “Data not available”).
- Execution:
    - Each node returns updated state to LangGraph. Use state to accumulate context.
- Tests:
    - Unit test for each node function.
    - Integration test for full graph:
        * e.g. Input: "What is total revenue?" 
        * Graph should call get_sales_metrics, then GenerateAnswer with result.
    - Test error flows (no tool found, LLM returns unknown tool).
```

### Phase 12 – Multi-Step Revenue Decline Investigation  
**Objective:** Implement the complex scenario “Why did revenue decline last month?” as a multi-agent workflow.  

**Tasks:**  
- Create a specialized sub-graph or node for revenue-decline analysis in `agents/investigations/revenue_decline.py`.  
- Steps:  
  1. Determine current (e.g. last month) and previous period.  
  2. Use sales tools: get revenue and orders for both periods.  
  3. Compute changes and percentage.  
  4. If a decline is detected, analyze causes:
     - Compare order count vs AOV.  
     - Check repeat vs new customers change (`get_customer_metrics`).  
     - Identify top categories and products contributing to change (`get_revenue_by_category`, `get_top_products`).  
  5. Collate findings: which factor had biggest impact (e.g. fewer orders, or category drop).  
  6. Generate a factual explanation citing numbers.  
- Use LangGraph to orchestrate multiple tool calls and aggregate results.  
- The final answer should include actual figures and percentage changes, not vague speculation.  

**Acceptance Criteria:**  
- The agent can answer “Why did revenue decline last month?” with a multi-step analysis.  
- Example (using test data): “Revenue dropped 15% from $100k to $85k. Orders fell by 20%, but AOV was steady. The largest contributors were X category (–$Y) and fewer repeat customers.”  
- Include tests with a known dataset where revenue decline analysis is verifiable.  

```text
Implement PHASE 12: Multi-Step Revenue Decline Investigation

- In backend/app/agents/investigations/, create revenue_decline.py.
- This graph should:
    1. Identify date ranges (e.g. current vs previous month).
    2. Call `get_sales_metrics` for both periods.
    3. Compute differences and percentage.
    4. If decline, do:
       - `get_monthly_revenue` for both (for trend).
       - `get_customer_metrics` for both.
       - `get_revenue_by_category` for both periods.
    5. Summarize:
       - "Revenue changed by X%. Orders changed by Y%. Repeat customers changed by Z%. The largest decline was in category A ($Δ)."
- Ensure every number in explanation comes from a tool result.
- Tests:
    - Create a mini-dataset where last month revenue is lower (e.g. $100→$80).
    - Assert the output explanation matches the calculated differences.
    - Test edge case: no previous period data (e.g. only one month of data) yields a graceful answer.
```

### Phase 13 – Evidence-Backed Insights & Anomaly Detection  
**Objective:** Automatically generate concise business insights and detect anomalies.  

**Tasks:**  
- Implement an `anomaly_service.py` in `app/services/`:
  - Analyze monthly revenue changes, category shifts, customer trends.
  - Detect anomalies by simple rules (e.g., a change > 2 standard deviations or a percentage threshold).  
- Implement `insight_service.py`:
  - Generate human-readable insights, e.g. “Anomaly: Revenue spike of 50% in May” or “Orders increased by 30% from Apr to May”.  
  - Provide supporting metrics for each insight (values and comparisons).  
- These insights will be fetched by the dashboard (e.g. `GET /insights`).  
- Ensure insights are data-driven (the text mentions actual numbers and context).  

**Acceptance Criteria:**  
- The system flags any unusual changes and outputs an insight object:  
  ```json
  { "title": "Revenue Spike Detected",
    "description": "Revenue jumped from $10k to $15k (+50%) last month.",
    "evidence": { "previous": 10000, "current": 15000 }
  }
  ```  
- Use anomaly detection best practices: identify outliers in time series.  
- Tests:
  - With a dataset containing a big outlier, confirm an insight is generated.
  - If no anomalies, return empty list or a note “No significant anomalies detected”.

```text
Implement PHASE 13: AI Insights and Anomaly Detection

- In backend/app/services/anomaly_service.py:
    - Function to scan recent revenue data for spikes/dips.
    - Use statistical thresholds or fixed % rules.
- In insight_service.py:
    - Functions to compile insights: e.g. top metrics changes, anomalies.
    - Each insight has title, description, metric values, and any comparative stat.
- API:
    - Expose `GET /api/insights` returning JSON list of insights.
- Anomaly example:
    - If May revenue = $150k and April = $100k, detect +50% increase.
    - Compare against historical std dev if available.
- Testing:
    - Synthetic data: one month has 2x revenue of others; ensure an insight is returned.
- Documentation:
    - Explain in README how anomalies are defined (based on IBM's definition).
```

### Phase 14 – Dynamic Chart Generation  
**Objective:** Let the AI agent return chart specifications that the frontend can render.  

**Tasks:**  
- Define a chart specification schema (JSON) for Recharts (e.g., `{ chart_type, title, x_key, y_key, data: [...] }`).  
- Update the agent/tools so it can handle chart requests:
  - E.g. if the user asks “Chart monthly revenue”, the agent calls `get_monthly_revenue`, then produces a response like:  
    ```json
    {
      "chart": {
         "type": "line",
         "title": "Monthly Revenue",
         "x_key": "month",
         "y_key": "revenue",
         "data": [{"month": "2023-01", "revenue": 10000}, ...]
      }
    }
    ```  
- Backend should only send JSON data; the React frontend will take care of actual rendering with Recharts.  
- Handle requests like “Show top 5 products by revenue” (bar chart), “Compare category revenue across months”, etc.  
- Validate chart requests to prevent invalid graphs (e.g. too many series, empty data).  

**Acceptance Criteria:**  
- A conversation example:  
  User: “Show monthly revenue as a chart.”  
  Agent: calls `get_monthly_revenue`, returns a valid chart schema (e.g. `{"chart_type":"line",...,"data":[...]}`).  
- React frontend uses this schema to render a chart (test manually).  
- Tests:
  - Backend: Given fixed data and a chart request, verify the returned JSON matches the schema.
  - Frontend: Component test that given a sample chart spec, Recharts renders something (basic snapshot).
  
```text
Implement PHASE 14: Dynamic Chart Generation

- Define a chart output model in Pydantic (backend/app/schemas/charts.py):
    - Fields: chart_type (line/bar/pie), title, x_key, y_key, data (list of records).
- Backend:
    - In tools/chart_tools.py, create functions like `generate_line_chart(data, x_key, y_key)`.
    - Alternatively, the agent can directly format the JSON without a separate tool if simpler.
- Frontend:
    - Create a React component `<DynamicChart>` that:
        - Accepts the chart JSON from API.
        - Switches on `chart_type` to render a Recharts LineChart, BarChart, etc.
        - Binds `data`, and maps x_key/y_key to axes/values.
    - Example usage in chat interface: if agent response contains a "chart", render it.
- Validation:
    - Backend should check that data is not empty before sending.
    - Limit max data points (to avoid huge charts).
- Tests:
    - Backend: Simulate an agent calling `generate_chart` and verify JSON.
    - Frontend: Provide a sample line-chart JSON and ensure the component renders axes and lines (basic test or screenshot).
```

### Phase 15 – Frontend Foundation (React)  
**Objective:** Set up the frontend project structure and theming.  

**Tasks:**  
- Initialize a React app using Vite in `frontend/`. Install dependencies: `react`, `react-dom`, `tailwindcss`, `axios` (for API calls), `@tanstack/react-query` (optional), `lucide-react` (icons), `react-router` (if multiple pages).  
- Configure Tailwind CSS.  
- Create common layout components: header, sidebar (with navigation items: Dashboard, AI Analyst), footer.  
- Set up a `services/api.js` or similar to handle HTTP requests to the backend. Base URL from environment (e.g. `.env.development`).  
- Create loading and error components (spinners, error alerts).  
- Ensure the app builds and runs with `npm run dev`.  

**Acceptance Criteria:**  
- The React app starts without errors.  
- Styles (Tailwind) are applied correctly to basic components.  
- Can fetch from the backend health endpoint (test connectivity).  
- Include a simple Axios test or React Query fetch call to `/api/health` on load.  

```text
Implement PHASE 15: React Frontend Foundation

- In frontend/, run `npm create vite@latest` (template: react).
- Install Tailwind and configure (postcss.config.js, tailwind.config.js).
- Install Recharts, axios, lucide-react.
- Create src/components/ (e.g., Sidebar.jsx, Header.jsx, DashboardCard.jsx, LoadingSpinner.jsx).
- Create src/services/api.js:
    ```js
    import axios from 'axios';
    const api = axios.create({ baseURL: import.meta.env.VITE_API_URL });
    export default api;
    ```
- Create a simple page Layout:
    - Sidebar with links (Dashboard, AI Chat).
    - Top nav with title/logo.
    - Content area where components render.
- Add a route for "/" that hits `GET /api/health` using useEffect/axios and displays a green “Up” or red “Down”.
- Ensure mobile responsiveness (Tailwind grids or flex).
- No backend mocking here; use a real local run or mock server for initial connectivity test.
- Do not implement real analytics UI yet.
```

### Phase 16 – Business Intelligence Dashboard (UI)  
 Modern BI dashboards display KPIs and charts in a clean layout. The example above shows KPI cards and trend charts. InsightIQ’s dashboard will have:  

- **KPI Cards** for Total Revenue, Total Orders, Total Customers, Average Order Value.  
- **Charts:**  
  - **Monthly Revenue:** Line chart showing revenue over time.  
  - **Revenue by Category:** Bar or pie chart.  
  - **Top Products:** Bar chart of top 5 products by revenue.  
  - **Customer Growth:** Bar chart of new vs repeat customers per month.  

- A date range filter that updates all metrics.  
- Loading skeletons for data, and “No data” states if empty.  
- Responsive design (cards stack on mobile).  

**Tasks:**  
- Build Dashboard page (`frontend/src/pages/Dashboard.jsx`).  
- Fetch required data from the FastAPI (`/api/dashboard`, `/api/sales/monthly`, etc.) using axios or React Query.  
- Map data to components:
  - `<MetricCard title="Revenue" value={...} />` etc.  
  - `<Recharts.LineChart data={monthlyRevenue} />`, etc.  
- Format currencies and dates.  
- Add date pickers or dropdown for filter (optional if time).  

**Acceptance Criteria:**  
- The dashboard loads real data from backend. (Manual check)  
- KPI values and charts match what backend returns.  
- Use React Testing Library to write a component test:
  - Mock API and verify that a metric card displays correct text.  
- The UI should look polished and professional (basic styling is fine, avoid clutter).

```text
Implement PHASE 16: Business Intelligence Dashboard

- Create src/pages/Dashboard.jsx.
- Inside, create 4 cards (Revenue, Orders, Customers, AOV):
    - Use a grid or flex layout (e.g. Tailwind `grid grid-cols-4 gap-4`).
    - Fetch from `/api/dashboard` (or individual endpoints).
    - Display numbers (format with Intl.NumberFormat for currency).
- Charts:
    - Monthly Revenue: Use <LineChart> from Recharts.
    - Category Revenue: <BarChart> or <PieChart>.
    - Top Products: <BarChart> horizontal.
    - Customer Trend: <LineChart> for new/repeat (or separate small charts).
- Date Range:
    - Add two <input type="date"> fields.
    - On change, refetch all data endpoints.
- Loading/Error:
    - Show skeleton or spinner while waiting.
    - If error from API, show message.
- Tests:
    - Mock axios responses in a Jest test.
    - Render Dashboard and check if metric values appear.
```

### Phase 17 – AI Analyst Chat Interface  
**Objective:** Build the chat UI where users can ask questions to the AI agent.  

**Tasks:**  
- Create a Chat page/component with:  
  - A text input for questions.  
  - A submit button.  
  - Conversation history area (list of messages).  
  - Suggested questions (button chips) to help users.  
- When the user asks a question:  
  1. Display user message.  
  2. Show a loading indicator.  
  3. Call `POST /api/chat` with the question.  
  4. Stream or receive the agent’s answer (which may include text and/or charts).  
- Render the AI’s answer:
  - Plain text answers in a chat bubble.  
  - If a chart schema is returned (see Phase 14), render it as a dynamic chart component in the chat.  
  - If insight bullets are returned, render them as a list.  
- Show tool execution info:
  - (Optional) For each answer, show a small debug panel: e.g. “Tool used: get_sales_metrics (Revenue)”. This is for your demo’s clarity.  
- Handle user follow-ups: keep the conversation context (the stateful agent can consider previous Q&A).  

**Acceptance Criteria:**  
- Chat interface is styled professionally (use Lucide icons for send button).  
- Asking "What is our total revenue?" returns the correct number from backend in a chat bubble.  
- Asking "Show me a chart of monthly revenue." displays a chart.  
- Suggestion buttons work (e.g. user clicks “Who are top customers?”).  
- Tests:
  - Unit test the Chat component: simulate user input and mock /api/chat to return a message, assert it appears.
  - Test chart rendering logic given sample JSON.  

```text
Implement PHASE 17: AI Analyst Chat Interface

- Create src/pages/Chat.jsx.
- Layout:
    - Left: (optional) suggestions or tips.
    - Center: Chat window (vertical scroll).
    - Bottom: Text input + Send button.
- State:
    - Keep an array of messages: {sender: 'user'|'ai', content: string or element}.
    - When user submits, push message and call API.
- Fetching:
    - POST question to `/api/chat` (use axios).
    - Await response: can be JSON with {answer: "...", chart: {...}}.
- Rendering:
    - For user: simple text box.
    - For AI:
       * If `answer` key: show text.
       * If `chart` key: render <DynamicChart>.
       * If `insights` key: render as bullet list.
       * If tool info: optionally display it (debug).
- Loading:
    - Disable input or show spinner while waiting.
- Error handling:
    - If API fails, show error bubble.
- Tests:
    - Use RTL: type a question, mock axios to return a chat response, check it in DOM.
    - Provide sample `chart` JSON to Chat component and assert a canvas or chart elements appear.
```

### Phase 18 – End-to-End Integration and Enhancements  
**Objective:** Connect all pieces and add any high-value enhancements.  

**Tasks:**  
- Run the full application end-to-end: data → DB → backend → frontend.  
- Verify user stories:
  - Dashboard displays correct values from data.
  - Chat answers questions accurately (test several queries).  
- Implement optional enhancements if core is solid:  
  - **Evidence Panel:** Next to each AI answer, show the data range, tool name, and key figures used. (Helps trust.)  
  - **Follow-up Questions:** Maintain conversation context so that referencing previous data works.  
  - **CSV/Report Export:** Add a button on dashboard to download current view data as CSV.  
  - **Anomaly Highlights:** Mark anomalies on charts or list them.  
- Ensure consistency:
  - All date filters apply everywhere.
  - The execution history (for demonstration) is logged.  

**Acceptance Criteria:**  
- The entire flow works in one session (start with a fresh DB).  
- Demonstrate a user scenario:
  1. Open app, see dashboard.  
  2. Ask a revenue question in chat, see correct answer.  
  3. Ask “Why did revenue decline?”, see the multi-step answer.  
  4. Ask “Show me monthly revenue chart,” see chart.
- Integration tests:
  - (Optional) Use a tool like Playwright or Cypress to automate a basic flow.  
- Any enhancements should not break core features.

```text
Implement PHASE 18: Full System Integration

- Deploy locally via Docker (optional at this step, or manual).
- Manually test:
    * Dashboard loads with data.
    * Chat queries produce correct output.
    * Follow-up context works (e.g. "And last year?").
- Add features:
    - Evidence panel in chat (small font metadata).
    - If time: Export CSV (frontend: fetch /api/data and use FileSaver).
- Ensure:
    - No hardcoded values anywhere.
    - All components use real APIs.
    - Show error handling: try invalid input and observe UI feedback.
- Tests:
    - Write an end-to-end test (if feasible).
- Document: Note any optional features partially done.
```

### Phase 19 – Testing and Reliability  
**Objective:** Ensure the application is robust, reliable, and well-tested.  

**Tasks:**  
- Review all code for error handling and edge cases.  
- Write remaining tests:  
  - Backend: test DB session, each API endpoint (happy and error paths).  
  - Agents: test agent fallbacks.  
  - Performance: test with large dataset (optional).  
  - Frontend: test components (cards, charts, chat bubble).  
- Security audit:  
  - Confirm no secrets in repo.  
  - No raw SQL exposures or injections.  
- Prepare documentation of known limitations or assumptions (e.g. “Current app uses GPT-4, which requires API key”, “Only English supported”, etc.) in `docs/known_limitations.md`.  
- Write test report in `docs/testing_report.md` summarizing test coverage and results.  

**Acceptance Criteria:**  
- pytest and frontend tests all pass with coverage.  
- Known issues (if any) are documented, not left silent.  
- The codebase is clean (no PyLint/flake8 warnings if possible).  

```text
Implement PHASE 19: Complete Quality Assurance

- Backend testing:
    * Unit tests (sales, customer, product services).
    * API tests with TestClient (both success and failure cases).
    * Agent tests (simulate LLM/tool combos).
    * Chart schema validation tests.
- Frontend testing:
    * Component tests for DashboardCard, DynamicChart, Chat.
    * Error state tests (e.g., show error message on API failure).
- Integration tests:
    * If using Playwright/Cypress, test the main user flows.
- Security:
    * Check .gitignore for secrets.
    * Verify no XSS or SQL injection.
- Documentation:
    * docs/testing_report.md: list tests run and their outcomes.
    * docs/known_limitations.md: e.g. model latency, data size limits, unit-testing LLMs, etc.
- Ensure you fix any critical failures. Do not mark phase done if tests fail.
```

### Phase 20 – Docker, Documentation, and Submission  
**Objective:** Containerize, document, and finalize the deliverables.  

**Tasks:**  
- Write a `Dockerfile` for the backend and one for the frontend (or a single multi-service with Docker Compose).  
- Create `docker-compose.yml` to run PostgreSQL, backend, frontend.  
- Ensure environment variables are passed correctly.  
- Update `README.md` with:
  - Project summary and features.  
  - Architecture diagram (inline or in docs).  
  - Setup instructions (both local and Docker).  
  - Explanation of each major component and phase.  
  - Testing instructions (`pytest`, `npm test`).  
  - How to run and access the app.  
  - Known limitations summary.  
- Draft a concise demo plan (can reuse the script below).  
- (Optional) Publish on GitHub (private or public as allowed) with a meaningful repo name.  
- Prepare a short video demo following the script.  

**Acceptance Criteria:**  
- Running `docker-compose up` brings up the entire app (backend on port 8000, frontend on 3000).  
- README and docs are complete and clear.  
- Tests run successfully in CI (or via command).  
- The repository is ready for submission (no broken links, images visible, README is entrypoint).  

```text
Implement PHASE 20: Final Packaging and Documentation

- Dockerization:
    * Write a Dockerfile for backend (start Uvicorn, copy code, set env).
    * Dockerfile for frontend (build with `npm run build`, serve via static server or nginx).
    * docker-compose.yml linking: 
        - db (Postgres),
        - backend (depends on db),
        - frontend (depends on backend).
    * Include volumes for db data.
- Documentation:
    * Complete README.md with:
       - Overview, features, tech stack.
       - Setup (local vs Docker).
       - Environment variables.
       - API endpoints summary.
       - How to run tests.
    * docs/architecture.md (if not done): include a diagram or ASCII art.
    * docs/data_dictionary.md: describe each DB field.
    * docs/testing_report.md: summarizing test results.
    * docs/known_limitations.md.
- Demo Video (optional but recommended):
    * Steps to record: use screen capture tool.
    * Follow the Demo Script below.
    * Ensure clarity and brevity (~4 minutes).
- Final checks:
    * Secrets are not committed.
    * Sample data (if any) is included.
    * README links to the video or instructions for it.
    * GitHub repo is up-to-date.
```

### Final Submission Checklist  
Use this checklist to ensure all requirements are met before submission:

- **Data & Ingestion:** Raw data ingestion pipeline, cleaning of missing/duplicate, DB load.  
- **Analytics:** Revenue, orders, AOV, monthly revenue, category/product breakdown, customer metrics (new, repeat, inactive), top/low products.  
- **AI & Agents:** Natural-language querying, OpenAI integration, LangGraph workflow, grounded answers via tools, unsupported question handling.  
- **Advanced:** Multi-step revenue decline analysis, dynamic chart generation, anomaly insights.  
- **API & UI:** FastAPI endpoints, React dashboard (4 KPIs, 4 charts), AI chat interface (text and charts).  
- **Engineering:** Pydantic validation, error handling, logging, Docker setup.  
- **Testing:** Pytest and frontend tests, reporting passed/failed, test coverage.  
- **Docs:** README, architecture, data dictionary, testing report, known issues.  
- **Presentation:** Demo video covering dashboard, Q&A, charts, agent reasoning.  

## Demo Script (4–5 minutes)  
Use the steps below when recording the final demo:

- **0:00–0:30 – Introduction:**  
  Briefly introduce *InsightIQ AI* and the business problem (e-commerce analytics, dashboards, AI analyst).  

- **0:30–1:00 – Dashboard Overview:**  
  Show the dashboard page with KPI cards (Revenue, Orders, Customers, AOV).  
  Highlight charts (monthly revenue line chart, category bar chart, etc.).  
  Mention data source and real-time stats.  

- **1:00–1:40 – Natural-Language Q&A:**  
  Switch to the AI Chat page. Ask: “What is our total revenue?”  
  Show how the agent uses tools to fetch the actual revenue and answer it.  
  Ask another simple question, e.g. “Who are our top five products by revenue?” and display the answer and chart.  

- **1:40–2:15 – Multi-Step Analysis:**  
  Ask: “Why did revenue decline last month?”  
  Show the agent performing multi-step reasoning: invoking multiple tools.  
  Display the evidence (e.g. orders down 20%, certain categories contributing) in the answer.  

- **2:15–3:00 – Dynamic Charts:**  
  Ask: “Show monthly revenue as a chart.”  
  The agent should return a chart specification. Verify the chart appears.  
  Try another chart request, e.g. “Compare category revenue.”  

- **3:00–3:30 – Robustness:**  
  Ask an unsupported question, e.g. “What is the weather today?”  
  Show the system’s safe error handling (“Sorry, I cannot do that”).  
  Demonstrate invalid input handling if time (e.g. invalid date).  

- **3:30–4:00 – Technical Wrap-up:**  
  Briefly display the project structure (optional, or mention GitHub).  
  Mention testing (`pytest`, frontend tests passed).  
  Conclude with main strengths: grounded results, end-to-end integration, professional UI.

---

This **implementation playbook** is intended to be used as a single-reference guide. Paste the global instructions at the start of the coding assistant (Antigravity) session, then run each phase in sequence using the provided prompts. Each phase should be verified before moving on.

{"cursor": 21, "loc": 52}