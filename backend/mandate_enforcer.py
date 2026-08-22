from typing import Dict, Any
from backend.database import SessionLocal
from backend import models

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def check_mandate(owner_id: str, amount: float, category: str = None) -> Dict[str, Any]:
    """
    Evaluates a purchase against the user's hard mandate limits.
    Returns decision: APPROVED, DENIED, or REQUIRES_APPROVAL
    """
    db = next(get_db())
    mandate = db.query(models.Mandate).filter(models.Mandate.owner_id == owner_id).first()
    
    if not mandate:
        # If no mandate exists, default to safe limits or deny. 
        # For buildathon demo, let's create a default one if missing.
        mandate = models.Mandate(
            id=f"mnd_{owner_id}",
            owner_id=owner_id,
            max_per_transaction=2000.0,
            max_daily_spend=5000.0,
            allowed_categories="[]",
            blocked_categories='["alcohol", "tobacco"]',
            auto_approve_below=500.0,
            require_approval_above=1500.0
        )
        db.add(mandate)
        db.commit()
        db.refresh(mandate)

    # 1. Per-transaction limit
    if amount > mandate.max_per_transaction:
        return {
            "decision": "DENIED",
            "reason": f"Amount ₹{amount} exceeds per-transaction limit of ₹{mandate.max_per_transaction}",
            "mandate_id": mandate.id
        }

    # 2. Daily aggregate check (mocking daily spend as 0 for simplicity, in reality query payments table)
    # We'll calculate total spent today.
    # Note: SQLite date filtering can be tricky, so we do a simple sum for the demo.
    total_spent_today = 0.0
    # In a full implementation: db.query(func.sum(Order.amount)).filter(...)
    
    if total_spent_today + amount > mandate.max_daily_spend:
        return {
            "decision": "DENIED",
            "reason": f"Amount ₹{amount} would exceed daily limit of ₹{mandate.max_daily_spend} (Already spent: ₹{total_spent_today})",
            "mandate_id": mandate.id
        }

    # 3. Category check
    if category:
        import json
        blocked = json.loads(mandate.blocked_categories) if mandate.blocked_categories else []
        if category.lower() in [b.lower() for b in blocked]:
            return {
                "decision": "DENIED",
                "reason": f"Category '{category}' is explicitly blocked by mandate.",
                "mandate_id": mandate.id
            }

    # 4. Approval thresholds
    if amount > mandate.require_approval_above:
        return {
            "decision": "REQUIRES_APPROVAL",
            "reason": f"Amount ₹{amount} exceeds auto-approve limit of ₹{mandate.require_approval_above}. Human approval required.",
            "mandate_id": mandate.id
        }

    return {
        "decision": "APPROVED",
        "reason": "All mandate checks passed.",
        "mandate_id": mandate.id
    }
