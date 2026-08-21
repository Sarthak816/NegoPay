# NegoPay Feature Tickets

This document contains individual, granular feature tickets for NegoPay. Each ticket is self-contained and designed to be implemented by an AI coding agent.

## DevOps

### KA-001: Project scaffold
- **Component**: DevOps
- **Priority**: P0
- **Dependencies**: None
- **Estimated Complexity**: S

**Description**

Initialize the base project structure for NegoPay. This includes creating the standard directory layout for the backend, frontend, and shared components, as well as setting up the Python virtual environment and dependency management.

**Technical Details**

- Create `backend/` and `frontend/` directories.
- In `backend/`, create `pyproject.toml` with dependencies: fastapi, uvicorn, razorpay, mcp, sqlite3, pydantic, langgraph.
- Create `requirements.txt` from pyproject.toml.
- Set up `.gitignore` for Python and Node.js.

**Acceptance Criteria**

- [ ] Repository has correct folder structure.
- [ ] `pyproject.toml` and `requirements.txt` exist with valid dependencies.
- [ ] Virtual environment can be created and dependencies install successfully.

---

### KA-008: Docker Compose setup
- **Component**: DevOps
- **Priority**: P1
- **Dependencies**: KA-001
- **Estimated Complexity**: M

**Description**

Create a Docker Compose configuration to easily spin up the entire application stack locally, including the backend, frontend, and persistent volumes for the database.

**Technical Details**

- Create `docker-compose.yml` in the project root.
- Define `backend` service building from `backend/Dockerfile`, exposing port 8000.
- Define `frontend` service building from `frontend/Dockerfile`, exposing port 3000.
- Define a volume for the SQLite database to persist data across restarts.

**Acceptance Criteria**

- [ ] `docker-compose up` starts both backend and frontend successfully.
- [ ] Backend API is accessible at `localhost:8000`.
- [ ] Database state persists after `docker-compose down` and `up`.

---

## Foundation

### KA-002: SQLite database setup
- **Component**: Foundation
- **Priority**: P0
- **Dependencies**: KA-001
- **Estimated Complexity**: M

**Description**

Set up the SQLite database schemas. We need tables to store product catalogs for multiple merchants, track orders and payments, store spending mandates, log audit events, and manage negotiation sessions.

**Technical Details**

- Create `backend/database.py` with SQLAlchemy or raw SQLite setup.
- Define tables: `merchants`, `products` (foreign key to merchants), `orders`, `payments`, `mandates`, `audit_events`, `negotiation_sessions`.
- Write an initialization script `init_db.py` that creates these tables if they don't exist.

**Acceptance Criteria**

- [ ] Running `init_db.py` creates a `NegoPay.db` file.
- [ ] All required tables are created with correct schemas and foreign keys.
- [ ] Database connection can be established without errors.

---

### KA-003: Product seed data
- **Component**: Foundation
- **Priority**: P0
- **Dependencies**: None
- **Estimated Complexity**: M

**Description**

Create realistic JSON seed data for the product catalog. This is essential for the AI buyer to have meaningful products to search and compare across multiple merchants.

**Technical Details**

- Create `backend/seed_products.json`.
- Define 3 merchants: TechMart, SoundStore, BookHaven.
- Add 50 products across 5 categories: Electronics, Audio, Books, Clothing, Sports.
- Each product needs: `id`, `merchant_id`, `name`, `description`, `price`, `currency` (INR), `stock_quantity`, `category`, `tags`.

**Acceptance Criteria**

- [ ] `seed_products.json` contains exactly 50 products.
- [ ] Products are distributed across 3 merchants and 5 categories.
- [ ] JSON is valid and follows the schema.

---

### KA-004: Database seeding script
- **Component**: Foundation
- **Priority**: P0
- **Dependencies**: KA-002, KA-003
- **Estimated Complexity**: S

**Description**

Write a script to load the seed data from the JSON file into the SQLite database. This script will be run during project setup to populate the initial state.

**Technical Details**

- Create `backend/seed_db.py`.
- Read `seed_products.json`.
- Insert merchants into the `merchants` table.
- Insert products into the `products` table.
- Handle conflicts (e.g., clear tables before seeding or use upsert).

**Acceptance Criteria**

- [ ] Running `seed_db.py` successfully populates the database.
- [ ] Data in SQLite matches the JSON file exactly.
- [ ] Script can be run multiple times safely (idempotent).

---

### KA-006: FastAPI server skeleton
- **Component**: Foundation
- **Priority**: P0
- **Dependencies**: KA-001
- **Estimated Complexity**: S

