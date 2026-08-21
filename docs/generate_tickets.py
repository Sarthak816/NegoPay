import os
import json

tickets = [
    # Foundation
    {
        "id": "KA-001",
        "title": "Project scaffold",
        "component": "DevOps",
        "priority": "P0",
        "dependencies": "None",
        "description": "Initialize the base project structure for KartAgent. This includes creating the standard directory layout for the backend, frontend, and shared components, as well as setting up the Python virtual environment and dependency management.",
        "tech_details": "- Create `backend/` and `frontend/` directories.\n- In `backend/`, create `pyproject.toml` with dependencies: fastapi, uvicorn, razorpay, mcp, sqlite3, pydantic, langgraph.\n- Create `requirements.txt` from pyproject.toml.\n- Set up `.gitignore` for Python and Node.js.",
        "ac": ["Repository has correct folder structure.", "`pyproject.toml` and `requirements.txt` exist with valid dependencies.", "Virtual environment can be created and dependencies install successfully."],
        "complexity": "S"
    },
    {
        "id": "KA-002",
        "title": "SQLite database setup",
        "component": "Foundation",
        "priority": "P0",
        "dependencies": "KA-001",
        "description": "Set up the SQLite database schemas. We need tables to store product catalogs for multiple merchants, track orders and payments, store spending mandates, log audit events, and manage negotiation sessions.",
        "tech_details": "- Create `backend/database.py` with SQLAlchemy or raw SQLite setup.\n- Define tables: `merchants`, `products` (foreign key to merchants), `orders`, `payments`, `mandates`, `audit_events`, `negotiation_sessions`.\n- Write an initialization script `init_db.py` that creates these tables if they don't exist.",
        "ac": ["Running `init_db.py` creates a `kartagent.db` file.", "All required tables are created with correct schemas and foreign keys.", "Database connection can be established without errors."],
        "complexity": "M"
    },
    {
        "id": "KA-003",
        "title": "Product seed data",
        "component": "Foundation",
        "priority": "P0",
        "dependencies": "None",
        "description": "Create realistic JSON seed data for the product catalog. This is essential for the AI buyer to have meaningful products to search and compare across multiple merchants.",
        "tech_details": "- Create `backend/seed_products.json`.\n- Define 3 merchants: TechMart, SoundStore, BookHaven.\n- Add 50 products across 5 categories: Electronics, Audio, Books, Clothing, Sports.\n- Each product needs: `id`, `merchant_id`, `name`, `description`, `price`, `currency` (INR), `stock_quantity`, `category`, `tags`.",
        "ac": ["`seed_products.json` contains exactly 50 products.", "Products are distributed across 3 merchants and 5 categories.", "JSON is valid and follows the schema."],
        "complexity": "M"
    },
    {
        "id": "KA-004",
        "title": "Database seeding script",
        "component": "Foundation",
        "priority": "P0",
        "dependencies": "KA-002, KA-003",
        "description": "Write a script to load the seed data from the JSON file into the SQLite database. This script will be run during project setup to populate the initial state.",
        "tech_details": "- Create `backend/seed_db.py`.\n- Read `seed_products.json`.\n- Insert merchants into the `merchants` table.\n- Insert products into the `products` table.\n- Handle conflicts (e.g., clear tables before seeding or use upsert).",
        "ac": ["Running `seed_db.py` successfully populates the database.", "Data in SQLite matches the JSON file exactly.", "Script can be run multiple times safely (idempotent)."],
        "complexity": "S"
    },
    {
        "id": "KA-005",
        "title": "Razorpay client wrapper",
        "component": "Razorpay",
        "priority": "P0",
        "dependencies": "KA-001",
        "description": "Create a wrapper around the Razorpay Python SDK. This wrapper will encapsulate the initialization with test keys and provide helper methods for common operations like creating orders and capturing payments.",
        "tech_details": "- Create `backend/razorpay_client.py`.\n- Initialize `razorpay.Client(auth=(RZP_KEY_ID, RZP_KEY_SECRET))`.\n- Implement methods: `create_order(amount, currency, receipt_id)`, `capture_payment(payment_id, amount)`, `verify_webhook_signature(body, signature, secret)`.\n- Use Pydantic models for request/response typing.",
        "ac": ["Wrapper can be imported and initialized successfully.", "Helper methods correctly map to Razorpay SDK calls.", "Authentication uses environment variables."],
        "complexity": "S"
    },
    {
        "id": "KA-006",
        "title": "FastAPI server skeleton",
        "component": "Foundation",
        "priority": "P0",
        "dependencies": "KA-001",
        "description": "Set up the core FastAPI application. This serves as the backend entry point, providing health checks, CORS configuration for the frontend, and global error handling.",
        "tech_details": "- Create `backend/main.py`.\n- Initialize FastAPI app with title and description.\n- Add CORS middleware allowing all origins (for local dev).\n- Add a `/health` endpoint returning `{\"status\": \"ok\"}`.\n- Add global exception handlers that return standardized JSON error responses.",
        "ac": ["Server starts successfully with `uvicorn main:app --reload`.", "`/health` endpoint returns 200 OK.", "CORS allows requests from localhost."],
        "complexity": "S"
    },
    {
        "id": "KA-007",
        "title": "Configuration management",
        "component": "Foundation",
        "priority": "P0",
        "dependencies": "KA-001",
        "description": "Implement configuration management using environment variables. This centralizes all settings like API keys, database URLs, and feature flags.",
        "tech_details": "- Create `backend/config.py` using `pydantic-settings`.\n- Define `Settings` class with fields: `DATABASE_URL`, `RZP_KEY_ID`, `RZP_KEY_SECRET`, `RZP_WEBHOOK_SECRET`, `LLM_API_KEY`.\n- Create a `.env.template` file with dummy values.\n- Ensure settings are loaded on application startup.",
        "ac": ["Settings class validates environment variables correctly.", "`.env.template` is provided in the repository.", "Application fails to start if required variables are missing."],
        "complexity": "S"
    },
    {
        "id": "KA-008",
        "title": "Docker Compose setup",
        "component": "DevOps",
        "priority": "P1",
        "dependencies": "KA-001",
        "description": "Create a Docker Compose configuration to easily spin up the entire application stack locally, including the backend, frontend, and persistent volumes for the database.",
        "tech_details": "- Create `docker-compose.yml` in the project root.\n- Define `backend` service building from `backend/Dockerfile`, exposing port 8000.\n- Define `frontend` service building from `frontend/Dockerfile`, exposing port 3000.\n- Define a volume for the SQLite database to persist data across restarts.",
        "ac": ["`docker-compose up` starts both backend and frontend successfully.", "Backend API is accessible at `localhost:8000`.", "Database state persists after `docker-compose down` and `up`."],
        "complexity": "M"
    },
    
    # MCP Server
    {
        "id": "KA-010",
        "title": "MCP server initialization",
        "component": "MCP Server",
        "priority": "P0",
        "dependencies": "KA-006",
        "description": "Set up the Merchant MCP Server using the official Python MCP SDK. This server will expose the merchant's catalog and capabilities as tools to the AI Buyer Agent.",
        "tech_details": "- Create `backend/mcp_server.py`.\n- Initialize an MCP Server instance: `Server(\"merchant-mcp\")`.\n- Set up the transport layer (stdio or SSE depending on deployment architecture, recommend stdio for initial local agent integration).\n- Add boilerplate for tool registration decorators.",
        "ac": ["MCP server script runs without errors.", "Basic tool registration structure is in place.", "Server can communicate over stdio (responds to basic MCP initialization messages)."],
        "complexity": "M"
    },
    {
        "id": "KA-011",
        "title": "search_products tool",
        "component": "MCP Server",
        "priority": "P0",
        "dependencies": "KA-010, KA-002",
        "description": "Implement the `search_products` MCP tool. This allows the buyer agent to search the catalog using semantic queries and filters.",
        "tech_details": "- Register `@server.tool()` for `search_products`.\n- Arguments: `query` (str), `max_price` (float, optional), `category` (str, optional).\n- Implementation: Query the SQLite `products` table using `LIKE` for the query, and apply price/category filters if provided.\n- Return a list of product dictionaries with basic details.",
        "ac": ["Tool successfully queries the database and returns matching products.", "Filters (price, category) are applied correctly.", "Returns empty list if no matches found."],
        "complexity": "M"
    },
    {
        "id": "KA-012",
        "title": "get_product_details tool",
        "component": "MCP Server",
        "priority": "P0",
        "dependencies": "KA-010, KA-002",
        "description": "Implement the `get_product_details` MCP tool. This allows the buyer agent to retrieve full information about a specific product, including description and exact stock levels.",
        "tech_details": "- Register `@server.tool()` for `get_product_details`.\n- Arguments: `product_id` (str).\n- Implementation: Fetch the specific product row from the `products` table. Return all fields.\n- Raise an appropriate MCP error if the product doesn't exist.",
        "ac": ["Returns complete product JSON for a valid ID.", "Returns clear error message if product ID is invalid.", "Stock quantity is accurately reported."],
        "complexity": "S"
    },
    {
        "id": "KA-014",
        "title": "create_order tool",
        "component": "MCP Server",
        "priority": "P0",
        "dependencies": "KA-010, KA-005",
        "description": "Implement the `create_order` MCP tool. This tool delegates to the Razorpay client to create an order on the merchant's behalf.",
        "tech_details": "- Register `@server.tool()` for `create_order`.\n- Arguments: `product_ids` (list[str]), `quantities` (list[int]), `idempotency_key` (str).\n- Implementation: Calculate total amount, call `razorpay_client.create_order()`. Store order details in SQLite `orders` table.\n- Return the Razorpay `order_id` and total amount.",
        "ac": ["Creates a valid order in Razorpay (test mode).", "Saves order record to the local SQLite database.", "Uses idempotency key to prevent duplicate orders for the same request."],
        "complexity": "L"
    },
    {
        "id": "KA-018",
        "title": "request_negotiation tool",
        "component": "MCP Server",
        "priority": "P1",
        "dependencies": "KA-010, KA-050",
        "description": "Implement the `request_negotiation` MCP tool. This initiates a negotiation session between the Buyer Agent and the Merchant's Seller Agent.",
        "tech_details": "- Register `@server.tool()` for `request_negotiation`.\n- Arguments: `product_id` (str), `buyer_initial_offer` (float), `buyer_context` (str).\n- Implementation: Create a new session in `negotiation_sessions` table. Trigger the Seller Agent to evaluate the offer and generate a response.\n- Return the session ID and the Seller's initial counter-offer.",
        "ac": ["Creates a new negotiation session record.", "Correctly routes the offer to the Seller Agent logic.", "Returns a structured response containing the session ID and seller's reply."],
        "complexity": "L"
    },

    # Mandate System
    {
        "id": "KA-020",
        "title": "Mandate data model",
        "component": "Mandate",
        "priority": "P0",
        "dependencies": "KA-002",
        "description": "Define the data structures for the Mandate System, which controls the deterministic spending rules for the Buyer Agent.",
        "tech_details": "- Create `backend/models/mandate.py`.\n- Define a Pydantic model `Mandate` with fields: `id`, `user_id`, `max_transaction_amount`, `daily_limit`, `allowed_categories` (list), `requires_approval_above`.\n- Ensure mapping to the SQLite `mandates` table.",
        "ac": ["Pydantic model correctly validates mandate data.", "Schema perfectly matches the SQLite table structure."],
        "complexity": "S"
    },
    {
        "id": "KA-021",
        "title": "Per-transaction limit check",
        "component": "Mandate",
        "priority": "P0",
        "dependencies": "KA-020",
        "description": "Implement the core logic to enforce per-transaction limits. Before any order is created, the system must verify the amount against this limit.",
        "tech_details": "- Create `backend/services/mandate_service.py`.\n- Implement `check_transaction_limit(mandate_id, amount)`.\n- Fetch mandate, compare `amount` <= `max_transaction_amount`.\n- Return a structured result: `{\"allowed\": bool, \"reason\": str}`.",
        "ac": ["Returns allowed=True when amount is below limit.", "Returns allowed=False and a reason when amount exceeds limit."],
        "complexity": "S"
    },
    {
        "id": "KA-022",
        "title": "Daily aggregate spend tracker",
        "component": "Mandate",
        "priority": "P0",
        "dependencies": "KA-020",
        "description": "Implement tracking and enforcement for daily spending limits to ensure the Buyer Agent doesn't drain the account over multiple transactions in a single day.",
        "tech_details": "- In `mandate_service.py`, implement `check_daily_limit(mandate_id, amount)`.\n- Query the `orders` table to sum all successful transaction amounts for the given user today.\n- Add the proposed `amount`. If total > `daily_limit`, return allowed=False.\n- Return structured result.",
        "ac": ["Correctly sums previous transactions for the current day.", "Blocks transactions that would push the total over the daily limit.", "Allows transactions within the daily limit."],
        "complexity": "M"
    },

    # AI Buyer Agent
    {
        "id": "KA-030",
        "title": "Buyer agent initialization",
        "component": "Buyer Agent",
        "priority": "P0",
        "dependencies": "KA-001",
        "description": "Set up the core loop for the AI Buyer Agent. This agent receives natural language instructions and uses tools to execute the purchase.",
        "tech_details": "- Create `backend/agents/buyer_agent.py`.\n- Initialize LangGraph or a basic OpenAI/Anthropic function calling loop.\n- Set up the state dictionary: `messages`, `current_intent`, `selected_products`, `mandate_status`.\n- Create the agent execution entrypoint `run_buyer_agent(prompt, mandate_id)`.",
        "ac": ["Agent can be invoked with a text prompt.", "Agent loop handles basic tool calls and returns a final response.", "Agent maintains state during execution."],
        "complexity": "L"
    },
    {
        "id": "KA-031",
        "title": "Buyer agent system prompt",
        "component": "Buyer Agent",
        "priority": "P0",
        "dependencies": "KA-030",
        "description": "Write the comprehensive system prompt that defines the Buyer Agent's persona, capabilities, strict adherence to mandates, and negotiation strategy.",
        "tech_details": "- Define the prompt in `backend/agents/prompts.py`.\n- Include sections: Role, Capabilities, Mandate Rules (NEVER bypass), Negotiation Guidelines (always try to get at least 5% off if price > 1000), Output Format.\n- Inject the current active mandate details dynamically into the prompt.",
        "ac": ["Prompt clearly defines the agent's constraints.", "Prompt explicitly instructs the agent to check mandates before purchasing.", "Agent follows the persona defined in the prompt."],
        "complexity": "M"
    },
    {
        "id": "KA-035",
        "title": "Mandate integration in buyer agent",
        "component": "Buyer Agent",
        "priority": "P0",
        "dependencies": "KA-030, KA-021",
        "description": "Integrate the Mandate System into the Buyer Agent's workflow. Ensure the agent programmatically checks mandates before committing to any purchase.",
        "tech_details": "- Expose `check_mandate` as a tool to the Buyer Agent, or enforce it deterministically in the LangGraph edge before allowing `create_order`.\n- Ensure if the mandate fails, the agent formulates a polite response explaining why it cannot complete the purchase.\n- Log the mandate check result in the audit trail.",
        "ac": ["Agent cannot execute a purchase if the mandate check fails.", "Agent gracefully handles mandate rejections and informs the user.", "Mandate checks are recorded in the system logs."],
        "complexity": "L"
    },

    # AI Seller Agent
    {
        "id": "KA-040",
        "title": "Seller agent initialization",
        "component": "Seller Agent",
        "priority": "P1",
        "dependencies": "KA-001",
        "description": "Set up the AI Seller Agent, which runs on the merchant side. It evaluates buyer requests, determines pricing strategies, and responds to negotiations.",
        "tech_details": "- Create `backend/agents/seller_agent.py`.\n- Initialize an LLM agent that takes the Buyer's message, context, and merchant config as input.\n- Provide tools like `check_inventory`, `calculate_margin`, `generate_upsell`.",
        "ac": ["Seller agent can receive a text prompt and return a response.", "Agent can access merchant-specific configuration."],
        "complexity": "M"
    },
    {
        "id": "KA-044",
        "title": "Margin guard implementation",
        "component": "Seller Agent",
        "priority": "P0",
        "dependencies": "KA-040",
        "description": "Implement strict, deterministic margin guards for the Seller Agent. The AI must never be able to offer a price below the merchant's configured floor price.",
        "tech_details": "- Create `backend/services/pricing_service.py`.\n- Implement `validate_offer(product_id, offer_price)`.\n- Fetch the product's base price and the merchant's `max_discount_percentage`.\n- If the AI proposes a price below the floor, the system must deterministically override it or reject the action.",
        "ac": ["System blocks any offer below the calculated floor price.", "Overrides AI-generated discounts that exceed the maximum allowed.", "Logs price adjustments for audit."],
        "complexity": "L"
    },

    # Negotiation Protocol
    {
        "id": "KA-051",
        "title": "Negotiation message format",
        "component": "Negotiation",
        "priority": "P1",
        "dependencies": "KA-050",
        "description": "Define the structured JSON protocol for agent-to-agent communication during negotiations.",
        "tech_details": "- Create `backend/models/negotiation.py`.\n- Define `NegotiationMessage` Pydantic model: `session_id`, `round_number`, `sender` ('buyer'|'seller'), `type` ('offer'|'counter'|'accept'|'reject'), `offer_amount` (float), `reasoning` (str).\n- Update the database schema to store these messages.",
        "ac": ["Messages strictly adhere to the Pydantic schema.", "Messages are correctly serialized and deserialized between agents."],
        "complexity": "S"
    },

    # Audit Trail
    {
        "id": "KA-060",
        "title": "Audit event schema",
        "component": "Audit",
        "priority": "P0",
        "dependencies": "KA-002",
        "description": "Define the structured logging format for all agent actions, ensuring complete transparency and traceability.",
        "tech_details": "- Create `backend/models/audit.py`.\n- Define `AuditEventType` enum: `AGENT_THOUGHT`, `TOOL_CALL`, `MANDATE_CHECK`, `NEGOTIATION_ROUND`, `PAYMENT_ATTEMPT`, `ORDER_CREATED`.\n- Define `AuditEvent` Pydantic model: `timestamp`, `event_type`, `agent_id`, `description`, `metadata` (JSON block).",
        "ac": ["Audit schema captures all necessary fields for traceability.", "Enums are strictly enforced."],
        "complexity": "S"
    },
    {
        "id": "KA-061",
        "title": "Audit logger service",
        "component": "Audit",
        "priority": "P0",
        "dependencies": "KA-060",
        "description": "Implement the service that writes audit events to the database. This must be fast and ideally asynchronous so it doesn't block agent execution.",
        "tech_details": "- Create `backend/services/audit_service.py`.\n- Implement `log_event(event_type, description, metadata)`.\n- Insert the record into the `audit_events` SQLite table.\n- Consider using a background task (FastAPI BackgroundTasks) for the DB insert.",
        "ac": ["Events are successfully written to the database.", "Service handles concurrent logging without locking issues.", "Writing logs does not significantly impact API latency."],
        "complexity": "M"
    },

    # Razorpay Integration
    {
        "id": "KA-071",
        "title": "Razorpay payment capture flow",
        "component": "Razorpay",
        "priority": "P0",
        "dependencies": "KA-005, KA-014",
        "description": "Implement the payment capture flow. Once an order is created and the buyer agrees to pay, simulate the payment capture via the Razorpay test API.",
        "tech_details": "- Implement `capture_payment` endpoint in `main.py`.\n- Receive `order_id` and `amount`.\n- Call Razorpay API to simulate payment success (using test card/UPI data if necessary, or just rely on the API response).\n- Update the `orders` table status to 'paid'.",
        "ac": ["Successfully calls Razorpay payment API.", "Order status in database is updated to 'paid' upon success.", "Handles API errors gracefully."],
        "complexity": "L"
    },

    # Frontend
    {
        "id": "KA-080",
        "title": "Next.js project setup",
        "component": "Frontend",
        "priority": "P0",
        "dependencies": "KA-001",
        "description": "Initialize the Next.js frontend application with Tailwind CSS and shadcn/ui components.",
        "tech_details": "- Run `npx create-next-app@latest frontend --typescript --tailwind --eslint --app`.\n- Run `npx shadcn-ui@latest init`.\n- Add base components: Button, Input, Card, ScrollArea.\n- Configure `next.config.js` to proxy API requests to the backend.",
        "ac": ["Next.js dev server starts successfully.", "Tailwind and shadcn/ui are properly configured.", "API proxying works correctly."],
        "complexity": "M"
    },
    {
        "id": "KA-081",
        "title": "Layout component",
        "component": "Frontend",
        "priority": "P1",
        "dependencies": "KA-080",
        "description": "Create the main application layout featuring a split-pane design. The left pane will contain the chat interface with the Buyer Agent, and the right pane will display real-time activity, audit logs, and the mandate dashboard.",
        "tech_details": "- Create `frontend/app/layout.tsx` (or main page component).\n- Implement a responsive CSS Grid or Flexbox layout (e.g., `grid-cols-2` on large screens).\n- Ensure both panes scroll independently using `ScrollArea`.",
        "ac": ["Layout implements a 50/50 split on desktop.", "Layout stacks vertically on mobile devices.", "Panes scroll independently without breaking the page layout."],
        "complexity": "S"
    },
    {
        "id": "KA-082",
        "title": "Chat interface component",
        "component": "Frontend",
        "priority": "P0",
        "dependencies": "KA-081",
        "description": "Build the chat interface where the user interacts with the AI Buyer Agent. This includes the message history, input field, and visual indicators for agent processing.",
        "tech_details": "- Create `components/ChatInterface.tsx`.\n- State management for messages `[{role: 'user'|'agent', content: string}]`.\n- Input area with a submit button.\n- Add a 'typing' indicator for when the backend is processing.",
        "ac": ["Users can type and send messages.", "Messages appear in the chat history with appropriate styling based on the sender.", "Typing indicator shows while waiting for an API response."],
        "complexity": "L"
    }
]

