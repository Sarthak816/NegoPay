from sqlalchemy import Column, Integer, String, Float, Boolean, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base

class Merchant(Base):
    __tablename__ = "merchants"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(Text)
    config_json = Column(Text)  # Store JSON as string (max discount, floor margin, etc)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    products = relationship("Product", back_populates="merchant")

class Product(Base):
    __tablename__ = "products"

    id = Column(String, primary_key=True, index=True)
    merchant_id = Column(String, ForeignKey("merchants.id"))
    name = Column(String, index=True)
    description = Column(Text)
    price = Column(Float)
    category = Column(String, index=True)
    tags = Column(String)  # Comma separated or JSON string
    stock = Column(Integer, default=0)
    image_url = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    merchant = relationship("Merchant", back_populates="products")

class Order(Base):
    __tablename__ = "orders"

    id = Column(String, primary_key=True, index=True)
    razorpay_order_id = Column(String, unique=True, index=True)
    product_id = Column(String, ForeignKey("products.id"))
    merchant_id = Column(String, ForeignKey("merchants.id"))
    quantity = Column(Integer)
    amount = Column(Float)
    status = Column(String)  # CREATED, PAID, FAILED
    idempotency_key = Column(String, unique=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class Payment(Base):
    __tablename__ = "payments"

    id = Column(String, primary_key=True, index=True)
    order_id = Column(String, ForeignKey("orders.id"))
    razorpay_payment_id = Column(String, unique=True, index=True, nullable=True)
    amount = Column(Float)
    status = Column(String)
    method = Column(String, nullable=True)
    attempts = Column(Integer, default=1)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Mandate(Base):
    __tablename__ = "mandates"

    id = Column(String, primary_key=True, index=True)
    owner_id = Column(String, index=True)
    max_per_transaction = Column(Float)
    max_daily_spend = Column(Float)
    allowed_categories = Column(Text)  # JSON string
    blocked_categories = Column(Text)  # JSON string
    auto_approve_below = Column(Float)
    require_approval_above = Column(Float)
    max_negotiation_rounds = Column(Integer, default=5)
    walk_away_threshold = Column(Float, default=0.85)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class AuditEvent(Base):
    __tablename__ = "audit_events"

    id = Column(String, primary_key=True, index=True)
    session_id = Column(String, index=True)
    event_type = Column(String, index=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    agent = Column(String)  # BUYER, SELLER, SYSTEM
    action = Column(String)
    input_data = Column(Text, nullable=True)
    output_data = Column(Text, nullable=True)
    reasoning = Column(Text, nullable=True)
    metadata_json = Column(Text, nullable=True)

class NegotiationSession(Base):
    __tablename__ = "negotiation_sessions"

    id = Column(String, primary_key=True, index=True)
    buyer_agent_id = Column(String)
    seller_agent_id = Column(String)
    product_id = Column(String, ForeignKey("products.id"))
    status = Column(String)  # INITIATED, OFFER, COUNTER_OFFER, ACCEPTED, REJECTED, DEADLOCK
    rounds = Column(Integer, default=0)
    initial_price = Column(Float)
    final_price = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