**Description**

Set up the core FastAPI application. This serves as the backend entry point, providing health checks, CORS configuration for the frontend, and global error handling.

**Technical Details**

- Create `backend/main.py`.
- Initialize FastAPI app with title and description.
- Add CORS middleware allowing all origins (for local dev).
- Add a `/health` endpoint returning `{"status": "ok"}`.
- Add global exception handlers that return standardized JSON error responses.

**Acceptance Criteria**

- [ ] Server starts successfully with `uvicorn main:app --reload`.
- [ ] `/health` endpoint returns 200 OK.
- [ ] CORS allows requests from localhost.

---

### KA-007: Configuration management
- **Component**: Foundation
- **Priority**: P0
- **Dependencies**: KA-001
- **Estimated Complexity**: S

**Description**

Implement configuration management using environment variables. This centralizes all settings like API keys, database URLs, and feature flags.

**Technical Details**

- Create `backend/config.py` using `pydantic-settings`.
- Define `Settings` class with fields: `DATABASE_URL`, `RZP_KEY_ID`, `RZP_KEY_SECRET`, `RZP_WEBHOOK_SECRET`, `LLM_API_KEY`.
- Create a `.env.template` file with dummy values.
- Ensure settings are loaded on application startup.

**Acceptance Criteria**

- [ ] Settings class validates environment variables correctly.
- [ ] `.env.template` is provided in the repository.
- [ ] Application fails to start if required variables are missing.

---

## Razorpay

### KA-005: Razorpay client wrapper
- **Component**: Razorpay
- **Priority**: P0
- **Dependencies**: KA-001
- **Estimated Complexity**: S

**Description**

Create a wrapper around the Razorpay Python SDK. This wrapper will encapsulate the initialization with test keys and provide helper methods for common operations like creating orders and capturing payments.

**Technical Details**

- Create `backend/razorpay_client.py`.
- Initialize `razorpay.Client(auth=(RZP_KEY_ID, RZP_KEY_SECRET))`.
- Implement methods: `create_order(amount, currency, receipt_id)`, `capture_payment(payment_id, amount)`, `verify_webhook_signature(body, signature, secret)`.
- Use Pydantic models for request/response typing.

**Acceptance Criteria**

- [ ] Wrapper can be imported and initialized successfully.
- [ ] Helper methods correctly map to Razorpay SDK calls.
- [ ] Authentication uses environment variables.

---

### KA-071: Razorpay payment capture flow
- **Component**: Razorpay
- **Priority**: P0
- **Dependencies**: KA-005, KA-014
- **Estimated Complexity**: L

**Description**

Implement the payment capture flow. Once an order is created and the buyer agrees to pay, simulate the payment capture via the Razorpay test API.

**Technical Details**

- Implement `capture_payment` endpoint in `main.py`.
- Receive `order_id` and `amount`.
- Call Razorpay API to simulate payment success (using test card/UPI data if necessary, or just rely on the API response).
- Update the `orders` table status to 'paid'.

**Acceptance Criteria**

- [ ] Successfully calls Razorpay payment API.
- [ ] Order status in database is updated to 'paid' upon success.
- [ ] Handles API errors gracefully.

---

## MCP Server

### KA-010: MCP server initialization
- **Component**: MCP Server
- **Priority**: P0
- **Dependencies**: KA-006
- **Estimated Complexity**: M

**Description**

Set up the Merchant MCP Server using the official Python MCP SDK. This server will expose the merchant's catalog and capabilities as tools to the AI Buyer Agent.

**Technical Details**

- Create `backend/mcp_server.py`.
- Initialize an MCP Server instance: `Server("merchant-mcp")`.
- Set up the transport layer (stdio or SSE depending on deployment architecture, recommend stdio for initial local agent integration).
- Add boilerplate for tool registration decorators.

**Acceptance Criteria**

- [ ] MCP server script runs without errors.
- [ ] Basic tool registration structure is in place.
- [ ] Server can communicate over stdio (responds to basic MCP initialization messages).

---

### KA-011: search_products tool
- **Component**: MCP Server
- **Priority**: P0
- **Dependencies**: KA-010, KA-002
- **Estimated Complexity**: M

**Description**

Implement the `search_products` MCP tool. This allows the buyer agent to search the catalog using semantic queries and filters.

**Technical Details**

- Register `@server.tool()` for `search_products`.
- Arguments: `query` (str), `max_price` (float, optional), `category` (str, optional).
- Implementation: Query the SQLite `products` table using `LIKE` for the query, and apply price/category filters if provided.
- Return a list of product dictionaries with basic details.

