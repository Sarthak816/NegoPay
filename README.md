# NegoPay: Agentic Commerce Gateway

NegoPay is a true Dual-Agent Autonomous Negotiation engine built for the Razorpay AI Buildathon (Track 1: Agentic Commerce). 

Rather than a standard single-agent chatbot, NegoPay facilitates **AI vs. AI negotiation**. A User-configured AI Buyer Agent natively negotiates pricing, terms, and discounts with a Merchant-configured AI Seller Agent. If the agents reach an agreement that falls within the user's financial mandate, NegoPay automatically triggers a Razorpay checkout.

## Architecture: Dual-Agent Protocol


`mermaid
sequenceDiagram
    actor Consumer
    participant BA as AI Buyer Agent
    participant SA as AI Seller Agent
    participant SG as Deterministic Guards
    participant RZ as Razorpay API

    Consumer->>BA: Set Mandate (Max Budget: ₹5,000)
    Note over BA, SA: LANP (Lightweight Agent Negotiation Protocol)
    BA->>SA: [OFFER] I want to buy this for ₹4,000
    SA->>SG: Check Floor Price (Margin Guard)
    SG-->>SA: Approved (Above Floor)
    SA->>BA: [COUNTER] I can do ₹4,500
    BA->>SA: [ACCEPT] ₹4,500 agreed
    
    Note over BA, SG: Pre-Transaction Verification
    BA->>SG: Verify Mandate (₹4,500 vs ₹5,000 limits)
    SG-->>BA: Mandate Verified (Idempotency Key Generated)
    BA->>RZ: create_order()
    RZ-->>Consumer: Autonomous Checkout Modal Initiated
`

NegoPay replaces traditional cart-based checkouts with an Agent Commerce Protocol (ACP). 
We implemented a Lightweight Agent Negotiation Protocol (LANP) utilizing structured syntaxes (`[COUNTER]`, `[ACCEPT]`) to allow rapid, sub-2-second negotiation loops over WebSockets.

### 1. The AI Buyer Agent
Configured by the consumer. It is aware of the user's maximum budget and strict daily spending limits. It analyzes the merchant's initial offer and counter-offers strategically to achieve the lowest possible price.

### 2. The AI Seller Agent
Configured by the merchant. It possesses private knowledge of product floor prices and maximum discount thresholds. It negotiates aggressively to maintain margins while attempting to close the sale.

---

## Enterprise-Grade AI Safety & Deterministic Guards

The biggest risk in Agentic Commerce is Prompt Injection (e.g., instructing an AI to sell a high-value item for a fraction of its cost). NegoPay solves this entirely by utilizing **Deterministic Mathematical Guards** that sit strictly outside the LLM execution environment. 

### Mandate Enforcer (Buyer-Side Guard)
Before any payment is executed, the `mandate_enforcer.py` intercepts the AI's decision and validates it against the user's database-level constraints:
* **Max Per-Transaction Limit:** The AI cannot authorize a payment exceeding a strictly defined cap.
* **Max Daily Spend Limit:** The engine aggregates the user's rolling 24-hour spend and explicitly blocks the transaction if the daily limit is breached.
* **Auto-Approve Thresholds:** NegoPay features a Hybrid Checkout. If the negotiated price falls below a safe auto-approve threshold, the system autonomously opens the Razorpay modal. If it requires manual review, the transaction is halted and flagged for human approval.

### Margin Guard (Seller-Side Guard)
The seller agent cannot be tricked. Even if the LLM hallucinates or is subjected to prompt injection, the negotiation engine cross-references the final agreed price against the database's strict `floor_price_margin`. If the AI agrees to a price below the floor, the system intercepts and hard-declines the transaction.

### Payment Idempotency
To prevent double-charging during network timeouts or agent hallucinations, every order creation utilizes a strict `Idempotency-Key` deterministically derived from the negotiation session and product ID. 

---

## Tech Stack

* **Backend:** Python, FastAPI, WebSockets
* **Frontend:** Next.js, React, Tailwind CSS (Glassmorphic minimalist UI)
* **AI/LLM:** Groq API (Llama 3) for sub-second inference
* **Database:** Serverless PostgreSQL (Neon) via SQLAlchemy
* **Payments:** Razorpay Python SDK

---

## Local Setup Instructions

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Sarthak816/NegoPay.git
   cd NegoPay
   ```

2. **Configure Environment Variables:**
   Create a `.env` file in the root directory and add your keys:
   ```env
   GROQ_API_KEY=your_groq_key
   RAZORPAY_KEY_ID=your_razorpay_key
   RAZORPAY_KEY_SECRET=your_razorpay_secret
   DATABASE_URL=your_postgres_url
   ```

3. **Start the FastAPI Backend:**
   ```bash
   pip install -r backend/requirements.txt
   uvicorn backend.main:app --reload --port 8000
   ```

4. **Start the Next.js Frontend:**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

5. **Access the Application:**
   Open `http://localhost:3000` in your browser.

## Testing & Automation
NegoPay includes an automated test suite to mathematically prove the integrity of the Mandate Enforcer. Run the tests using `pytest`:
```bash
pytest tests/test_mandate.py
```
