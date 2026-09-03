import time
import asyncio
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

    async def stream_negotiation(self, initial_buyer_message: str):
        def add_audit(t, d):
            import time
            log = {"type": t, "detail": d, "timestamp": time.strftime("%I:%M:%S %p").lower()}
            self.audit_trail.append(log)
            return {"type": "audit", "log": log}
            
        def add_chat(sender, msg, action=None, price=None):
            turn = {"sender": sender, "message": msg, "action": action, "price": price}
            self.transcript.append(turn)
            return {"type": "chat", "turn": turn}

        yield add_audit("SYSTEM", f"[MCP Call] Discovery phase initiated. Target: {self.product_id}")
        await asyncio.sleep(0.5)
        
        yield add_chat("BUYER", initial_buyer_message)
        self.buyer.inject_user_instruction(initial_buyer_message)
        
        seller_response = await self.seller.receive_inquiry(self.product_id, initial_buyer_message)
        self.neg_session.initial_price = seller_response["price"]
        self.db.commit()
        
        round_num = 1
        last_seller_response = seller_response
        
        while round_num <= self.max_rounds:
            await asyncio.sleep(1.5) # Theatrical delay for reading
            yield add_chat("SELLER", last_seller_response["message"], last_seller_response["action"], last_seller_response["price"])
            yield add_audit("AGENT", f"Negotiation Round {round_num}/{self.max_rounds} completed.")
            
            if last_seller_response["action"] == "DEADLOCK":
                await asyncio.sleep(0.5)
                yield add_audit("FAILURE", "[System] Seller invoked DEADLOCK. Terminating.")
                self._close_session("DEADLOCK")
                yield {"type": "status", "status": "DEADLOCK", "final_price": None, "purchase_result": None}
                return
                
            if last_seller_response["action"] == "ACCEPT":
                await asyncio.sleep(0.8) # Let user read the chat before log appears
                yield add_audit("SUCCESS", f"[System] Seller accepted buyer's offer at ₹{last_seller_response['price']}.")
                
                pre_len = len(self.audit_trail)
                purchase_result = self.buyer.execute_purchase(self.product_id, last_seller_response["price"], self.audit_trail)
                
                for log in self.audit_trail[pre_len:]:
                    yield {"type": "audit", "log": log}
                
                status_string = "ACCEPTED"
                if purchase_result.get("status") == "requires_approval":
                    status_string = "REQUIRES_APPROVAL"
                elif purchase_result.get("status") == "failed":
                    status_string = "FAILED"
                    
                self._close_session(status_string, final_price=last_seller_response["price"])
                
                yield {
                    "type": "status",
                    "status": status_string,
                    "final_price": last_seller_response["price"],
                    "purchase_result": purchase_result
                }
                return
                
            # Buyer's turn to evaluate
            buyer_raw = await self.buyer.evaluate_offer(self.product_id, last_seller_response["price"], last_seller_response["message"])
            buyer_action, buyer_msg = self._parse_buyer_response(buyer_raw)
            
            await asyncio.sleep(1.5) # Theatrical delay for reading
            yield add_chat("BUYER", buyer_msg, buyer_action)
            
            if buyer_action == "ACCEPT":
                await asyncio.sleep(0.8) # Let user read the chat before log appears
                yield add_audit("SUCCESS", f"[System] Buyer accepted offer at ₹{last_seller_response['price']}.")
                
                # Execute purchase and grab pre-purchase trail length
                pre_len = len(self.audit_trail)
                purchase_result = self.buyer.execute_purchase(self.product_id, last_seller_response["price"], self.audit_trail)
                
                # Yield any new logs appended by execute_purchase
                for log in self.audit_trail[pre_len:]:
                    yield {"type": "audit", "log": log}
                
                status_string = "ACCEPTED"
                if purchase_result.get("status") == "requires_approval":
                    status_string = "REQUIRES_APPROVAL"
                elif purchase_result.get("status") == "failed":
                    status_string = "FAILED"
                    
                self._close_session(status_string, final_price=last_seller_response["price"])
                
                yield {
                    "type": "status",
                    "status": status_string,
                    "final_price": last_seller_response["price"],
                    "purchase_result": purchase_result
                }
                return
                
            if buyer_action == "WALK_AWAY":
                yield add_audit("SYSTEM", "[System] Buyer invoked WALK_AWAY. Deal collapsed.")
                self._close_session("REJECTED")
                yield {"type": "status", "status": "WALK_AWAY", "final_price": None, "purchase_result": None}
                return
                
            # Seller's turn to respond to counter
            round_num += 1
            if round_num > self.max_rounds:
                break
                
            last_seller_response = await self.seller.receive_inquiry(self.product_id, buyer_msg)
            
        yield add_audit("FAILURE", "[System] Max negotiation rounds reached. DEADLOCK enforced.")
        self._close_session("DEADLOCK")
        yield {"type": "status", "status": "DEADLOCK", "final_price": None, "purchase_result": None}

    def _parse_buyer_response(self, content: str):
        import re
        action = "COUNTER"
        message = content.strip()
        
        action_match = re.search(r"ACTION:\s*([^\n]+)", content)
        if action_match:
            action = action_match.group(1).replace("[", "").replace("]", "").strip()
            
        if "MESSAGE:" in content:
            message = content.split("MESSAGE:")[1].strip()
            
        return action, message
        
    def _close_session(self, status: str, final_price: float = None):
        self.neg_session.status = status
        if final_price:
            self.neg_session.final_price = final_price
        self.db.commit()
        self.db.close()
