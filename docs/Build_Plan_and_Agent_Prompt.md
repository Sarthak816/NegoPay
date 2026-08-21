# NegoPay Build Plan and Agent Prompts

This document serves as the master playbook for developing **NegoPay**, an agentic commerce platform for the Razorpay AI Buildathon. It provides a phased build plan with clear milestones, and exact prompts to feed into AI coding assistants (like Cursor, Claude, Antigravity) to build each component from scratch.

---

## 1. Build Phases Overview

### Phase 1: Foundation (Database + Config + Project Scaffold)
- Set up project structure (Python backend, Next.js frontend).
- Create SQLite database with all tables (products, merchants, orders, audit logs).
- Seed database with 30-50 realistic products across 2-3 merchants and 5 categories.
- Set up Razorpay SDK client with test keys.
- Set up FastAPI server skeleton and Docker Compose.
- **Milestone:** `python main.py` starts the server, the database is populated, and the Razorpay client can create a test order.

### Phase 2: MCP Server
- Implement all 8 MCP tools.
- Wire `search_products` to SQLite with filtering.
- Wire `create_order` to Razorpay Orders API.
- Wire `process_payment` to Razorpay Payments API.
- Wire `generate_qr` to Razorpay QR API.
- Add error handling on every tool.
- **Milestone:** MCP tools can be called directly and return correct responses; a product can be searched, ordered, and paid for via MCP.

### Phase 3: Mandate System
- Implement mandate data model.
- Implement per-transaction check, daily aggregate tracking, category filtering, approval threshold logic, and anti-splitting protection.
- **Milestone:** Unit tests pass for all mandate scenarios (approve, deny, over-daily, blocked category, split attempt).

### Phase 4: AI Buyer Agent
- Implement buyer agent with LangGraph or raw function calling.
- Define system prompt with tool definitions.
- Implement intent parsing (natural language → structured query).
- Add product discovery across multiple merchants, product comparison with reasoning, and mandate integration.
- Include audit trail logging on every action.
- **Milestone:** User can type 'buy me earbuds under 1000' and the agent searches, selects, checks mandate, creates order, and processes payment.

### Phase 5: AI Seller Agent
- Implement seller agent with LLM.
- Define system prompt with pricing/bundling/upsell capabilities.
- Implement margin guard (deterministic floor price enforcement), dynamic discount calculation, and bundle/upsell suggestion logic.
- **Milestone:** Seller agent can receive a product inquiry and respond with pricing, discount offers, and upsell suggestions.

### Phase 6: Negotiation Protocol
- Implement negotiation session manager.
- Handle message passing between buyer and seller agents, round counting, and max rounds enforcement.
- Implement walk-away threshold evaluation, BATNA handling, deadlock detection, and resolution.
- **Milestone:** Two agents can negotiate a deal over 3-5 rounds, reach agreement or deadlock, and the outcome is logged.

### Phase 7: Failure Handling
- Implement all 6 failure scenarios (Infinite negotiation loop, Hallucinated product, Split-order mandate bypass, Seller price war, Double charge, MCP server crash).
- **Milestone:** Each failure scenario can be triggered and is handled gracefully with audit log.

### Phase 8: Razorpay Webhooks
- Set up webhook endpoint and verify signature.
- Handle `payment.captured` and `payment.failed` events.
- Update order status and push to frontend via WebSocket.
- **Milestone:** Payment status updates flow from Razorpay → webhook → database → frontend in real-time.

### Phase 9: Frontend Dashboard
- Next.js project with Tailwind + shadcn/ui.
- Implement Chat interface, Agent activity feed (real-time), Negotiation transcript viewer, Mandate dashboard, and Audit trail viewer.
- **Milestone:** Complete UI showing chat + live agent activity + mandate status + audit trail.

### Phase 10: Polish & Demo Prep
- Create README with setup instructions.
- Add Docker Compose one-command setup.
- Clean up repo and prepare for demo.
- **Milestone:** Repository is ready for presentation.

