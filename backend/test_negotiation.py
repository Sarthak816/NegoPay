import sys
import os
import uuid

# Ensure backend module is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.agents.negotiation_manager import NegotiationManager
from backend.mcp_server import search_products

def run_test():
    print("=== NegoPay Agent Negotiation Test ===")
    
    # 1. Simulate Buyer discovering a product
    print("\n🔍 Buyer searching for 'earbuds' under 1500...")
    results = search_products(query="earbuds", max_price=1500)
    
    if not results:
        print("No products found. (Run backend/seed.py first)")
        return
        
    product = results[0]
    print(f"Found: {product['name']} (₹{product['price']}) at {product['merchant_id']}")
    
    # 2. Start Negotiation
    print("\n🤝 Starting Negotiation...")
    session_id = f"sess_{uuid.uuid4().hex[:8]}"
    manager = NegotiationManager(
        owner_id="user_123",
        merchant_id=product["merchant_id"],
        product_id=product["id"],
        session_id=session_id
    )
    
    initial_msg = f"I want to buy {product['name']}. My absolute max budget is ₹{product['price'] * 0.8}. Can you give me a discount?"
    
    result = manager.start_negotiation(initial_msg)
    
    print("\n=== FINAL RESULT ===")
    print(f"Status: {result['status']}")
    if "purchase_result" in result:
        print(f"Purchase: {result['purchase_result']}")

if __name__ == "__main__":
    run_test()
