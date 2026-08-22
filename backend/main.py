from fastapi import FastAPI, Depends, HTTPException, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel
import os
from dotenv import load_dotenv
from typing import Optional

from . import models, database
from .mcp_server import search_products, get_product_details
from .agents.negotiation_manager import NegotiationManager
from .razorpay_client import verify_webhook_signature

load_dotenv()

# Create database tables
models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(title="NegoPay API", description="Agentic Commerce Gateway")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Pydantic Models ---
class SearchRequest(BaseModel):
    query: str = ""
    max_price: Optional[float] = None
    category: Optional[str] = None

class NegotiateRequest(BaseModel):
    owner_id: str
    product_id: str
    initial_message: str

# --- API Endpoints ---
@app.get("/")
def read_root():
    return {"status": "ok", "service": "NegoPay Backend"}

@app.post("/api/products/search")
def api_search_products(req: SearchRequest):
    results = search_products(query=req.query, max_price=req.max_price, category=req.category)
    return {"results": results}

@app.post("/api/negotiate")
def api_start_negotiation(req: NegotiateRequest, db: Session = Depends(database.get_db)):
    import uuid
    product = get_product_details(req.product_id)
    if "error" in product:
        raise HTTPException(status_code=404, detail="Product not found")
        
    session_id = f"sess_{uuid.uuid4().hex[:8]}"
    manager = NegotiationManager(
        owner_id=req.owner_id,
        merchant_id=product["merchant_id"],
        product_id=req.product_id,
        session_id=session_id
    )
    
    # This runs synchronously for the demo, but in production would be async/websockets
    result = manager.start_negotiation(req.initial_message)
    return {"session_id": session_id, "result": result}

@app.get("/api/orders/{owner_id}")
def api_get_orders(owner_id: str, db: Session = Depends(database.get_db)):
    orders = db.query(models.Order).all() # Simplification for demo
    return {"orders": orders}

@app.post("/api/webhook/razorpay")
async def razorpay_webhook(request: Request, db: Session = Depends(database.get_db)):
    signature = request.headers.get("X-Razorpay-Signature")
    body = await request.body()
    
    if not verify_webhook_signature(body, signature):
        raise HTTPException(status_code=400, detail="Invalid signature")
        
    import json
    data = json.loads(body)
    
    if data.get("event") == "order.paid":
        order_data = data["payload"]["order"]["entity"]
        rp_order_id = order_data["id"]
        
        order = db.query(models.Order).filter(models.Order.razorpay_order_id == rp_order_id).first()
        if order:
            order.status = "PAID"
            db.commit()
            
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
