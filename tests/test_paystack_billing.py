import asyncio
import json
import hmac
import hashlib
from httpx import AsyncClient, ASGITransport
from main import app
from database import init_db, engine, Base
from services.paystack_service import PaystackService

async def test_paystack_service_and_billing_routes():
    """Integration test suite for Paystack Service, Billing Router, and HMAC Webhook verification."""
    print("\n🚀 Starting Paystack Integration & Security Test Suite...")

    # Initialize DB schema for test
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    import uuid
    test_email = f"paystack_{uuid.uuid4().hex[:8]}@acme.com"

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        
        # 1. Test Tenant Registration
        reg_res = await ac.post("/api/tenants/register", json={
            "name": "Paystack Test Org",
            "email": test_email,
            "tier": "free"
        })
        assert reg_res.status_code == 201
        tenant_data = reg_res.json()["tenant"]
        tenant_id = tenant_data["id"]
        print(f"  ✅ Tenant Registered: {tenant_id}")

        # 2. Test Initialize Payment Session
        init_res = await ac.post("/api/billing/initialize", json={
            "email": test_email,
            "amount": 5000,  # 5000 NGN
            "currency": "NGN",
            "tenant_id": tenant_id
        })
        assert init_res.status_code == 200
        init_data = init_res.json()
        assert "checkout_url" in init_data or "authorization_url" in init_data
        print(f"  ✅ Payment Initialization Successful: {init_data.get('reference', 'mock_ref')}")

        # 3. Test Paystack HMAC Webhook Signature Verification Utility
        secret = "sk_test_mock_secret_key_12345"
        PaystackService_PAYSTACK_SECRET_KEY_BACKUP = PaystackService.is_configured
        
        # Simulate HMAC calculation
        raw_body = json.dumps({"event": "charge.success", "data": {"metadata": {"tenant_id": tenant_id}}}).encode('utf-8')
        computed_sig = hmac.new(secret.encode('utf-8'), msg=raw_body, digestmod=hashlib.sha512).hexdigest()

        # Temporarily inject secret key for signature verification test
        from services import paystack_service
        paystack_service.PAYSTACK_SECRET_KEY = secret
        
        isValid = PaystackService.verify_webhook_signature(raw_body, computed_sig)
        assert isValid is True
        print("  ✅ Paystack HMAC SHA512 Webhook Signature Verification Passed!")

        # 4. Test Webhook Endpoint with Signature
        webhook_res = await ac.post(
            "/api/billing/webhook",
            content=raw_body,
            headers={"x-paystack-signature": computed_sig, "Content-Type": "application/json"}
        )
        assert webhook_res.status_code == 200
        assert webhook_res.json()["status"] == "success"
        print("  ✅ Webhook Event Handler Successfully Processed 'charge.success'")

        # 5. Verify Tenant Quota Top-Up
        usage_res = await ac.get(f"/api/tenants/{tenant_id}/usage")
        assert usage_res.status_code == 200
        updated_quota = usage_res.json()["monthly_quota"]
        assert updated_quota == 11000  # Initial 1000 + 10000 top up
        print(f"  ✅ Tenant Quota Successfully Upgraded to {updated_quota}!")

if __name__ == "__main__":
    asyncio.run(test_paystack_service_and_billing_routes())
    print("\n🎉 ALL PAYSTACK INTEGRATION TESTS PASSED SUCCESSFULLY!")
