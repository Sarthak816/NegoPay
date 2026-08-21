import razorpay
import os
import hmac
import hashlib
from dotenv import load_dotenv

load_dotenv()

key_id = os.getenv("RAZORPAY_KEY_ID")
key_secret = os.getenv("RAZORPAY_KEY_SECRET")

# Initialize Razorpay client only if keys are present
if key_id and key_secret:
    client = razorpay.Client(auth=(key_id, key_secret))
else:
    client = None
    print("WARNING: Razorpay API keys not found in environment. Payment features will not work.")

def create_order(amount_inr: float, currency: str = "INR", receipt: str = None, notes: dict = None):
    if not client:
        raise ValueError("Razorpay client not configured.")
    
    amount_paise = int(amount_inr * 100)
    data = {
        "amount": amount_paise,
        "currency": currency,
        "receipt": receipt,
        "notes": notes or {}
    }
    return client.order.create(data=data)

def verify_webhook_signature(body: bytes, signature: str) -> bool:
    if not key_secret:
        return False
    
    expected_signature = hmac.new(
        key_secret.encode('utf-8'),
        body,
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(expected_signature, signature)
