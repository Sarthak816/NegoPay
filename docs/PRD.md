# Product Requirements Document (PRD): NegoPay

## 1. Product Vision & Objective

**What NegoPay is:**
NegoPay is an MCP-powered merchant gateway and AI buyer/seller agent system that makes any Razorpay merchant AI-transactable, end-to-end. It provides a standardized framework where AI buyer agents can discover products, negotiate with AI seller agents, adhere to strict human-configured spending mandates, and execute transactions using Razorpay's infrastructure.

**The problem it solves:**
Currently, AI agents excel at researching and comparing products across the web but fail at the "last mile"—executing the purchase. They cannot securely handle payments, negotiate dynamic deals, or interact with merchant catalogs in a machine-readable way. NegoPay bridges this gap by providing an Agentic Commerce Protocol (ACP) via Model Context Protocol (MCP), enabling true agent-to-agent commerce.

**Target context:**
Razorpay AI Buildathon (Track 01: AI Growth & Agentic Commerce).

**Success metric:**
A fully working, reliable demo showing an AI Buyer Agent and AI Seller Agent discovering a product, negotiating a price, respecting spending constraints, and successfully settling money on Razorpay (test mode) with comprehensive audit logs and failure recovery.

## 2. Target Users

- **Primary:** Razorpay buildathon judges evaluating the project based on problem taste, build quality, AI judgment (understanding where AI is useful vs. where deterministic logic is needed), and failure recovery.
- **Secondary:** Merchants who want to open their storefronts to the emerging economy of AI agents, allowing discovery, dynamic pricing, and automated sales.
- **Tertiary:** Developers building AI buyer agents who need a standardized payment rail and catalog access protocol (MCP) to make their agents transactional.

## 3. User Stories

### Buyer Agent Stories
1. **As a Buyer Agent**, I want to search for products across multiple merchants so that I can find the best match for my user's request.
2. **As a Buyer Agent**, I want to retrieve detailed product specifications to accurately compare items.
3. **As a Buyer Agent**, I want to check real-time inventory to ensure the product is available before attempting to buy.
4. **As a Buyer Agent**, I want to request a negotiation with a Seller Agent to secure a better price for my user.
5. **As a Buyer Agent**, I want to automatically retry or fall back to alternatives if a payment fails or inventory runs out during checkout.

### Seller Agent Stories
6. **As a Seller Agent**, I want to receive incoming purchase requests in a structured format so I can evaluate the buyer's intent.
7. **As a Seller Agent**, I want to offer dynamic discounts within my configured margin guards to close a sale without losing money.
8. **As a Seller Agent**, I want to suggest relevant upsells or bundles during negotiation to increase the Average Order Value (AOV).
9. **As a Seller Agent**, I want to automatically reject offers that fall below my Floor Price (walk-away threshold).

### Merchant Stories
10. **As a Merchant**, I want to expose my product catalog via an MCP Server so AI agents can natively interact with my store.
11. **As a Merchant**, I want to configure the margin guards and personality of my Seller Agent so it represents my brand and profitability goals.
12. **As a Merchant**, I want to view an analytics dashboard of agent-to-agent negotiations to understand demand and pricing elasticity.

### Human Owner (Buyer) Stories
13. **As a Human Owner**, I want to set strict spending mandates (e.g., max $100 per transaction, $500 daily limit) so my agent cannot bankrupt me.
14. **As a Human Owner**, I want to require manual approval for purchases above a certain threshold or in specific categories.
15. **As a Human Owner**, I want to view a transparent audit trail of every action my agent took, including search queries, negotiation logs, and mandate checks.

### System Stories
16. **As the System**, I want to enforce deterministic mandate checks before any payment is initiated to guarantee financial safety.
17. **As the System**, I want to use idempotency keys for all Razorpay API calls to prevent double-charging in case of network timeouts.
18. **As the System**, I want to log every tool call, negotiation round, and state change as structured JSON for observability and debugging.
19. **As the System**, I want to gracefully handle webhooks for payment status updates to keep the local database in sync with Razorpay.

