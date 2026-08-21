import json
import os
from .database import SessionLocal, engine
from . import models

def seed_db():
    print("Starting database seeding...")
    models.Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    # Merchants
    merchants = [
        {"id": "techmart", "name": "TechMart", "description": "Premium electronics and gadgets", "config_json": '{"max_discount_percent": 15, "floor_price_margin": 10}'},
        {"id": "soundstore", "name": "SoundStore", "description": "High-end audio equipment", "config_json": '{"max_discount_percent": 20, "floor_price_margin": 15}'},
        {"id": "bookhaven", "name": "BookHaven", "description": "Books for every reader", "config_json": '{"max_discount_percent": 10, "floor_price_margin": 5}'}
    ]

    for m_data in merchants:
        merchant = db.query(models.Merchant).filter(models.Merchant.id == m_data["id"]).first()
        if not merchant:
            db.add(models.Merchant(**m_data))

    # Products
    seed_file_path = os.path.join(os.path.dirname(__file__), "seed_products.json")
    if os.path.exists(seed_file_path):
        with open(seed_file_path, "r", encoding="utf-8") as f:
            products = json.load(f)
            
        for p_data in products:
            existing = db.query(models.Product).filter(models.Product.id == p_data["id"]).first()
            if not existing:
                tags = p_data.pop("tags", [])
                p_data["tags"] = json.dumps(tags)
                db.add(models.Product(**p_data))
                
    db.commit()
    db.close()
    print("Seeding complete!")

if __name__ == "__main__":
    seed_db()
