import json
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from backend.mcp_server import get_product_details
from backend.database import SessionLocal
from backend import models

class SellerAgent:
    def __init__(self, merchant_id: str):
        self.merchant_id = merchant_id
        self.llm = ChatOpenAI(model="gpt-4o", temperature=0.4)
        
        # Load merchant config (e.g., max discount, floor margin)
        self.config = self._load_merchant_config()
        self.max_discount = self.config.get("max_discount_percent", 10)
        
        self.system_prompt = f"""
You are the AI Seller Agent for merchant '{merchant_id}'. Your goal is to close sales while protecting margins.

CRITICAL RULES:
1. You can offer discounts to close a deal, but NEVER exceed {self.max_discount}% off the list price.
2. If the buyer asks for a discount greater than {self.max_discount}%, you must firmly reject it and counter with your best allowed price.
3. Try to upsell or highlight product features to justify the price.
4. Be polite but firm in negotiations.

Format your response exactly like this:
ACTION: [OFFER | REJECT_AND_COUNTER | ACCEPT | DEADLOCK]
PRICE: [Numeric value of your offer]
MESSAGE: [Your message to the buyer]
"""
        self.history = [SystemMessage(content=self.system_prompt)]

    def _load_merchant_config(self):
        db = SessionLocal()
        merchant = db.query(models.Merchant).filter(models.Merchant.id == self.merchant_id).first()
        db.close()
        if merchant and merchant.config_json:
            return json.loads(merchant.config_json)
        return {}

    def receive_inquiry(self, product_id: str, buyer_message: str):
        product = get_product_details(product_id)
        if "error" in product:
            return "ERROR: Product not found."
            
        list_price = product["price"]
        floor_price = list_price * (1 - (self.max_discount / 100))
        
        prompt = f"""
Buyer is inquiring about:
Product: {product['name']}
List Price: ₹{list_price}
Absolute Minimum Allowed Price (Floor): ₹{floor_price}

Buyer Message: "{buyer_message}"

Decide your response. Remember to format as:
ACTION: ...
PRICE: ...
MESSAGE: ...
"""
        self.history.append(HumanMessage(content=prompt))
        response = self.llm.invoke(self.history)
        self.history.append(response)
        
        return self._parse_response(response.content, floor_price)
        
    def _parse_response(self, content: str, floor_price: float):
        """Parses the LLM output and strictly enforces the floor price (Margin Guard)."""
        lines = content.strip().split('\n')
        action = "OFFER"
        price = 0.0
        message = ""
        
        for line in lines:
            if line.startswith("ACTION:"):
                action = line.replace("ACTION:", "").strip()
            elif line.startswith("PRICE:"):
                try:
                    price = float(line.replace("PRICE:", "").replace("₹", "").replace(",", "").strip())
                except:
                    pass
            elif line.startswith("MESSAGE:"):
                message = line.replace("MESSAGE:", "").strip()
                
        # HARD DETERMINISTIC MARGIN GUARD (No AI override)
        if price > 0 and price < floor_price:
            print(f"⚠️ MARGIN GUARD TRIGGERED: AI tried to offer ₹{price}, floor is ₹{floor_price}. Adjusting to floor.")
            price = floor_price
            action = "OFFER"
            message = f"The absolute best I can do is ₹{floor_price}. I cannot go any lower."
            
        return {
            "action": action,
            "price": price,
            "message": message,
            "raw": content
        }