---

## 2. AI Agent Prompts

### Phase 1 Agent Prompt

```markdown
### Context
We are building a new project called NegoPay, an agentic commerce platform using a Python backend and a Next.js frontend. This is Phase 1, where we set up the foundation, database, and project scaffolding.

### Task
Set up the Python backend project structure using FastAPI, SQLAlchemy for SQLite, and the official `razorpay` Python SDK. Create a SQLite database with tables for products, merchants, orders, and audit logs. Seed the database with 30-50 realistic products across 2-3 merchants and 5 categories. Set up a basic FastAPI server skeleton, Docker Compose for local dev, and initialize the Razorpay client using test keys.

### Files to Create
- `backend/requirements.txt`: Include fastapi, uvicorn, sqlalchemy, pydantic, razorpay, python-dotenv.
- `backend/main.py`: FastAPI application entry point.
- `backend/database.py`: SQLAlchemy setup and SQLite connection.
- `backend/models.py`: SQLAlchemy models (Merchant, Product, Order, AuditLog).
- `backend/schemas.py`: Pydantic models for request/response validation.
- `backend/seed.py`: Script to populate the database with seed data.
- `backend/razorpay_client.py`: Initialization of Razorpay client.
- `docker-compose.yml`: For running backend (and later frontend) services.
- `.env.example`: Template for environment variables including Razorpay keys.

### Data Models / Schemas
- **Merchant**: id, name, razorpay_account_id (optional for route)
- **Product**: id, merchant_id, name, description, category, price, floor_price (margin guard), inventory_count.
- **Order**: id, order_id (from Razorpay), amount, currency, status, merchant_id.
- **AuditLog**: id, timestamp, agent_type, action, details (JSON).

### Implementation Details
- Use Python 3.11+.
- In `razorpay_client.py`, fetch `RAZORPAY_KEY_ID` and `RAZORPAY_KEY_SECRET` from environment variables.
- Write a `/health` endpoint in `main.py` that verifies DB connectivity.
- Write a script `seed.py` that clears existing data and inserts 3-5 merchants and 30-50 tech/lifestyle products across categories like Electronics, Audio, Wearables.

### Integration Points
- Backend runs on port 8000.
- Database is a local file: `NegoPay.db`.

### Acceptance Criteria
- Running `docker-compose up` starts the server successfully.
- Executing `python backend/seed.py` populates `NegoPay.db` without errors.
- A manual Python script can instantiate the Razorpay client and successfully call `client.order.create({"amount": 100, "currency": "INR"})`.
```

### Phase 2 Agent Prompt

```markdown
### Context
The foundation is built, and we have a FastAPI server, SQLite DB, and Razorpay client. We now need to build the MCP (Model Context Protocol) Server for the Merchant.

### Task
Implement an MCP server exposing 8 tools that connect to our database and Razorpay test-mode APIs. Use the official Python `mcp` SDK. Wire the tools to perform database queries and execute Razorpay API calls.

### Files to Create
- `backend/mcp_server.py`: The MCP server implementation and tool registration.
- `backend/mcp_tools.py`: The actual business logic for each tool.

### Data Models / Schemas
Tools to expose:
1. `search_products(query: str, category: str = None, max_price: float = None)` -> List of products.
2. `get_product_details(product_id: int)` -> Detailed info including inventory.
3. `check_inventory(product_id: int, quantity: int)` -> Boolean.
4. `create_order(product_id: int, quantity: int, amount: int)` -> Razorpay Order dict.
5. `process_payment(order_id: str, payment_details: dict)` -> Payment response.
6. `generate_qr(amount: int, description: str)` -> QR string/URL.
7. `get_order_status(order_id: str)` -> Status string.
8. `request_negotiation(product_id: int, proposed_price: float)` -> Start negotiation flag.

### Implementation Details
- `search_products`: Perform ILIKE SQL queries on Product.name/description. Filter by category and price if provided.
- `create_order`: Must call `razorpay_client.order.create({"amount": amount * 100, "currency": "INR"})`. Save the created order in the DB.
- Handle errors gracefully. If Razorpay throws an exception, catch it and return a descriptive JSON error instead of crashing the MCP server.
- The MCP server should be runnable as a standalone process (stdio) or via SSE. Implement stdio for now.

### Integration Points
- Calls functions from `database.py` and `razorpay_client.py`.
- Exposed as an MCP server that the AI agents will consume.

### Acceptance Criteria
- All 8 tools are registered in the MCP server.
- A test client calling `create_order` successfully returns a Razorpay order ID.
- `search_products` returns accurate results based on SQLite contents.
```

