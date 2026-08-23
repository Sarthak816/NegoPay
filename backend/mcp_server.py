import json
import uuid
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from backend.database import SessionLocal
from backend import models
from backend import razorpay_client

# Note: We implement these as raw functions that can be exposed via MCP 
# or directly called by our LangGraph agents for simplicity in the buildathon.

def _get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def search_products(query: str = "", max_price: float = None, category: str = None) -> List[Dict[str, Any]]:
    """Search for products based on query, price, and category."""
    db = next(_get_db())
    qs = db.query(models.Product)
    
    if query:
        qs = qs.filter(models.Product.name.ilike(f"%{query}%") | models.Product.description.ilike(f"%{query}%"))
    if max_price is not None:
        qs = qs.filter(models.Product.price <= max_price)
    if category:
        qs = qs.filter(models.Product.category.ilike(f"%{category}%"))
        
    products = qs.all()
    return [{"id": p.id, "name": p.name, "price": p.price, "merchant_id": p.merchant_id, "stock": p.stock, "category": p.category} for p in products]

def get_product_details(product_id: str) -> Dict[str, Any]:
    """Get full details of a specific product."""
    db = next(_get_db())
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not product:
        return {"error": "Product not found"}
    return {
        "id": product.id,
        "name": product.name,
        "description": product.description,
        "price": product.price,
        "merchant_id": product.merchant_id,
        "stock": product.stock,
        "category": product.category,
        "tags": json.loads(product.tags) if product.tags else []
    }

def check_inventory(product_id: str, quantity: int) -> Dict[str, Any]:
    """Check if a product has enough stock."""
    db = next(_get_db())
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not product:
        return {"error": "Product not found"}
    
    available = product.stock >= quantity
    return {
        "product_id": product.id,
        "requested": quantity,
        "available_stock": product.stock,
        "is_sufficient": available
    }

def create_order(product_id: str, quantity: int, session_id: str, agreed_price: float = None) -> Dict[str, Any]:
    """Creates an order on Razorpay and stores it in the database."""
    db = next(_get_db())
    
    # 1. Check product
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not product:
        return {"error": "Product not found"}
    if product.stock < quantity:
        return {"error": "Insufficient stock"}
        
    # 2. Generate Idempotency Key
    idempotency_key = f"idem_{session_id}_{product_id}_{uuid.uuid4().hex[:8]}"
    
    # Check if already exists
    existing = db.query(models.Order).filter(models.Order.idempotency_key == idempotency_key).first()
    if existing:
        return {"order_id": existing.id, "razorpay_order_id": existing.razorpay_order_id, "amount": existing.amount, "status": existing.status}
        
    unit_price = agreed_price if agreed_price is not None else product.price
    total_amount = unit_price * quantity
    db_order_id = f"ord_internal_{uuid.uuid4().hex[:8]}"
    
    # 3. Create Razorpay Order
    try:
        rp_order = razorpay_client.create_order(
            amount_inr=total_amount,
            receipt=db_order_id,
            notes={"product_id": product_id, "quantity": quantity}
        )
    except Exception as e:
        return {"error": f"Razorpay API Error: {str(e)}"}
        
    # 4. Save to DB
    new_order = models.Order(
        id=db_order_id,
        razorpay_order_id=rp_order["id"],
        product_id=product.id,
        merchant_id=product.merchant_id,
        quantity=quantity,
        amount=total_amount,
        status="CREATED",
        idempotency_key=idempotency_key
    )
    db.add(new_order)
    
    # Decrement stock temporarily (simulate reservation)
    product.stock -= quantity
    
    db.commit()
    
    return {
        "order_id": new_order.id,
        "razorpay_order_id": new_order.razorpay_order_id,
        "amount": new_order.amount,
        "status": new_order.status
    }

def process_payment(order_id: str) -> Dict[str, Any]:
    """
    Simulates successful payment capture for test mode. 
    In real flow, frontend sends token. Here we simulate success.
    """
    db = next(_get_db())
    order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if not order:
        return {"error": "Order not found"}
        
    if order.status == "PAID":
        return {"status": "already_paid", "order_id": order_id}
        
    payment_id = f"pay_mock_{uuid.uuid4().hex[:8]}"
    
    payment = models.Payment(
        id=payment_id,
        order_id=order.id,
        razorpay_payment_id=payment_id,
        amount=order.amount,
        status="CAPTURED",
        method="upi"
    )
    order.status = "PAID"
    
    db.add(payment)
    db.commit()
    
    return {
        "status": "success",
        "payment_id": payment_id,
        "order_id": order_id,
        "amount": order.amount
    }

def get_order_status(order_id: str) -> Dict[str, Any]:
    db = next(_get_db())
    order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if not order:
        return {"error": "Order not found"}
    return {
        "order_id": order.id,
        "razorpay_order_id": order.razorpay_order_id,
        "status": order.status,
        "amount": order.amount
    }
