import logging
from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Request, Header, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database import get_db
from models.tenant import Tenant
from services.paystack_service import PaystackService
from services.billing_service import BillingService

logger = logging.getLogger(__name__)

router = APIRouter()

class InitializePaymentRequest(BaseModel):
    email: EmailStr
    amount: float  # Amount in main currency unit (e.g. 5000 NGN)
    currency: Optional[str] = "NGN"
    tenant_id: Optional[str] = None
    callback_url: Optional[str] = None

@router.post("/initialize", status_code=status.HTTP_200_OK)
async def initialize_payment(
    body: InitializePaymentRequest,
    db: AsyncSession = Depends(get_db)
):
    """Initialize a Paystack payment session for subscription upgrades or credit top-ups."""
    # Convert amount to subunit (kobo / cents) -> 1 NGN = 100 kobo
    amount_kobo = int(body.amount * 100)

    metadata: Dict[str, Any] = {}
    if body.tenant_id:
        result = await db.execute(select(Tenant).where(Tenant.id == body.tenant_id))
        tenant = result.scalar_one_or_none()
        if not tenant:
            raise HTTPException(status_code=404, detail="Tenant not found")
        metadata["tenant_id"] = tenant.id
        metadata["tenant_name"] = tenant.name

    checkout_res = await BillingService.create_checkout_session(
        email=body.email,
        amount_kobo=amount_kobo,
        currency=body.currency,
        callback_url=body.callback_url,
        metadata=metadata
    )

    if "error" in checkout_res:
        raise HTTPException(status_code=400, detail=checkout_res["error"])

    return checkout_res

@router.get("/verify/{reference}", status_code=status.HTTP_200_OK)
async def verify_payment(
    reference: str,
    db: AsyncSession = Depends(get_db)
):
    """Verify transaction status on Paystack by reference."""
    res = await PaystackService.verify_transaction(reference)
    if not res.get("status"):
        raise HTTPException(status_code=400, detail=res.get("message", "Verification failed"))

    data = res.get("data", {})
    transaction_status = data.get("status")

    if transaction_status == "success":
        metadata = data.get("metadata", {})
        tenant_id = metadata.get("tenant_id")
        if tenant_id:
            result = await db.execute(select(Tenant).where(Tenant.id == tenant_id))
            tenant = result.scalar_one_or_none()
            if tenant:
                # Top up or upgrade tenant quota (e.g. add 10,000 requests)
                tenant.monthly_quota += 10000
                tenant.tier = "growth"
                await db.commit()
                logger.info(f"Updated quota for tenant {tenant_id} after successful Paystack transaction {reference}")

    return {
        "status": transaction_status,
        "amount": data.get("amount", 0) / 100,
        "currency": data.get("currency"),
        "reference": reference,
        "customer": data.get("customer", {}).get("email")
    }

@router.post("/webhook", status_code=status.HTTP_200_OK)
async def paystack_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
    x_paystack_signature: Optional[str] = Header(None)
):
    """Receive and process Paystack event webhooks (e.g., charge.success).
    
    Verifies HMAC SHA512 signature using x-paystack-signature header.
    """
    body_bytes = await request.body()

    # If Paystack secret key is configured, verify HMAC signature
    if PaystackService.is_configured():
        if not x_paystack_signature or not PaystackService.verify_webhook_signature(body_bytes, x_paystack_signature):
            logger.warning("Paystack webhook signature verification failed!")
            raise HTTPException(status_code=400, detail="Invalid Paystack signature header")

    event_data = await request.json()
    event_type = event_data.get("event")
    data = event_data.get("data", {})

    logger.info(f"Received Paystack Webhook Event: {event_type}")

    if event_type == "charge.success":
        metadata = data.get("metadata", {})
        tenant_id = metadata.get("tenant_id")
        if tenant_id:
            result = await db.execute(select(Tenant).where(Tenant.id == tenant_id))
            tenant = result.scalar_one_or_none()
            if tenant:
                tenant.monthly_quota += 10000
                tenant.tier = "growth"
                await db.commit()
                logger.info(f"Webhook updated tenant {tenant_id} quota successfully")

    return {"status": "success", "event": event_type}
