import logging
from typing import Optional, Dict, Any
from services.paystack_service import PaystackService

logger = logging.getLogger(__name__)

class BillingService:
    """Unified Billing Service interface powered by Paystack."""

    @staticmethod
    def is_configured() -> bool:
        """Check if payment provider (Paystack) is configured."""
        return PaystackService.is_configured()

    @staticmethod
    async def create_customer(email: str, name: Optional[str] = None) -> Optional[str]:
        """Create a new customer in Paystack."""
        res = await PaystackService.create_customer(email=email, first_name=name)
        if res.get("status") and "data" in res:
            return res["data"].get("customer_code")
        return None

    @staticmethod
    async def create_checkout_session(
        email: str,
        amount_kobo: int,
        currency: str = "NGN",
        callback_url: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Initialize a Paystack payment session for subscriptions or top-ups."""
        res = await PaystackService.initialize_transaction(
            email=email,
            amount_kobo=amount_kobo,
            currency=currency,
            callback_url=callback_url,
            metadata=metadata
        )
        if res.get("status") and "data" in res:
            return {
                "checkout_url": res["data"].get("authorization_url"),
                "reference": res["data"].get("reference"),
                "access_code": res["data"].get("access_code")
            }
        return {"error": res.get("message", "Payment initialization failed")}

    @staticmethod
    async def verify_payment(reference: str) -> Dict[str, Any]:
        """Verify transaction status on Paystack."""
        return await PaystackService.verify_transaction(reference)
