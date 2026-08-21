# NegoPay: Security and Access

This document covers the security architecture, access controls, trust boundaries, and failure recovery mechanisms for NegoPay. It is designed to ensure that AI agents operate safely within deterministic boundaries, particularly regarding financial transactions.

## 1. Security Architecture Overview

NegoPay relies on strict separation between intelligent, non-deterministic components (AI Agents) and strict, deterministic systems (Mandate Enforcer, Margin Guard, Payment Gateway).

```mermaid
flowchart TD
    subgraph Untrusted Layer
        U[Human User]
        BA[AI Buyer Agent]
        SA[AI Seller Agent]
    end

    subgraph Trusted Boundary (Deterministic)
        ME[Mandate Enforcer]
        MG[Margin Guard]
        MCP[MCP Server]
        AE[Audit Engine]
    end

    subgraph External Systems
        DB[(Local SQLite Database)]
        RZP[Razorpay API Test Mode]
    end

    U -->|Natural Language Intent| BA
    BA <-->|Negotiation Protocol| SA
    BA -->|Tool Call Request| MCP
    SA -->|Tool Call Request| MCP

    MCP -->|Check| ME
    MCP -->|Check| MG
    
    ME -->|Mandate Decision| BA
    MG -->|Margin Decision| SA

    MCP -->|Log Actions| AE
    AE --> DB

    MCP -->|Create Order / Capture Payment| RZP
    RZP -->|Webhook| MCP
```

**Trust Boundaries & Data Crossing:**
- **User Input -> Buyer Agent**: Completely untrusted. Subject to prompt injection. Handled strictly as purchase intent.
- **Buyer Agent <-> Seller Agent**: Untrusted negotiation channel. Agents cannot force actions on each other, only propose.
- **Agent -> MCP Server**: The primary trust boundary. Agents propose actions (like `create_order`), but the MCP Server validates all parameters against deterministic rules (Mandates, Margins, Inventory) before execution.
- **MCP Server -> Razorpay**: Trusted API connection secured via test-mode API keys.

## 2. Mandate System (The Core Security Layer)

The Mandate System is a deterministic (non-AI) spending control mechanism. The Buyer Agent cannot bypass it.

### 2.1 Mandate Data Model

```python
from dataclasses import dataclass
from datetime import datetime

@dataclass
class Mandate:
    id: str
    owner_id: str
    max_per_transaction: float  # Max amount for single purchase
    max_daily_spend: float  # Max total spend per day
    daily_spent: float  # Current day's spend (reset at midnight)
    allowed_categories: list[str]  # Whitelist
    blocked_categories: list[str]  # Blacklist (takes precedence)
    auto_approve_below: float  # No confirmation needed
    require_approval_above: float  # Human must approve
    max_negotiation_rounds: int  # Prevent infinite loops
    walk_away_threshold: float  # 0.0-1.0, buyer walks if price > threshold * asking
    created_at: datetime
    updated_at: datetime
```

### 2.2 Enforcement Logic (Pseudocode)

```python
from enum import Enum
from dataclasses import dataclass

class Decision(Enum):
    APPROVED = "APPROVED"
    DENIED = "DENIED"
    REQUIRES_APPROVAL = "REQUIRES_APPROVAL"

@dataclass
class MandateDecision:
    decision: Decision
    reason: str

def check_mandate(mandate: Mandate, purchase_amount: float, purchase_category: str) -> MandateDecision:
    # Step 1: Category check
    if purchase_category in mandate.blocked_categories:
        return MandateDecision(Decision.DENIED, f"Category '{purchase_category}' is blocked.")
    
    if mandate.allowed_categories and purchase_category not in mandate.allowed_categories:
        return MandateDecision(Decision.DENIED, f"Category '{purchase_category}' is not allowed.")

    # Step 2: Per-transaction limit
    if purchase_amount > mandate.max_per_transaction:
        return MandateDecision(Decision.DENIED, f"Amount {purchase_amount} exceeds per-transaction limit of {mandate.max_per_transaction}.")

    # Step 3: Daily aggregate check (including anti-splitting)
    if mandate.daily_spent + purchase_amount > mandate.max_daily_spend:
        return MandateDecision(Decision.DENIED, f"Amount {purchase_amount} would exceed daily spend limit of {mandate.max_daily_spend}.")

    # Step 4: Approval threshold
    if purchase_amount > mandate.require_approval_above:
        return MandateDecision(Decision.REQUIRES_APPROVAL, f"Amount {purchase_amount} requires human approval.")

    if purchase_amount <= mandate.auto_approve_below:
        return MandateDecision(Decision.APPROVED, "Auto-approved.")

    return MandateDecision(Decision.APPROVED, "Approved within normal limits.")
```