### Phase 3 Agent Prompt

```markdown
### Context
The MCP server is up. Now we need a deterministic Mandate System that acts as a guardrail for the AI Buyer Agent's spending.

### Task
Implement a Mandate System that evaluates purchase requests against strict, non-AI rules before any order creation is allowed.

### Files to Create
- `backend/mandate.py`: Core logic for mandate evaluation.
- `backend/test_mandate.py`: Unit tests for mandate logic.

### Data Models / Schemas
Mandate Config (can be hardcoded or in DB):
- `per_transaction_limit`: e.g., 5000 INR
- `daily_aggregate_limit`: e.g., 20000 INR
- `blocked_categories`: e.g., ["Gaming", "Luxury"]
- `approval_threshold`: e.g., > 3000 INR requires explicit user approval flag.

### Implementation Details
- Create a function `evaluate_mandate(request_amount: float, category: str, user_id: str, is_approved: bool) -> MandateResult`.
- `MandateResult` is a Pydantic model: `is_allowed: bool`, `reason: str`.
- **Anti-splitting protection:** Query the DB for orders in the last 10 minutes for the same category. If `sum(recent_orders) + request_amount > per_transaction_limit`, reject it.
- **Daily aggregate:** Sum all orders for the current date for the user.

### Integration Points
- Will be called by the AI Buyer Agent before executing `create_order`.
- Requires querying the `Order` table for aggregate limits and anti-splitting.

### Acceptance Criteria
- `pytest backend/test_mandate.py` passes all cases: approve normal, deny over-limit, deny blocked category, deny over daily limit, deny split attempt (e.g., 5 orders of 1000 when limit is 4000).
```

### Phase 4 Agent Prompt

```markdown
### Context
We have the Mandate System and MCP tools. Now we need the AI Buyer Agent that takes natural language requests, interacts with the tools, and makes purchases.

### Task
Implement the AI Buyer Agent using LangGraph (or raw function calling with OpenAI/Anthropic). The agent must parse user intent, discover products using `search_products`, evaluate options, check the mandate using the Mandate System, and execute the purchase if allowed. Log every step.

### Files to Create
- `backend/buyer_agent.py`: Agent definition, system prompt, and graph execution.
- `backend/audit_logger.py`: Utility for logging agent actions.

### Implementation Details
- **System Prompt**: Define the agent's persona. "You are a smart shopping assistant. You find the best deals, compare them, check the user's spending mandate, and buy the product."
- **Workflow**:
  1. Receive "Buy earbuds under 2000".
  2. Call `search_products`.
  3. Reason about the best option.
  4. Call `evaluate_mandate`.
  5. If allowed, call `create_order` via MCP.
- **Audit Logging**: Every time the agent makes a decision or tool call, append a structured JSON log to the `AuditLog` table (e.g., `{"step": "search", "query": "earbuds", "results_count": 5}`).

### Integration Points
- Uses the LLM API (OpenAI or Anthropic).
- Calls the Python functions corresponding to the MCP tools directly (since they are in the same backend) or via an MCP client.
- Uses `evaluate_mandate`.

### Acceptance Criteria
- A script passing "buy me a keyboard under 1500" successfully results in an order being created in the DB and Razorpay, and audit logs are recorded.
- Passing "buy a luxury watch for 50000" fails cleanly due to the mandate.
```

