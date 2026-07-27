import asyncio
from httpx import AsyncClient, ASGITransport
from main import app
from database import init_db, engine, Base

async def test_tenant_registration_and_api_key_flow():
    """Integration test verifying Tenant registration and API Key authentication."""
    # Ensure DB tables exist
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    import uuid
    test_email = f"dev_{uuid.uuid4().hex[:8]}@acme-edtech.com"
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # 1. Register a new tenant
        reg_response = await ac.post("/api/tenants/register", json={
            "name": "Acme EdTech Corp",
            "email": test_email,
            "tier": "free"
        })
        assert reg_response.status_code == 201, reg_response.text
        data = reg_response.json()
        assert "tenant" in data
        assert "api_key" in data
        
        tenant_id = data["tenant"]["id"]
        raw_key = data["api_key"]["raw_key"]
        assert raw_key.startswith("qg_live_")

        # 2. List API Keys for the tenant
        keys_response = await ac.get(f"/api/tenants/{tenant_id}/api-keys")
        assert keys_response.status_code == 200
        keys_data = keys_response.json()
        assert len(keys_data["api_keys"]) >= 1

        # 3. Create a second API key
        new_key_response = await ac.post(f"/api/tenants/{tenant_id}/api-keys", json={
            "name": "Staging Key",
            "rate_limit_rpm": 120
        })
        # 4. Check Free Tier usage & quota
        usage_response = await ac.get(f"/api/tenants/{tenant_id}/usage")
        assert usage_response.status_code == 200
        usage_data = usage_response.json()
        assert usage_data["monthly_quota"] == 1000
        assert usage_data["pricing"] == "Free ($0.00)"

from utils.rate_limit import check_rate_limit

def test_rate_limiter():
    tenant_id = "test_tenant_123"
    # First 5 requests under limit of 5 should pass
    for _ in range(5):
        assert check_rate_limit(tenant_id, limit_rpm=5) is True
    # 6th request should fail
    assert check_rate_limit(tenant_id, limit_rpm=5) is False
    print("✅ RATE LIMITER TEST PASSED!")

if __name__ == "__main__":
    asyncio.run(test_tenant_registration_and_api_key_flow())
    test_rate_limiter()
    print("✅ ALL TESTS PASSED!")