### 2.3 Anti-Splitting Protection
- **Detection**: The system tracks all orders in the current session and aggregates the total daily spend in the database. If an AI agent attempts to split a ₹10,000 order into ten ₹1,000 orders to bypass a ₹2,000 per-transaction limit, the `daily_spent` accumulator will catch it on the third order.
- **Implementation**: The mandate enforcer validates `daily_spent + new_amount <= max_daily_spend` on every transaction, reading from a locked database row to prevent race conditions.
- **Agent Prompts**: The Buyer Agent's system prompt explicitly prohibits splitting: "Do not attempt to split large orders into multiple smaller ones."
- **Enforcement**: The mandate enforcer validates constraints REGARDLESS of what the AI agent requests.

### 2.4 Mandate vs. Margin Guard Comparison

| Aspect | Mandate (Buyer Side) | Margin Guard (Seller Side) |
|--------|---------------------|---------------------------|
| Purpose | Protect buyer from overspending | Protect merchant from selling below cost |
| Enforcement | Deterministic rules | Deterministic rules |
| AI involvement | NONE | NONE |
| Overridable by AI | NO | NO |
| Configurable by | Human owner | Merchant admin |

## 3. Payment Security

### 3.1 Idempotency Keys
To prevent duplicate orders and double charges, an idempotency key is attached to every `create_order` call.
- **Generation**: `hash(session_id + product_id + timestamp_bucket)` (e.g., bucketed to 5-minute intervals).
- **Behavior**: If Razorpay receives a duplicate idempotency key, it returns the existing order instead of creating a new one. This prevents double charges.

```python
import hashlib
import time

def generate_idempotency_key(session_id: str, product_id: str) -> str:
    # 5-minute bucket
    time_bucket = int(time.time() / 300)
    raw_key = f"{session_id}:{product_id}:{time_bucket}"
    return hashlib.sha256(raw_key.encode()).hexdigest()
```

### 3.2 Payment Flow Security
1. **Mandate check**: System verifies `check_mandate` BEFORE order creation is requested.
2. **Order creation**: Agent requests order via MCP. MCP generates idempotency key and calls Razorpay.
3. **Payment capture**: Using test credentials, the payment is captured. The system validates the captured amount against the created order amount.
4. **Webhook verification**: System receives async confirmation. Validates Razorpay signature.
5. **Post-payment reconciliation**: Confirms final status and updates daily spend.

### 3.3 Razorpay Webhook Security
Webhooks provide authoritative payment status but must be verified.
- **Verification Algorithm**: HMAC-SHA256 of the raw request body using the webhook secret.
- **Implementation**: Use `razorpay_client.utility.verify_webhook_signature(payload_body, signature_header, webhook_secret)`.
- **Failure handling**: If signature verification fails, the request is dropped (400 Bad Request) and logged as a potential attack.
- **Replay attack prevention**: Timestamps in webhooks and idempotency tracking in our local DB prevent processing the same webhook event twice.

## 4. AI Safety & Guardrails

### 4.1 Hallucination Prevention
- **Problem**: AI agent may fabricate `product_id`s or invent features to close a deal.
- **Solution**: Every product recommendation must be validated against MCP search results from the SAME session.
- **Implementation**: The MCP Server maintains a session-scoped product cache. Any `product_id` requested by the agent that is not in the cache is rejected with a 404 Not Found error.