def generate_markdown(tickets):
    md = "# KartAgent Feature Tickets\n\n"
    md += "This document contains individual, granular feature tickets for KartAgent. Each ticket is self-contained and designed to be implemented by an AI coding agent.\n\n"
    
    components = {}
    for t in tickets:
        comp = t['component']
        if comp not in components:
            components[comp] = []
        components[comp].append(t)
        
    for comp, comp_tickets in components.items():
        md += f"## {comp}\n\n"
        for t in comp_tickets:
            md += f"### {t['id']}: {t['title']}\n"
            md += f"- **Component**: {t['component']}\n"
            md += f"- **Priority**: {t['priority']}\n"
            md += f"- **Dependencies**: {t['dependencies']}\n"
            md += f"- **Estimated Complexity**: {t['complexity']}\n\n"
            
            md += "**Description**\n\n"
            md += f"{t['description']}\n\n"
            
            md += "**Technical Details**\n\n"
            md += f"{t['tech_details']}\n\n"
            
            md += "**Acceptance Criteria**\n\n"
            for ac in t['ac']:
                md += f"- [ ] {ac}\n"
            md += "\n---\n\n"
            
    return md

content = generate_markdown(tickets)

with open(r"E:\Razorpay\docs\Feature_Tickets.md", "w", encoding="utf-8") as f:
    f.write(content)
print("File generated successfully.")
