import json
import os
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from backend.mcp_server import search_products, create_order, process_payment, get_product_details
from backend.mandate_enforcer import check_mandate
from backend.database import SessionLocal
from backend import models

def _get_mandate(owner_id: str):
    db = SessionLocal()
    mandate = db.query(models.Mandate).filter(models.Mandate.owner_id == owner_id).first()
    db.close()
    return mandate

class BuyerAgent:
    def __init__(self, owner_id: str, session_id: str):
        self.owner_id = owner_id
        self.session_id = session_id
        self.llm = ChatGroq(model="openai/gpt-oss-20b", temperature=0.2)
        
        # Load deterministic mandate
        mandate = _get_mandate(owner_id)
        max_spend = mandate.max_per_transaction if mandate else 2000.0
        
        self.system_prompt = f"""
You are an AUTONOMOUS AI Buyer Agent acting on behalf of user {owner_id}.
Your job is to discover products, negotiate, and execute purchases entirely on your own.

YOUR DETERMINISTIC BUDGET:
- Your hard max limit per transaction is: ₹{max_spend}.
- You CANNOT exceed this under any circumstances.

CRITICAL RULES:
1. YOU ARE FULLY AUTONOMOUS. Do NOT ask the user for permission, budget confirmations, or clarifications during the negotiation.
2. Make decisions independently. If an offer is good and under ₹{max_spend}, ACCEPT it.
3. If an offer exceeds ₹{max_spend} and the seller refuses to go lower, you must WALK_AWAY.
4. You CANNOT execute a purchase without FIRST calling `check_mandate` to ensure the system allows it.
5. If `check_mandate` returns DENIED, you must stop and WALK_AWAY.

When you decide to buy, your final steps are ALWAYS:
1. check_mandate(amount, category)
2. create_order(product_id, quantity)
3. process_payment(order_id)
"""
        self.history = [SystemMessage(content=self.system_prompt)]

    def handle_user_intent(self, user_intent: str):
        """Parse user intent and search for products."""
        self.history.append(HumanMessage(content=user_intent))
        
        # Tools available to the buyer at the discovery stage
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "search_products",
                    "description": "Search the marketplace for products.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string"},
                            "max_price": {"type": "number"},
                            "category": {"type": "string"}
                        }
                    }
                }
            }
        ]
        
        response = self.llm.invoke(self.history, tools=tools)
        self.history.append(response)
        
        if response.tool_calls:
            # For simplicity in this demo, we auto-execute the search tool
            for tool_call in response.tool_calls:
                if tool_call["name"] == "search_products":
                    args = tool_call["args"]
                    results = search_products(**args)
                    self.history.append(SystemMessage(content=f"Search Results: {json.dumps(results)}"))
            
            # Get the LLM to process the search results
            response = self.llm.invoke(self.history)
            self.history.append(response)
            
        return response.content

    def evaluate_offer(self, product_id: str, offer_price: float, merchant_message: str):
        """Called during negotiation when the seller agent makes an offer."""
        prompt = f"""
The merchant has made an offer:
Product ID: {product_id}
Offered Price: ₹{offer_price}
Merchant Message: "{merchant_message}"

Respond with your next action. You can either:
1. Accept the offer (if it fits the user's budget and is a good deal).
2. Counter-offer (ask for a lower price or bundle).
3. Walk away (if it's too expensive).

Format your response exactly like this:
ACTION: [ACCEPT | COUNTER | WALK_AWAY]
MESSAGE: [Your message to the merchant]
"""
        self.history.append(SystemMessage(content=prompt))
        response = self.llm.invoke(self.history)
        self.history.append(response)
        return response.content

    def execute_purchase(self, product_id: str, final_price: float, audit_trail: list, category: str = "Electronics"):
        """Executes the actual purchase flow after negotiation succeeds."""
        # 1. Mandate Check
        audit_trail.append({"type": "SYSTEM", "detail": f"[Mandate Check] Evaluating {final_price} against limits."})
        mandate_result = check_mandate(self.owner_id, final_price, category)
        
        if mandate_result["decision"] == "REQUIRES_APPROVAL":
            audit_trail.append({"type": "FAILURE", "detail": f"[Mandate Blocked] {mandate_result['reason']}"})
            return {"status": "requires_approval", "reason": mandate_result["reason"]}
            
        if mandate_result["decision"] != "APPROVED":
            audit_trail.append({"type": "FAILURE", "detail": f"[Mandate Rejected] {mandate_result['reason']}"})
            return {"status": "failed", "reason": mandate_result["reason"]}
            
        audit_trail.append({"type": "SUCCESS", "detail": "[Mandate Approved] Limits verified."})
        
        # 2. Create Order
        audit_trail.append({"type": "API_CALL", "detail": f"[Razorpay API] Calling create_order({product_id}, qty=1, price={final_price})"})
        order_result = create_order(product_id, 1, self.session_id, agreed_price=final_price)
        if "error" in order_result:
            audit_trail.append({"type": "FAILURE", "detail": f"[Razorpay API Error] {order_result['error']}"})
            return {"status": "failed", "reason": order_result["error"]}
            
        audit_trail.append({"type": "SUCCESS", "detail": f"[Razorpay API] Order Created: {order_result['razorpay_order_id']}"})
            
        # 3. Process Payment
        audit_trail.append({"type": "API_CALL", "detail": f"[Razorpay API] Processing payment for {order_result['razorpay_order_id']}"})
        pay_result = process_payment(order_result["order_id"]) # Uses internal ID for mock process_payment
        if "error" in pay_result:
            audit_trail.append({"type": "FAILURE", "detail": f"[Razorpay API Error] {pay_result['error']}"})
            return {"status": "failed", "reason": pay_result["error"]}
            
        audit_trail.append({"type": "SUCCESS", "detail": f"[Razorpay API] Payment Captured: {pay_result.get('payment_id', 'mocked')}"})
            
        return {
            "status": "success", 
            "order_id": order_result["razorpay_order_id"],
            "amount": final_price,
            "receipt": "Payment captured successfully on Razorpay."
        }