### 4.2 Prompt Injection Protection
- The Buyer Agent's system prompt clearly defines its boundaries: it is a buyer, not a system administrator.
- User input is treated strictly as `purchase intent`, completely segregated from system instructions.
- The agent has no MCP tools to modify its own mandate or access core system files. It can only call MCP tools defined in its specific toolset.

### 4.3 AI Boundary Enforcement

| Action | Buyer Agent | Seller Agent | Neither (System Only) |
|--------|------------|-------------|----------------------|
| Search products | ✅ | ❌ | |
| Compare products | ✅ | ❌ | |
| Negotiate price | ✅ | ✅ | |
| Suggest upsells | ❌ | ✅ | |
| Check mandate | ❌ (system does) | ❌ | ✅ |
| Modify mandate | ❌ | ❌ | ❌ (human only) |
| Create order | ❌ (requests it) | ❌ | ✅ |
| Process payment | ❌ | ❌ | ✅ |
| Set floor price | ❌ | ❌ (reads it) | ❌ (merchant only) |
| Access other sessions | ❌ | ❌ | ❌ |
| Modify audit logs | ❌ | ❌ | ❌ |

## 5. Failure Scenarios & Recovery

### 1. Infinite Negotiation Loop
- **Threat description**: Buyer and Seller agents get stuck proposing the same prices back and forth.
- **Attack vector**: Suboptimal AI generation or missing convergence logic.
- **Detection**: `round_count` in session exceeds `mandate.max_negotiation_rounds`.
- **Prevention**: The deterministic protocol engine tracks rounds.
- **Recovery**: The system forcibly terminates the negotiation (Deadlock) and notifies the user.
- **Audit**: Logs `NEGOTIATION_DEADLOCK`.
- **Implementation**: 
```python
if session.round_count >= mandate.max_negotiation_rounds:
    return DeadlockResponse("Maximum negotiation rounds reached.")
```

### 2. Hallucinated Product Purchase
- **Threat description**: Buyer agent requests to purchase `prod_fake123`.
- **Attack vector**: LLM hallucination.
- **Detection**: MCP server checks `prod_fake123` against the session cache.
- **Prevention**: Reject order creation.
- **Recovery**: Return error to agent, prompting it to search for valid products.
- **Audit**: Logs `ERROR_OCCURRED` (Product not found).
- **Implementation**:
```python
if product_id not in session.valid_product_ids:
    raise ValueError(f"Invalid product ID: {product_id}")
```

### 3. Split-Order Mandate Bypass
- **Threat description**: Agent makes multiple small purchases to avoid single-transaction limits.
- **Attack vector**: LLM misinterprets constraints or tries to be "helpful" by bypassing blocks.
- **Detection**: `daily_spent + new_amount > max_daily_spend`.
- **Prevention**: `check_mandate` fails the subsequent transactions.
- **Recovery**: Purchase is denied. User is notified.
- **Audit**: Logs `MANDATE_DENIED`.

### 4. Seller Agent Price War (Race to Bottom)
- **Threat description**: Seller agent offers items at ₹1 to close the deal.
- **Attack vector**: Flawed seller logic.
- **Detection**: Margin Guard checks `proposed_price < floor_price`.
- **Prevention**: The MCP Tool `propose_offer` raises an error if below floor price.
- **Recovery**: Offer is blocked before reaching the buyer. Seller is prompted to revise.
- **Audit**: Logs `ERROR_OCCURRED` (Margin guard violation).
- **Implementation**:
```python
if proposed_price < product.floor_price:
    raise ValueError(f"Proposed price below floor margin.")
```

### 5. Double Charge via Payment Retry
- **Threat description**: Network timeout causes agent to retry payment.
- **Attack vector**: Distributed systems failure.
- **Detection**: Razorpay detects duplicate idempotency key.
- **Prevention**: Returns existing order ID.
- **Recovery**: System syncs state with existing order and proceeds without double charging.
- **Audit**: Logs `PAYMENT_RETRIED`.