**Acceptance Criteria**

- [ ] Tool successfully queries the database and returns matching products.
- [ ] Filters (price, category) are applied correctly.
- [ ] Returns empty list if no matches found.

---

### KA-012: get_product_details tool
- **Component**: MCP Server
- **Priority**: P0
- **Dependencies**: KA-010, KA-002
- **Estimated Complexity**: S

**Description**

Implement the `get_product_details` MCP tool. This allows the buyer agent to retrieve full information about a specific product, including description and exact stock levels.

**Technical Details**

- Register `@server.tool()` for `get_product_details`.
- Arguments: `product_id` (str).
- Implementation: Fetch the specific product row from the `products` table. Return all fields.
- Raise an appropriate MCP error if the product doesn't exist.

**Acceptance Criteria**

- [ ] Returns complete product JSON for a valid ID.
- [ ] Returns clear error message if product ID is invalid.
- [ ] Stock quantity is accurately reported.

---

### KA-014: create_order tool
- **Component**: MCP Server
- **Priority**: P0
- **Dependencies**: KA-010, KA-005
- **Estimated Complexity**: L

**Description**

Implement the `create_order` MCP tool. This tool delegates to the Razorpay client to create an order on the merchant's behalf.

**Technical Details**

- Register `@server.tool()` for `create_order`.
- Arguments: `product_ids` (list[str]), `quantities` (list[int]), `idempotency_key` (str).
- Implementation: Calculate total amount, call `razorpay_client.create_order()`. Store order details in SQLite `orders` table.
- Return the Razorpay `order_id` and total amount.

**Acceptance Criteria**

- [ ] Creates a valid order in Razorpay (test mode).
- [ ] Saves order record to the local SQLite database.
- [ ] Uses idempotency key to prevent duplicate orders for the same request.

---

### KA-018: request_negotiation tool
- **Component**: MCP Server
- **Priority**: P1
- **Dependencies**: KA-010, KA-050
- **Estimated Complexity**: L

**Description**

Implement the `request_negotiation` MCP tool. This initiates a negotiation session between the Buyer Agent and the Merchant's Seller Agent.

**Technical Details**

- Register `@server.tool()` for `request_negotiation`.
- Arguments: `product_id` (str), `buyer_initial_offer` (float), `buyer_context` (str).
- Implementation: Create a new session in `negotiation_sessions` table. Trigger the Seller Agent to evaluate the offer and generate a response.
- Return the session ID and the Seller's initial counter-offer.

**Acceptance Criteria**

- [ ] Creates a new negotiation session record.
- [ ] Correctly routes the offer to the Seller Agent logic.
- [ ] Returns a structured response containing the session ID and seller's reply.

---

## Mandate

### KA-020: Mandate data model
- **Component**: Mandate
- **Priority**: P0
- **Dependencies**: KA-002
- **Estimated Complexity**: S

**Description**

Define the data structures for the Mandate System, which controls the deterministic spending rules for the Buyer Agent.

**Technical Details**

- Create `backend/models/mandate.py`.
- Define a Pydantic model `Mandate` with fields: `id`, `user_id`, `max_transaction_amount`, `daily_limit`, `allowed_categories` (list), `requires_approval_above`.
- Ensure mapping to the SQLite `mandates` table.

**Acceptance Criteria**

- [ ] Pydantic model correctly validates mandate data.
- [ ] Schema perfectly matches the SQLite table structure.

---

### KA-021: Per-transaction limit check
- **Component**: Mandate
- **Priority**: P0
- **Dependencies**: KA-020
- **Estimated Complexity**: S

**Description**

Implement the core logic to enforce per-transaction limits. Before any order is created, the system must verify the amount against this limit.

**Technical Details**

- Create `backend/services/mandate_service.py`.
- Implement `check_transaction_limit(mandate_id, amount)`.
- Fetch mandate, compare `amount` <= `max_transaction_amount`.
- Return a structured result: `{"allowed": bool, "reason": str}`.

**Acceptance Criteria**

- [ ] Returns allowed=True when amount is below limit.
- [ ] Returns allowed=False and a reason when amount exceeds limit.

---

### KA-022: Daily aggregate spend tracker
- **Component**: Mandate
- **Priority**: P0
- **Dependencies**: KA-020
- **Estimated Complexity**: M

**Description**

Implement tracking and enforcement for daily spending limits to ensure the Buyer Agent doesn't drain the account over multiple transactions in a single day.

**Technical Details**

