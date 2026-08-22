import json
import os
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from backend.mcp_server import search_products, create_order, process_payment, get_product_details
from backend.mandate_enforcer import check_mandate

class BuyerAgent:
    def __init__(self, owner_id: str, session_id: str):
        self.owner_id = owner_id
        self.session_id = session_id
        self.llm = ChatGroq(model="openai/gpt-oss-20b", temperature=0.2)
        
        self.system_prompt = f"""
You are the AI Buyer Agent for user {owner_id}. Your job is to fulfill the user's purchase intent by discovering products, negotiating with merchants, and buying them securely via Razorpay.

CRITICAL RULES:
1. You CANNOT execute a purchase (`create_order` or `process_payment`) without FIRST calling `check_mandate` to ensure the price and category are allowed.
2. If `check_mandate` returns DENIED, you must stop and inform the user.
3. You should negotiate with the merchant if the price is near the budget limit.
4. If the seller explicitly states they cannot go any lower (a hard floor), DO NOT keep countering. You must either ACCEPT the offer (if it's close to your budget) or WALK_AWAY.
5. You must be transparent with the user about your reasoning and actions.

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

    def execute_purchase(self, product_id: str, final_price: float, category: str = "Electronics"):
        """Executes the actual purchase flow after negotiation succeeds."""
        # 1. Mandate Check
        mandate_result = check_mandate(self.owner_id, final_price, category)
        if mandate_result["decision"] != "APPROVED":
            return {"status": "failed", "reason": mandate_result["reason"]}
            
        # 2. Create Order
        order_result = create_order(product_id, 1, self.session_id)
        if "error" in order_result:
            return {"status": "failed", "reason": order_result["error"]}
            
        # 3. Process Payment
        pay_result = process_payment(order_result["order_id"])
        if "error" in pay_result:
            return {"status": "failed", "reason": pay_result["error"]}
            
        return {
            "status": "success", 
            "order_id": order_result["order_id"],
            "amount": final_price,
            "receipt": "Payment captured successfully on Razorpay."
        }