## 4. Scope Definition

### In Scope (MVP):
- **Mock Merchants:** 2-3 merchants with 30-50 products each across 5 categories (Electronics, Books, Clothing, Home, Sports).
- **Merchant MCP Server:** 8 core tools (`search_products`, `get_product_details`, `check_inventory`, `create_order`, `process_payment`, `generate_qr`, `get_order_status`, `request_negotiation`).
- **AI Buyer Agent:** Capable of intent parsing, multi-merchant discovery, and mandate enforcement.
- **AI Seller Agent:** Capable of handling requests, margin guards, and generating upsells.
- **Agent-to-agent negotiation:** Structured protocol with a maximum of 5 rounds.
- **Multi-merchant discovery:** Buyer can query 2-3 merchants simultaneously.
- **Razorpay Integration:** Test-mode integrations for Orders, Payments, and Webhooks.
- **Audit Trail:** Structured JSON logging for all activities.
- **Frontend Dashboard:** React/Next.js UI with a split view (chat on left, real-time activity feed, audit trail, and mandate panel on right).
- **Failure Recovery:** 6 specific failure scenarios handled gracefully (e.g., payment timeout, mandate violation, inventory exhaustion, negotiation breakdown).

### Out of Scope:
- Real payment processing (strictly Razorpay test mode).
- User authentication/login systems (OAuth, JWT, etc.).
- Real product inventory management (integration with Shopify/WooCommerce).
- Production deployment (Docker Compose for local execution is sufficient).
- Mobile application.

## 5. Functional Requirements

### MCP Server
- **FR-001 [P0]:** Expose `search_products(query, filters)` tool to query SQLite DB.
- **FR-002 [P0]:** Expose `get_product_details(product_id)` tool.
- **FR-003 [P0]:** Expose `check_inventory(product_id)` tool.
- **FR-004 [P0]:** Expose `request_negotiation(product_id, offer_price)` tool.
- **FR-005 [P0]:** Expose `create_order(product_id, final_price)` tool to generate a Razorpay Order ID.
- **FR-006 [P0]:** Expose `process_payment(order_id, payment_details)` tool using Razorpay test cards.
- **FR-007 [P1]:** Expose `generate_qr(order_id)` tool for UPI test payments.
- **FR-008 [P1]:** Expose `get_order_status(order_id)` tool.

### Buyer Agent
- **FR-009 [P0]:** Parse natural language user intent into structured search queries.
- **FR-010 [P0]:** Call MCP tools across multiple mock merchants to compare products.
- **FR-011 [P0]:** Execute negotiation strategy based on user's target price and BATNA.

### Seller Agent
- **FR-012 [P0]:** Evaluate buyer offers against deterministic `Floor Price`.
- **FR-013 [P1]:** Generate context-aware upsell or bundle offers during negotiation.

### Negotiation Protocol
- **FR-014 [P0]:** Enforce a strict maximum of 5 negotiation rounds per session.
- **FR-015 [P0]:** Return structured accept/reject/counter-offer payloads.

### Mandate System
- **FR-016 [P0]:** Deterministically check `per_transaction_limit` before calling `process_payment`.
- **FR-017 [P0]:** Deterministically check `daily_aggregate_limit` before calling `process_payment`.
- **FR-018 [P0]:** Block transactions in restricted categories (e.g., Weapons, Alcohol).

### Audit Trail
- **FR-019 [P0]:** Log every MCP tool call request and response as JSON.
- **FR-020 [P0]:** Log mandate evaluation results (Pass/Fail + reason).

### Frontend
- **FR-021 [P0]:** Split-screen UI: Chat interface (left) and Agent Activity Feed (right).
- **FR-022 [P0]:** Real-time display of negotiation rounds and tool execution.

### Razorpay Integration
- **FR-023 [P0]:** Create Orders via Razorpay Python SDK.
- **FR-024 [P0]:** Capture test payments via Razorpay API.
- **FR-025 [P1]:** Handle Razorpay Webhooks (`payment.captured`, `payment.failed`) to update SQLite DB.

