import pytest
from httpx import AsyncClient, ASGITransport
from main import app
from services.education import LEVELS, Stage

@pytest.mark.anyio
async def test_get_education_levels():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.get("/api/education-levels")
        assert res.status_code == 200
        data = res.json()
        
        assert "levels" in data
        assert "stages" in data
        assert "total_levels" in data
        assert data["total_levels"] == len(LEVELS)
        assert len(data["stages"]) == len(list(Stage))
        
        # Verify first and last levels
        assert data["levels"][0]["code"] == "kg_1"
        assert data["levels"][-1]["code"] == "professional"
        
        # Verify cache control header
        assert "public, max-age=86400" in res.headers.get("cache-control", "")

@pytest.mark.anyio
async def test_resolve_education_level_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Test Primary 1
        res = await ac.get("/api/education-levels/resolve?query=Primary 1")
        assert res.status_code == 200
        data = res.json()
        assert data["matched"] is True
        assert data["level"]["code"] == "primary_1"
        assert data["level"]["stage"] == "primary"
        
        # Test Ghanaian / Regional alias
        res = await ac.get("/api/education-levels/resolve?query=JHS 2")
        assert res.status_code == 200
        data = res.json()
        assert data["matched"] is True
        assert data["level"]["code"] == "jss_2"
        assert data["level"]["stage"] == "junior_secondary"
        
        # Test University Level 300
        res = await ac.get("/api/education-levels/resolve?query=Level 300")
        assert res.status_code == 200
        data = res.json()
        assert data["matched"] is True
        assert data["level"]["code"] == "ug_3"
        assert data["level"]["stage"] == "undergraduate"
        
        # Test PhD
        res = await ac.get("/api/education-levels/resolve?query=PhD")
        assert res.status_code == 200
        data = res.json()
        assert data["matched"] is True
        assert data["level"]["code"] == "phd"
        assert data["level"]["stage"] == "doctoral"
        
        # Test Section preservation in class_label
        res = await ac.get("/api/education-levels/resolve?query=Class 5A")
        assert res.status_code == 200
        data = res.json()
        assert data["matched"] is True
        assert data["level"]["code"] == "primary_5"
        assert data["class_label"] == "Class 5A"
        
        # Test Unmatched
        res = await ac.get("/api/education-levels/resolve?query=UnknownNonsenseStringXYZ")
        assert res.status_code == 200
        data = res.json()
        assert data["matched"] is False
        assert data["level"] is None

@pytest.mark.anyio
async def test_questions_education_level_filters():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Verify endpoint responds to education_level and stage params without error
        res1 = await ac.get("/api/questions?education_level=primary_1&limit=5")
        assert res1.status_code == 200
        data1 = res1.json()
        assert "questions" in data1
        
        res2 = await ac.get("/api/questions?stage=primary&limit=5")
        assert res2.status_code == 200
        data2 = res2.json()
        assert "questions" in data2
        
        res3 = await ac.get("/api/questions?min_level=primary_1&max_level=primary_6&limit=5")
        assert res3.status_code == 200
        data3 = res3.json()
        assert "questions" in data3

async def main():
    print("Testing GET /api/education-levels...")
    await test_get_education_levels()
    print("✅ /api/education-levels passed")

    print("Testing GET /api/education-levels/resolve...")
    await test_resolve_education_level_endpoint()
    print("✅ /api/education-levels/resolve passed")

    print("Testing GET /api/questions with education level filters...")
    await test_questions_education_level_filters()
    print("✅ /api/questions filters passed")

    print("\n🎉 ALL EDUCATION API TESTS PASSED!")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

