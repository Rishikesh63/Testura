import hmac
import hashlib
import logging
import razorpay
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.core.config import settings
from supabase import create_client
import uuid

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/billing", tags=["billing"])
supabase = create_client(settings.supabase_url, settings.supabase_service_key)

PLANS = {
    "starter": {"amount": 99900,  "currency": "INR", "name": "Starter Plan"},
    "pro":     {"amount": 249900, "currency": "INR", "name": "Pro Plan"},
}


def _client():
    return razorpay.Client(auth=(settings.razorpay_key_id, settings.razorpay_key_secret))


class CreateOrderRequest(BaseModel):
    plan: str
    user_id: str


class VerifyPaymentRequest(BaseModel):
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str
    plan: str
    user_id: str


@router.post("/create-order")
async def create_order(body: CreateOrderRequest):
    if body.plan not in PLANS:
        raise HTTPException(400, "Invalid plan")
    plan = PLANS[body.plan]
    order = _client().order.create({
        "amount": plan["amount"],
        "currency": plan["currency"],
        "receipt": f"testura_{uuid.uuid4().hex[:12]}",
        "notes": {"plan": body.plan, "user_id": body.user_id},
    })
    logger.info("Created Razorpay order %s for user %s plan %s", order["id"], body.user_id, body.plan)
    return {
        "order_id": order["id"],
        "amount": plan["amount"],
        "currency": plan["currency"],
        "name": plan["name"],
    }


@router.post("/verify")
async def verify_payment(body: VerifyPaymentRequest):
    # Verify Razorpay signature
    expected = hmac.new(
        settings.razorpay_key_secret.encode(),
        f"{body.razorpay_order_id}|{body.razorpay_payment_id}".encode(),
        hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(expected, body.razorpay_signature):
        raise HTTPException(400, "Invalid payment signature")

    # Upgrade user plan
    supabase.table("user_plans").upsert({
        "user_id": body.user_id,
        "plan": body.plan,
        "payment_id": body.razorpay_payment_id,
        "updated_at": "now()",
    }).execute()

    logger.info("Upgraded user %s to %s plan (payment %s)", body.user_id, body.plan, body.razorpay_payment_id)
    return {"ok": True, "plan": body.plan}


@router.get("/plan/{user_id}")
async def get_plan(user_id: str):
    res = supabase.table("user_plans").select("plan").eq("user_id", user_id).maybe_single().execute()
    return {"plan": res.data["plan"] if res.data else "free"}