## 6. Non-Functional Requirements

- **Performance:** End-to-end negotiation (up to 5 rounds) must complete in under 10 seconds.
- **Reliability:** Every payment-related API call (Order creation, Payment capture) MUST include an Idempotency Key to prevent double charges on retries.
- **Observability:** All actions (LLM calls, tool executions, mandate checks) must be logged with a high-resolution timestamp and trace ID.
- **Testability:** 
  - Unit tests for Mandate System (deterministic logic).
  - Integration tests for all MCP tools.
- **Portability:** Entire system must run locally via `docker-compose up` without complex external dependencies (besides Razorpay API keys and LLM keys).

## 7. Success Criteria (Buildathon-Specific)

- **Problem Taste (25%):** NegoPay directly addresses the "last mile" problem of AI agents—executing transactions safely. The architecture perfectly aligns with Razorpay's agentic commerce vision.
- **Build Quality (25%):** Clean repository structure, comprehensive documentation (README, PRD), Docker Compose setup for easy evaluation, and sufficient test coverage.
- **AI Judgment (25%):** Clear separation of concerns. AI is used for intent, strategy, and parsing (load-bearing). Deterministic code is used for mandate enforcement, margin guards, and payment execution (money handling).
- **Failure Recovery (25%):** The system gracefully handles and documents 6 specific failures:
  1. Insufficient funds / Mandate violation (Agent explains issue to user).
  2. Inventory exhaustion mid-negotiation (Agent finds alternative).
  3. Negotiation breakdown (Agent walks away and searches elsewhere).
  4. Payment timeout (System retries with idempotency key).
  5. API rate limiting (Exponential backoff implemented).
  6. Invalid MCP tool arguments (Agent auto-corrects based on schema error).

## 8. Key Decisions Log

- **Why MCP over REST?**
  MCP (Model Context Protocol) is natively designed for LLMs. It provides built-in schema discovery, allowing the Buyer Agent to understand the Seller's capabilities dynamically without hardcoding API specs.
- **Why mandate enforcement is deterministic (not AI)?**
  Financial safety cannot rely on probabilistic models. LLMs can be prompt-injected or hallucinate. Mandate limits and margin guards MUST be standard `if/else` logic in Python.
- **Why SQLite over Postgres?**
  For a hackathon demo, zero-setup is crucial. SQLite provides sufficient relational features and ACID compliance without requiring judges to install or configure a database server.
- **Why LangGraph vs raw function calling?**
  LangGraph provides state persistence, cyclicity (crucial for multi-round negotiation), and observability (checkpointing), making it superior for multi-agent workflows compared to raw API loops.
- **Why two agents (buyer + seller) instead of just buyer?**
  A single buyer agent accessing a static API is just automation. Two agents negotiating dynamically represent true "Agentic Commerce," where price and bundles are fluid based on context.

## 9. Glossary

- **MCP (Model Context Protocol):** An open standard for connecting AI models to data sources and tools.
- **UAP (Universal Agentic Protocol):** A conceptual framework for how agents should interact.
- **ACP (Agentic Commerce Protocol):** NegoPay's specific implementation of MCP tailored for discovery, negotiation, and purchasing.
- **BATNA:** Best Alternative to a Negotiated Agreement. The buyer agent's fallback option if the current negotiation fails.
- **Mandate:** Human-configured rules dictating spending limits and allowed categories for the Buyer Agent.
- **Margin Guard:** A deterministic constraint set by the Merchant defining the absolute minimum price (Floor Price) the Seller Agent can accept.
- **Idempotency Key:** A unique identifier sent with payment requests to ensure the operation is only processed once, even if retried.
- **Floor Price:** The lowest acceptable price for a product, below which the Seller Agent will immediately reject the offer (walk-away threshold).
- **Walk-away Threshold:** The point at which either the buyer or seller terminates the negotiation due to irreconcilable price differences.