### 6. MCP Server Crash Mid-Transaction
- **Threat description**: Server dies after creating Razorpay order but before saving to DB.
- **Attack vector**: Hardware/container failure.
- **Detection**: On restart, database state is incomplete, but Razorpay webhook arrives.
- **Prevention**: Webhook processing is idempotent and can create the local order record if missing.
- **Recovery**: Webhook reconciles the state.
- **Audit**: Logs `WEBHOOK_RECEIVED`.

## 6. Data Security

### 6.1 Sensitive Data Handling
- **API Keys**: Razorpay keys (`RZP_KEY_ID`, `RZP_KEY_SECRET`) are stored in `.env` and never committed to version control.
- **Logging**: Payment IDs are logged in audit trails but masked/omitted from raw chat messages.
- **Customer Info**: Minimal PII is collected—only what's needed for order creation in test mode.

### 6.2 .gitignore Requirements
```text
.env
*.db
__pycache__/
node_modules/
.next/
```

### 6.3 Test Mode Safety
- All Razorpay operations strictly use test keys (`rzp_test_*`).
- No real money is ever transacted.
- Test card numbers (`4384796827703274`) and test UPI (`success@razorpay` / `failure@razorpay`) are documented and used exclusively.
- Clear 'TEST MODE' indicator is displayed in the UI.

## 7. Audit & Compliance

Every action taken by agents or the system is recorded to ensure full traceability and accountability.

### 7.1 Audit Event Schema
```json
{
  "event_id": "evt_uuid",
  "session_id": "sess_uuid",
  "timestamp": "2026-08-21T19:00:00Z",
  "event_type": "MANDATE_CHECK",
  "agent": "SYSTEM",
  "action": "check_per_transaction_limit",
  "input": {"amount": 1099, "limit": 2000},
  "output": {"decision": "APPROVED", "remaining": 901},
  "reasoning": "Amount ₹1,099 is within per-transaction limit of ₹2,000",
  "metadata": {"mandate_id": "mnd_123", "daily_spent_before": 0}
}
```

### 7.2 Event Types Enum
- `INTENT_PARSED`: User request understood.
- `PRODUCTS_DISCOVERED`: Search results retrieved.
- `PRODUCT_SELECTED`: Specific item chosen for negotiation/purchase.
- `NEGOTIATION_INITIATED`: Buyer contacts seller.
- `NEGOTIATION_ROUND`: Price exchange.
- `NEGOTIATION_ACCEPTED`: Agreement reached.
- `NEGOTIATION_REJECTED`: Deal refused.
- `NEGOTIATION_DEADLOCK`: Max rounds exceeded.
- `MANDATE_CHECK`: System evaluates spend limits.
- `MANDATE_APPROVED`: Spend allowed.
- `MANDATE_DENIED`: Spend blocked.
- `ORDER_CREATED`: Razorpay order generated.
- `PAYMENT_ATTEMPTED`: Capture initiated.
- `PAYMENT_CAPTURED`: Funds secured.
- `PAYMENT_FAILED`: Capture declined.
- `PAYMENT_RETRIED`: Idempotent retry.
- `QR_GENERATED`: UPI QR created.
- `WEBHOOK_RECEIVED`: Razorpay async update.
- `ERROR_OCCURRED`: General fault.
- `FALLBACK_TRIGGERED`: Graceful degradation activated.

### 7.3 Audit Trail Completeness
Every single action by every agent MUST produce at least one audit event. The audit trail for a complete purchase should tell the full story. A judge or security reviewer should be able to read the JSON audit trail and understand every decision made.

## 8. Access Control Matrix

This matrix defines exactly which entities can access specific system API endpoints.

| Endpoint | Human User | Buyer Agent | Seller Agent | System |
|----------|-----------|-------------|-------------|--------|
| `POST /api/chat` | ✅ | ❌ | ❌ | ❌ |
| `GET /api/merchants` | ✅ | ✅ (via MCP) | ❌ | ✅ |
| `PUT /api/mandates` | ✅ | ❌ | ❌ | ❌ |
| `GET /api/audit` | ✅ | ❌ | ❌ | ✅ |
| `POST /api/webhooks/razorpay` | ❌ | ❌ | ❌ | ✅ (Razorpay only) |