### Phase 5 Agent Prompt

```markdown
### Context
The Buyer Agent works. Now we need a Merchant-side AI Seller Agent to handle inquiries, dynamic pricing, and upsells.

### Task
Implement the AI Seller Agent. It receives structured requests from the buyer agent (or user) and responds with offers, adhering strictly to margin guards (floor price).

### Files to Create
- `backend/seller_agent.py`: Agent definition and pricing logic.

### Data Models / Schemas
- `SellerRequest`: product_id, proposed_price, quantity.
- `SellerResponse`: status (accept/counter/reject), final_price, upsell_product_id (optional), reason.

### Implementation Details
- **Margin Guard**: The agent must NEVER offer or accept a price below `Product.floor_price`.
- **Dynamic Discount**: If `proposed_price` is between `floor_price` and `price`, the LLM can decide to accept based on quantity (e.g., higher discount for bulk) or counter-offer.
- **Upsells**: If accepting, query the DB for related products in the same category and suggest a bundle.
- Log all decisions to the `AuditLog`.

### Integration Points
- Interacts with the `Product` table to check `floor_price`.
- Invoked during the negotiation protocol.

### Acceptance Criteria
- If buyer proposes a price below `floor_price`, seller rejects or counters at or above `floor_price`.
- If buyer proposes a fair price, seller accepts and suggests a related upsell.
```

### Phase 6 Agent Prompt

```markdown
### Context
We have both Buyer and Seller agents. Now we need them to negotiate directly with each other.

### Task
Implement an Agent-to-Agent Negotiation Protocol. This is a structured loop where the Buyer and Seller exchange offers until an agreement is reached, maximum rounds are hit, or walk-away thresholds are breached.

### Files to Create
- `backend/negotiator.py`: The negotiation state machine and loop.

### Implementation Details
- Create a `run_negotiation(buyer_context, seller_context)` function.
- **Round Limits**: Hard cap at 5 rounds to prevent infinite loops.
- **Walk-away / BATNA**: If the Seller refuses to meet the Buyer's max price after 3 rounds, the Buyer should query for an alternative product (BATNA) and terminate negotiation with the current seller.
- The loop consists of: Buyer makes offer -> Seller evaluates and responds -> Buyer evaluates response.
- Log every round's bid and ask to `AuditLog`.

### Integration Points
- Uses `buyer_agent.py` and `seller_agent.py`.
- Final state dictates whether `create_order` is called.

### Acceptance Criteria
- A test script running a negotiation between a tight-budget buyer and a strict seller resolves in a deadlock within 5 rounds.
- A test script with overlapping acceptable price ranges reaches an agreement in 1-3 rounds.
```

### Phase 7 Agent Prompt

```markdown
### Context
The core flow works. We need to implement robust failure handling for 6 specific scenarios.

### Task
Implement deterministic guards and recovery paths for: Infinite negotiation loop, Hallucinated product, Split-order mandate bypass, Seller price war, Double charge, and MCP server crash.

### Files to Create
- `backend/guards.py`: Validation utilities.
- Updates to existing files (negotiator, mcp_tools, mandate).

### Implementation Details
1. **Infinite Loop**: Ensure the 5-round cap in `negotiator.py` raises a `NegotiationTimeout` exception.
2. **Hallucinated Product**: In `create_order`, explicitly verify `product_id` exists in the DB before calling Razorpay.
3. **Split-order**: Ensure the logic from Phase 3 strictly aborts.
4. **Seller Price War**: (Conceptual) restrict seller to only lower prices, never raise them during a single negotiation session.
5. **Double Charge**: Add an `idempotency_key` (UUID) to the `create_order` tool. Store it in the DB; if called again with the same key, return the existing order.
6. **MCP Crash**: Wrap MCP tool executions in try-except blocks with a 5-second timeout, returning a standardized fallback response.

### Integration Points
- Modifies `create_order` tool, Mandate evaluator, and Negotiator.

### Acceptance Criteria
- Triggering a double charge with the same idempotency key returns the original Razorpay order instead of creating a new one.
- Requesting a non-existent product ID fails with a clean "Invalid Product" error, not a stack trace.
```

