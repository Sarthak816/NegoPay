import time
import uuid
from backend.agents.buyer_agent import BuyerAgent
from backend.agents.seller_agent import SellerAgent
from backend.database import SessionLocal
from backend import models

class NegotiationManager:
    def __init__(self, owner_id: str, merchant_id: str, product_id: str, session_id: str):
        self.buyer = BuyerAgent(owner_id, session_id)
        self.seller = SellerAgent(merchant_id)
        self.product_id = product_id
        self.max_rounds = 5
        self.transcript = []
        self.audit_trail = []
        
        # Init DB Session
        self.db = SessionLocal()
        self.neg_session = models.NegotiationSession(
            id=f"neg_{uuid.uuid4().hex[:8]}",
            buyer_agent_id=owner_id,
            seller_agent_id=merchant_id,
            product_id=product_id,
            status="INITIATED"
        )
        self.db.add(self.neg_session)
        self.db.commit()

    def start_negotiation(self, initial_buyer_message: str):
        self.audit_trail.append({"type": "SYSTEM", "detail": f"[MCP Call] Discovery phase initiated. Target: {self.product_id}"})
        self.transcript.append({"sender": "BUYER", "message": initial_buyer_message})
        print(f"\n[Round 1] BUYER: {initial_buyer_message}")
        
        seller_response = self.seller.receive_inquiry(self.product_id, initial_buyer_message)
        
        self.neg_session.initial_price = seller_response["price"]
        self.db.commit()
        
        return self._loop(seller_response, round_num=1)
        
    def _loop(self, last_seller_response, round_num: int):
        while round_num <= self.max_rounds:
            self.audit_trail.append({"type": "AGENT", "detail": f"Negotiation Round {round_num}/{self.max_rounds} completed."})
            print(f"[Round {round_num}] SELLER ({last_seller_response['action']} - ₹{last_seller_response['price']}): {last_seller_response['message']}")
            self.transcript.append({
                "sender": "SELLER", 
                "action": last_seller_response["action"],
                "price": last_seller_response["price"],
                "message": last_seller_response["message"]
            })
            
            if last_seller_response["action"] == "DEADLOCK":
                self.audit_trail.append({"type": "FAILURE", "detail": "[System] Seller invoked DEADLOCK. Terminating."})
                self._close_session("DEADLOCK")
                return {"status": "DEADLOCK", "transcript": self.transcript, "audit_trail": self.audit_trail}
                
            # Buyer's turn to evaluate
            buyer_raw = self.buyer.evaluate_offer(self.product_id, last_seller_response["price"], last_seller_response["message"])
            buyer_action, buyer_msg = self._parse_buyer_response(buyer_raw)
            
            print(f"[Round {round_num}] BUYER ({buyer_action}): {buyer_msg}")
            self.transcript.append({"sender": "BUYER", "action": buyer_action, "message": buyer_msg})
            
            if buyer_action == "ACCEPT":
                self.audit_trail.append({"type": "SUCCESS", "detail": f"[System] Buyer accepted offer at ₹{last_seller_response['price']}."})
                print(f"\n DEAL REACHED at ₹{last_seller_response['price']}!")
                
                # Execute purchase
                purchase_result = self.buyer.execute_purchase(self.product_id, last_seller_response["price"], self.audit_trail)
                
                status_string = "ACCEPTED"
                if purchase_result.get("status") == "requires_approval":
                    status_string = "REQUIRES_APPROVAL"
                elif purchase_result.get("status") == "failed":
                    status_string = "FAILED"
                    
                self._close_session(status_string, final_price=last_seller_response["price"])
                
                return {
                    "status": status_string,
                    "final_price": last_seller_response["price"],
                    "purchase_result": purchase_result,
                    "transcript": self.transcript,
                    "audit_trail": self.audit_trail
                }
                
            if buyer_action == "WALK_AWAY":
                self.audit_trail.append({"type": "SYSTEM", "detail": "[System] Buyer invoked WALK_AWAY. Deal collapsed."})
                print(f"\n BUYER WALKED AWAY.")
                self._close_session("REJECTED")
                return {"status": "WALK_AWAY", "transcript": self.transcript, "audit_trail": self.audit_trail}
                
            # Seller's turn to respond to counter
            round_num += 1
            if round_num > self.max_rounds:
                break
                
            last_seller_response = self.seller.receive_inquiry(self.product_id, buyer_msg)
            time.sleep(1) # Small pause for log readability
            
        self.audit_trail.append({"type": "FAILURE", "detail": "[System] Max negotiation rounds reached. DEADLOCK enforced."})
        print("\n MAX ROUNDS REACHED. DEADLOCK.")
        self._close_session("DEADLOCK")
        return {"status": "DEADLOCK", "transcript": self.transcript, "audit_trail": self.audit_trail}

    def _parse_buyer_response(self, content: str):
        lines = content.strip().split('\n')
        action = "COUNTER"
        message = ""
        for line in lines:
            if line.startswith("ACTION:"):
                action = line.replace("ACTION:", "").strip()
            elif line.startswith("MESSAGE:"):
                message = line.replace("MESSAGE:", "").strip()
        return action, message
        
    def _close_session(self, status: str, final_price: float = None):
        self.neg_session.status = status
        if final_price:
            self.neg_session.final_price = final_price
        self.db.commit()
        self.db.close()
