import os
import hmac
import hashlib
import logging
from typing import Optional, Dict, Any
import httpx
from config import settings

logger = logging.getLogger(__name__)

PAYSTACK_BASE_URL = "https://api.paystack.co"
PAYSTACK_SECRET_KEY = getattr(settings, "PAYSTACK_SECRET_KEY", os.getenv("PAYSTACK_SECRET_KEY", ""))

class PaystackService:
    """Service to interface with Paystack REST API for payments, subscriptions, and webhooks."""

    @staticmethod
    def is_configured() -> bool:
        """Check if Paystack Secret Key is configured."""
        return bool(PAYSTACK_SECRET_KEY and PAYSTACK_SECRET_KEY.startswith("sk_"))

    @staticmethod
    def get_headers() -> Dict[str, str]:
        """Get standard Paystack API authorization headers."""
        return {
            "Authorization": f"Bearer {PAYSTACK_SECRET_KEY}",
            "Content-Type": "application/json",
        }

    @classmethod
    async def create_customer(
        cls, 
        email: str, 
        first_name: Optional[str] = None, 
        last_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a new customer in Paystack.
        
        API Docs: https://paystack.com/docs/api/customer/#create
        """
        if not cls.is_configured():
            logger.warning("Paystack is not configured. Returning fallback customer representation.")
            return {"status": False, "message": "Paystack secret key is not configured"}

        payload = {"email": email}
        if first_name:
            payload["first_name"] = first_name
        if last_name:
            payload["last_name"] = last_name

        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                response = await client.post(
                    f"{PAYSTACK_BASE_URL}/customer",
                    json=payload,
                    headers=cls.get_headers()
                )
                res_data = response.json()
                if response.status_code in (200, 201) and res_data.get("status"):
                    logger.info(f"Successfully created Paystack customer: {email}")
                    return res_data
                else:
                    logger.error(f"Paystack customer creation failed: {res_data}")
                    return res_data
            except Exception as e:
                logger.error(f"Exception during Paystack customer creation: {e}")
                return {"status": False, "message": str(e)}

    @classmethod
    async def initialize_transaction(
        cls,
        email: str,
        amount_kobo: int,
        currency: str = "NGN",
        callback_url: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Initialize a payment transaction on Paystack.
        
        API Docs: https://paystack.com/docs/api/transaction/#initialize
        Note: amount is in subunit (e.g. 5000 NGN = 500000 kobo).
        """
        if not cls.is_configured():
            logger.info("Paystack is unconfigured; returning dev mock authorization URL.")
            return {
                "status": True, 
                "message": "Paystack dev mock session created.",
                "data": {
                    "authorization_url": "https://checkout.paystack.com/mock-demo",
                    "reference": "mock_ref_12345",
                    "access_code": "mock_access_12345"
                }
            }

        payload: Dict[str, Any] = {
            "email": email,
            "amount": amount_kobo,
            "currency": currency,
        }
        if callback_url:
            payload["callback_url"] = callback_url
        if metadata:
            payload["metadata"] = metadata

        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                response = await client.post(
                    f"{PAYSTACK_BASE_URL}/transaction/initialize",
                    json=payload,
                    headers=cls.get_headers()
                )
                res_data = response.json()
                return res_data
            except Exception as e:
                logger.error(f"Exception during Paystack transaction initialization: {e}")
                return {"status": False, "message": str(e)}

    @classmethod
    async def verify_transaction(cls, reference: str) -> Dict[str, Any]:
        """Verify the status of a transaction reference on Paystack.
        
        API Docs: https://paystack.com/docs/api/transaction/#verify
        """
        if not cls.is_configured():
            return {"status": False, "message": "Paystack is not configured on server"}

        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                response = await client.get(
                    f"{PAYSTACK_BASE_URL}/transaction/verify/{reference}",
                    headers=cls.get_headers()
                )
                res_data = response.json()
                return res_data
            except Exception as e:
                logger.error(f"Exception verifying Paystack transaction: {e}")
                return {"status": False, "message": str(e)}

    @staticmethod
    def verify_webhook_signature(payload_bytes: bytes, signature_header: Optional[str]) -> bool:
        """Verify incoming Paystack webhook HMAC SHA512 signature.
        
        Paystack signs all event webhooks with HMAC SHA512 using your secret key.
        Header: x-paystack-signature
        """
        if not PAYSTACK_SECRET_KEY or not signature_header:
            return False

        computed_signature = hmac.new(
            PAYSTACK_SECRET_KEY.encode('utf-8'),
            msg=payload_bytes,
            digestmod=hashlib.sha512
        ).hexdigest()

        return hmac.compare_digest(computed_signature, signature_header)