### Phase 8 Agent Prompt

```markdown
### Context
Orders are being created. We need to handle Razorpay Webhooks to track asynchronous payment completion.

### Task
Implement a webhook endpoint in FastAPI to receive and verify Razorpay events (`payment.captured`, `payment.failed`). Update the database and notify the frontend via WebSockets.

### Files to Create
- `backend/webhooks.py`: FastAPI router for webhooks.
- `backend/websocket_manager.py`: Manager for active WS connections.

### Implementation Details
- Endpoint: `POST /webhook`
- Use `razorpay_client.utility.verify_webhook_signature(payload, signature, secret)`.
- If valid, parse the event. For `payment.captured`, update `Order.status = 'paid'`.
- Broadcast the update via WebSocket to connected clients using the `websocket_manager`.

### Integration Points
- Mounts into `main.py`.
- Needs a `RAZORPAY_WEBHOOK_SECRET` in `.env`.

### Acceptance Criteria
- Simulating a webhook payload with a valid signature updates the order in the database.
- A connected WebSocket client receives a JSON message `{"type": "order_update", "order_id": "...", "status": "paid"}`.
```

### Phase 9 Agent Prompt

```markdown
### Context
The backend is fully complete and robust. We need the Next.js Frontend Dashboard to visualize the agentic commerce process.

### Task
Build the Next.js (App Router) frontend with Tailwind CSS and shadcn/ui. Create a split-view dashboard showing the user chat, live agent activity, mandate status, and audit logs.

### Files to Create
- `frontend/app/page.tsx`: Main dashboard layout.
- `frontend/components/chat-panel.tsx`: User input and chatbot UI.
- `frontend/components/activity-feed.tsx`: Real-time WebSocket consumer for agent actions.
- `frontend/components/mandate-dashboard.tsx`: UI showing spending limits (progress bars).
- `frontend/components/audit-table.tsx`: Table displaying structured logs.

### Implementation Details
- Use React hooks to manage WebSocket connections to `ws://localhost:8000/ws`.
- Chat panel sends text to a backend endpoint (e.g., `POST /api/chat`) which triggers the Buyer Agent.
- As the Buyer Agent executes tools, the backend broadcasts logs over WS, which populate the Activity Feed in real time.
- Use shadcn/ui components: Cards, Progress (for mandates), ScrollArea, Table.

### Integration Points
- Connects to FastAPI backend running on port 8000.

### Acceptance Criteria
- User can open `localhost:3000`, type a prompt, and visually see the agents negotiating and the mandate bar updating without refreshing the page.
```

### Phase 10 Agent Prompt

```markdown
### Context
The project is functionally complete. We need to finalize it for the Razorpay AI Buildathon submission.

### Task
Prepare the project for presentation. Write a comprehensive README, ensure Docker Compose works cleanly, and prepare a 'what broke / challenges' document.

### Files to Create
- `README.md`: Project description, architecture diagram, setup instructions.
- `docs/CHALLENGES.md`: Documenting technical hurdles (e.g., state management in LangGraph, idempotency).
- `Makefile` (optional): Helper commands like `make run`, `make test`.

### Implementation Details
- Ensure `docker-compose up --build` brings up both the FastAPI backend and Next.js frontend, fully wired together.
- Include dummy credentials or strict instructions on where to place the `rzp_test_xxx` keys.

### Integration Points
- Entire repository.

### Acceptance Criteria
- A developer can clone the repo, add their test keys to `.env`, run `docker-compose up`, and use the platform within 2 minutes.
```