- In `mandate_service.py`, implement `check_daily_limit(mandate_id, amount)`.
- Query the `orders` table to sum all successful transaction amounts for the given user today.
- Add the proposed `amount`. If total > `daily_limit`, return allowed=False.
- Return structured result.

**Acceptance Criteria**

- [ ] Correctly sums previous transactions for the current day.
- [ ] Blocks transactions that would push the total over the daily limit.
- [ ] Allows transactions within the daily limit.

---

## Buyer Agent

### KA-030: Buyer agent initialization
- **Component**: Buyer Agent
- **Priority**: P0
- **Dependencies**: KA-001
- **Estimated Complexity**: L

**Description**

Set up the core loop for the AI Buyer Agent. This agent receives natural language instructions and uses tools to execute the purchase.

**Technical Details**

- Create `backend/agents/buyer_agent.py`.
- Initialize LangGraph or a basic OpenAI/Anthropic function calling loop.
- Set up the state dictionary: `messages`, `current_intent`, `selected_products`, `mandate_status`.
- Create the agent execution entrypoint `run_buyer_agent(prompt, mandate_id)`.

**Acceptance Criteria**

- [ ] Agent can be invoked with a text prompt.
- [ ] Agent loop handles basic tool calls and returns a final response.
- [ ] Agent maintains state during execution.

---

### KA-031: Buyer agent system prompt
- **Component**: Buyer Agent
- **Priority**: P0
- **Dependencies**: KA-030
- **Estimated Complexity**: M

**Description**

Write the comprehensive system prompt that defines the Buyer Agent's persona, capabilities, strict adherence to mandates, and negotiation strategy.

**Technical Details**

- Define the prompt in `backend/agents/prompts.py`.
- Include sections: Role, Capabilities, Mandate Rules (NEVER bypass), Negotiation Guidelines (always try to get at least 5% off if price > 1000), Output Format.
- Inject the current active mandate details dynamically into the prompt.

**Acceptance Criteria**

- [ ] Prompt clearly defines the agent's constraints.
- [ ] Prompt explicitly instructs the agent to check mandates before purchasing.
- [ ] Agent follows the persona defined in the prompt.

---

### KA-035: Mandate integration in buyer agent
- **Component**: Buyer Agent
- **Priority**: P0
- **Dependencies**: KA-030, KA-021
- **Estimated Complexity**: L

**Description**

Integrate the Mandate System into the Buyer Agent's workflow. Ensure the agent programmatically checks mandates before committing to any purchase.

**Technical Details**

- Expose `check_mandate` as a tool to the Buyer Agent, or enforce it deterministically in the LangGraph edge before allowing `create_order`.
- Ensure if the mandate fails, the agent formulates a polite response explaining why it cannot complete the purchase.
- Log the mandate check result in the audit trail.

**Acceptance Criteria**

- [ ] Agent cannot execute a purchase if the mandate check fails.
- [ ] Agent gracefully handles mandate rejections and informs the user.
- [ ] Mandate checks are recorded in the system logs.

---

## Seller Agent

### KA-040: Seller agent initialization
- **Component**: Seller Agent
- **Priority**: P1
- **Dependencies**: KA-001
- **Estimated Complexity**: M

**Description**

Set up the AI Seller Agent, which runs on the merchant side. It evaluates buyer requests, determines pricing strategies, and responds to negotiations.

**Technical Details**

- Create `backend/agents/seller_agent.py`.
- Initialize an LLM agent that takes the Buyer's message, context, and merchant config as input.
- Provide tools like `check_inventory`, `calculate_margin`, `generate_upsell`.

**Acceptance Criteria**

- [ ] Seller agent can receive a text prompt and return a response.
- [ ] Agent can access merchant-specific configuration.

---

### KA-044: Margin guard implementation
- **Component**: Seller Agent
- **Priority**: P0
- **Dependencies**: KA-040
- **Estimated Complexity**: L

**Description**

Implement strict, deterministic margin guards for the Seller Agent. The AI must never be able to offer a price below the merchant's configured floor price.

**Technical Details**

- Create `backend/services/pricing_service.py`.
- Implement `validate_offer(product_id, offer_price)`.
- Fetch the product's base price and the merchant's `max_discount_percentage`.
- If the AI proposes a price below the floor, the system must deterministically override it or reject the action.

**Acceptance Criteria**

- [ ] System blocks any offer below the calculated floor price.
- [ ] Overrides AI-generated discounts that exceed the maximum allowed.
- [ ] Logs price adjustments for audit.

---

## Negotiation

