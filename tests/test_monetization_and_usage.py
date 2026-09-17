import os
import sys
import uuid
import asyncio
from unittest.mock import patch, AsyncMock
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select

from main import app
from database import engine, Base, async_session_maker
from models.user import User
from models.tenant import Tenant, APIKey
from utils.usage_limits import USER_TIER_LIMITS, get_user_quota_info

async def test_full_monetization_and_quota_suite():
    print("\n🚀 Starting Monetization, Quota Enforcement & Billing Test Suite...")

    # Ensure DB tables exist
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:

        # -------------------------------------------------------------
        # 1. B2C User Registration & Initial Free Quota (15 / mo)
        # -------------------------------------------------------------
        user_email = f"educator_{uuid.uuid4().hex[:8]}@oxford.edu"
        reg_res = await ac.post("/api/auth/register", json={
            "email": user_email,
            "password": "Password123!",
            "full_name": "Prof. Charles Xavier"
        })
        assert reg_res.status_code == 201, reg_res.text
        reg_data = reg_res.json()
        token = reg_data["access_token"]
        user_id = reg_data["user"]["id"]
        auth_headers = {"Authorization": f"Bearer {token}"}

        # Check /me profile quota fields
        me_res = await ac.get("/api/auth/me", headers=auth_headers)
        assert me_res.status_code == 200
        me_user = me_res.json()["user"]
        assert me_user["tier"] == "free"
        assert me_user["monthly_generations_used"] == 0
        assert me_user["monthly_limit"] == 6
        assert me_user["generations_remaining"] == 6
        assert me_user["max_questions_per_quiz"] == 20
        assert me_user["monthly_questions_limit"] == 120
        print(f"  ✅ Step 1: User Registered on Free Tier ({me_user['generations_remaining']}/{me_user['monthly_limit']} remaining)")

        # -------------------------------------------------------------
        # 2. Test Generation Quota Deduction for Free User
        # -------------------------------------------------------------
        mock_questions = [
            {
                "question": "What is the primary function of mitochondria?",
                "answer": "A",
                "choices": ["ATP energy production", "Protein synthesis", "Lipid storage", "DNA replication"],
                "rationale": "Mitochondria produce cellular ATP.",
                "blooms_level": "Remember"
            }
        ]

        with patch("routers.upload_and_generate.process_image", new_callable=AsyncMock) as mock_img, \
             patch("routers.upload_and_generate.generate_questions_from_content", return_value=mock_questions):
            mock_img.return_value = {"text": "Cell biology content", "description": "", "file_path": "uploads/test.png"}

            files = {"files": ("biology.png", b"fake_png_data", "image/png")}
            gen_res = await ac.post(
                "/api/generate/upload-and-generate",
                files=files,
                data={"qtype": "mcq", "num_questions": 1},
                headers=auth_headers
            )
            assert gen_res.status_code == 200, gen_res.text
            gen_data = gen_res.json()
            assert "usage" in gen_data
            assert gen_data["usage"]["monthly_generations_used"] == 1
            assert gen_data["usage"]["generations_remaining"] == 5
            assert gen_data["usage"]["monthly_questions_generated"] == 1
            print(f"  ✅ Step 2: Generation successful; quota deducted (Used: 1, Remaining: 5)")

        # -------------------------------------------------------------
        # 3. Test User Quota Exhaustion (Limit Reached -> 402 Payment Required)
        # -------------------------------------------------------------
        async with async_session_maker() as session:
            stmt = select(User).where(User.id == user_id)
            res = await session.execute(stmt)
            user_obj = res.scalar_one()
            user_obj.monthly_generations_used = 6  # Max for free tier
            await session.commit()

        # Attempt another generation -> Must return HTTP 402 PLAN_LIMIT_REACHED
        files = {"files": ("biology.png", b"fake_png_data", "image/png")}
        blocked_res = await ac.post(
            "/api/generate/upload-and-generate",
            files=files,
            data={"qtype": "mcq", "num_questions": 1},
            headers=auth_headers
        )
        assert blocked_res.status_code == 402, f"Expected 402, got {blocked_res.status_code}: {blocked_res.text}"
        blocked_json = blocked_res.json()
        assert blocked_json["error_code"] == "PLAN_LIMIT_REACHED"
        print(f"  ✅ Step 3: Quota exhaustion enforced with HTTP 402: {blocked_json['message']}")

        # -------------------------------------------------------------
        # 4. Paystack Subscription Upgrade to 'Pro' Tier
        # -------------------------------------------------------------
        # Initialize payment with user_id & plan_tier
        init_res = await ac.post("/api/billing/initialize", json={
            "email": user_email,
            "amount": 15.0,
            "user_id": user_id,
            "plan_tier": "pro"
        })
        assert init_res.status_code == 200
        init_data = init_res.json()
        ref = init_data["reference"]

        # Simulate Paystack Webhook Event: charge.success
        webhook_res = await ac.post("/api/billing/webhook", json={
            "event": "charge.success",
            "data": {
                "reference": ref,
                "amount": 1500,
                "status": "success",
                "customer": {"email": user_email, "customer_code": "CUS_test123"},
                "metadata": {
                    "user_id": user_id,
                    "plan_tier": "pro"
                }
            }
        })
        assert webhook_res.status_code == 200, webhook_res.text

        # Verify User profile is now Pro tier with 300 quota & reset count
        me_pro_res = await ac.get("/api/auth/me", headers=auth_headers)
        assert me_pro_res.status_code == 200
        pro_user = me_pro_res.json()["user"]
        assert pro_user["tier"] == "pro"
        assert pro_user["monthly_generations_used"] == 0
        assert pro_user["monthly_limit"] == 50
        assert pro_user["generations_remaining"] == 50
        assert pro_user["max_questions_per_quiz"] == 35
        assert pro_user["monthly_questions_limit"] == 1000
        print(f"  ✅ Step 4: Paystack Upgrade to PRO Succeeded! (Limit: 50, Remaining: 50, Max Qs/Quiz: 35, Monthly Qs: 1,000)")

        # -------------------------------------------------------------
        # 5. B2B Tenant API Key & Quota Enforcement
        # -------------------------------------------------------------
        tenant_email = f"corp_{uuid.uuid4().hex[:8]}@edtech-global.com"
        reg_tenant_res = await ac.post("/api/tenants/register", json={
            "name": "EdTech Global",
            "email": tenant_email,
            "tier": "starter"
        })
        assert reg_tenant_res.status_code == 201
        tenant_data = reg_tenant_res.json()
        tenant_id = tenant_data["tenant"]["id"]
        raw_api_key = tenant_data["api_key"]["raw_key"]
        api_headers = {"X-API-Key": raw_api_key}

        # Check tenant usage
        tenant_usage_res = await ac.get(f"/api/tenants/{tenant_id}/usage")
        assert tenant_usage_res.status_code == 200
        assert tenant_usage_res.json()["monthly_quota"] == 1000
        print(f"  ✅ Step 5: B2B Tenant registered with 1,000 initial API credits")

        # -------------------------------------------------------------
        # 6. Tenant Generation Call Deducts API Quota
        # -------------------------------------------------------------
        with patch("routers.upload_and_generate.process_image", new_callable=AsyncMock) as mock_img, \
             patch("routers.upload_and_generate.generate_questions_from_content", return_value=mock_questions):
            mock_img.return_value = {"text": "History content", "description": "", "file_path": "uploads/test2.png"}

            files = {"files": ("history.png", b"fake_png_data", "image/png")}
            tenant_gen_res = await ac.post(
                "/api/generate/upload-and-generate",
                files=files,
                data={"qtype": "mcq", "num_questions": 1},
                headers=api_headers
            )
            assert tenant_gen_res.status_code == 200, tenant_gen_res.text
            assert tenant_gen_res.json()["usage"]["quota_remaining"] == 999
            print(f"  ✅ Step 6: API Key call deducted 1 credit (Remaining: 999)")

        # -------------------------------------------------------------
        # 7. Tenant Quota Depletion -> HTTP 402 QUOTA_EXHAUSTED
        # -------------------------------------------------------------
        async with async_session_maker() as session:
            stmt = select(Tenant).where(Tenant.id == tenant_id)
            res = await session.execute(stmt)
            t_obj = res.scalar_one()
            t_obj.monthly_quota = 0
            await session.commit()

        files = {"files": ("history.png", b"fake_png_data", "image/png")}
        tenant_blocked_res = await ac.post(
            "/api/generate/upload-and-generate",
            files=files,
            data={"qtype": "mcq", "num_questions": 1},
            headers=api_headers
        )
        assert tenant_blocked_res.status_code == 402, tenant_blocked_res.text
        assert tenant_blocked_res.json()["error_code"] == "QUOTA_EXHAUSTED"
        print(f"  ✅ Step 7: B2B Quota exhaustion enforced with HTTP 402: {tenant_blocked_res.json()['message']}")

        # -------------------------------------------------------------
        # 8. Tenant Credit Top-up via Paystack (+10,000 Credits)
        # -------------------------------------------------------------
        topup_webhook = await ac.post("/api/billing/webhook", json={
            "event": "charge.success",
            "data": {
                "reference": f"ref_{uuid.uuid4().hex[:8]}",
                "amount": 500000,
                "status": "success",
                "customer": {"email": tenant_email, "customer_code": "CUS_tenant456"},
                "metadata": {
                    "tenant_id": tenant_id
                }
            }
        })
        assert topup_webhook.status_code == 200

        # Check tenant usage after top-up
        after_topup_res = await ac.get(f"/api/tenants/{tenant_id}/usage")
        assert after_topup_res.status_code == 200
        assert after_topup_res.json()["monthly_quota"] == 10000
        assert after_topup_res.json()["tier"] == "growth"
        print(f"  ✅ Step 8: Paystack Webhook credited +10,000 API calls (New Balance: 10,000, Tier: Growth)")

    print("\n🎉 ALL MONETIZATION & USAGE TESTS PASSED FLAWLESSLY!\n")

if __name__ == "__main__":
    asyncio.run(test_full_monetization_and_quota_suite())
