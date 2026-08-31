import pytest
import os
import sys

# Add parent directory to path so we can import backend modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.mandate_enforcer import check_mandate
from backend.database import SessionLocal, Base, engine
from backend import models

@pytest.fixture(scope="module", autouse=True)
def setup_test_db():
    # Ensure tables are created
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    
    # Create a test mandate
    test_owner = "test_user_123"
    existing = db.query(models.Mandate).filter(models.Mandate.owner_id == test_owner).first()
    if existing:
        db.delete(existing)
        db.commit()
        
    mandate = models.Mandate(
        id=f"mnd_{test_owner}",
        owner_id=test_owner,
        max_per_transaction=2000.0,
        max_daily_spend=5000.0,
        allowed_categories="[]",
        blocked_categories='["alcohol", "tobacco"]',
        auto_approve_below=500.0,
        require_approval_above=1500.0
    )
    db.add(mandate)
    db.commit()
    yield
    
    # Cleanup
    try:
        db.delete(mandate)
        db.commit()
    except:
        pass
    db.close()

def test_mandate_approved():
    # Amount below limits should be APPROVED
    result = check_mandate("test_user_123", 400.0, "Electronics")
    assert result["decision"] == "APPROVED"

def test_mandate_requires_approval():
    # Amount above auto-approve limit (1500) but below transaction max (2000)
    result = check_mandate("test_user_123", 1800.0, "Electronics")
    assert result["decision"] == "REQUIRES_APPROVAL"

def test_mandate_exceeds_transaction_limit():
    # Amount exceeds max_per_transaction (2000)
    result = check_mandate("test_user_123", 2500.0, "Electronics")
    assert result["decision"] == "DENIED"
    assert "exceeds per-transaction limit" in result["reason"]

def test_mandate_blocked_category():
    # Product category is blocked
    result = check_mandate("test_user_123", 100.0, "Alcohol")
    assert result["decision"] == "DENIED"
    assert "explicitly blocked" in result["reason"]

def test_mandate_fallback_creation():
    # Test that a missing mandate generates a safe default
    result = check_mandate("unknown_user_999", 50.0, "Books")
    assert result["decision"] == "APPROVED"