### KA-051: Negotiation message format
- **Component**: Negotiation
- **Priority**: P1
- **Dependencies**: KA-050
- **Estimated Complexity**: S

**Description**

Define the structured JSON protocol for agent-to-agent communication during negotiations.

**Technical Details**

- Create `backend/models/negotiation.py`.
- Define `NegotiationMessage` Pydantic model: `session_id`, `round_number`, `sender` ('buyer'|'seller'), `type` ('offer'|'counter'|'accept'|'reject'), `offer_amount` (float), `reasoning` (str).
- Update the database schema to store these messages.

**Acceptance Criteria**

- [ ] Messages strictly adhere to the Pydantic schema.
- [ ] Messages are correctly serialized and deserialized between agents.

---

## Audit

### KA-060: Audit event schema
- **Component**: Audit
- **Priority**: P0
- **Dependencies**: KA-002
- **Estimated Complexity**: S

**Description**

Define the structured logging format for all agent actions, ensuring complete transparency and traceability.

**Technical Details**

- Create `backend/models/audit.py`.
- Define `AuditEventType` enum: `AGENT_THOUGHT`, `TOOL_CALL`, `MANDATE_CHECK`, `NEGOTIATION_ROUND`, `PAYMENT_ATTEMPT`, `ORDER_CREATED`.
- Define `AuditEvent` Pydantic model: `timestamp`, `event_type`, `agent_id`, `description`, `metadata` (JSON block).

**Acceptance Criteria**

- [ ] Audit schema captures all necessary fields for traceability.
- [ ] Enums are strictly enforced.

---

### KA-061: Audit logger service
- **Component**: Audit
- **Priority**: P0
- **Dependencies**: KA-060
- **Estimated Complexity**: M

**Description**

Implement the service that writes audit events to the database. This must be fast and ideally asynchronous so it doesn't block agent execution.

**Technical Details**

- Create `backend/services/audit_service.py`.
- Implement `log_event(event_type, description, metadata)`.
- Insert the record into the `audit_events` SQLite table.
- Consider using a background task (FastAPI BackgroundTasks) for the DB insert.

**Acceptance Criteria**

- [ ] Events are successfully written to the database.
- [ ] Service handles concurrent logging without locking issues.
- [ ] Writing logs does not significantly impact API latency.

---

## Frontend

### KA-080: Next.js project setup
- **Component**: Frontend
- **Priority**: P0
- **Dependencies**: KA-001
- **Estimated Complexity**: M

**Description**

Initialize the Next.js frontend application with Tailwind CSS and shadcn/ui components.

**Technical Details**

- Run `npx create-next-app@latest frontend --typescript --tailwind --eslint --app`.
- Run `npx shadcn-ui@latest init`.
- Add base components: Button, Input, Card, ScrollArea.
- Configure `next.config.js` to proxy API requests to the backend.

**Acceptance Criteria**

- [ ] Next.js dev server starts successfully.
- [ ] Tailwind and shadcn/ui are properly configured.
- [ ] API proxying works correctly.

---

### KA-081: Layout component
- **Component**: Frontend
- **Priority**: P1
- **Dependencies**: KA-080
- **Estimated Complexity**: S

**Description**

Create the main application layout featuring a split-pane design. The left pane will contain the chat interface with the Buyer Agent, and the right pane will display real-time activity, audit logs, and the mandate dashboard.

**Technical Details**

- Create `frontend/app/layout.tsx` (or main page component).
- Implement a responsive CSS Grid or Flexbox layout (e.g., `grid-cols-2` on large screens).
- Ensure both panes scroll independently using `ScrollArea`.

**Acceptance Criteria**

- [ ] Layout implements a 50/50 split on desktop.
- [ ] Layout stacks vertically on mobile devices.
- [ ] Panes scroll independently without breaking the page layout.

---

### KA-082: Chat interface component
- **Component**: Frontend
- **Priority**: P0
- **Dependencies**: KA-081
- **Estimated Complexity**: L

**Description**

Build the chat interface where the user interacts with the AI Buyer Agent. This includes the message history, input field, and visual indicators for agent processing.

**Technical Details**

- Create `components/ChatInterface.tsx`.
- State management for messages `[{role: 'user'|'agent', content: string}]`.
- Input area with a submit button.
- Add a 'typing' indicator for when the backend is processing.

**Acceptance Criteria**

- [ ] Users can type and send messages.
- [ ] Messages appear in the chat history with appropriate styling based on the sender.
- [ ] Typing indicator shows while waiting for an API response.

---

