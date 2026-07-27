import asyncio
import uuid
from httpx import AsyncClient, ASGITransport
from main import app
from database import engine, Base

async def test_auth_and_quizzes_flow():
    """Test suite for JWT authentication, Quiz persistence, and QTI export."""
    print("\n🚀 Starting Auth, Quiz CRUD & Export Test Suite...")

    # Init DB schema
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    test_email = f"teacher_{uuid.uuid4().hex[:8]}@school.edu"
    test_password = "Password123!"

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:

        # 1. Test User Registration
        reg_res = await ac.post("/api/auth/register", json={
            "email": test_email,
            "password": test_password,
            "full_name": "Dr. Alex Vance"
        })
        assert reg_res.status_code == 201
        reg_data = reg_res.json()
        token = reg_data["access_token"]
        assert "user" in reg_data
        print(f"  ✅ Educator Account Registered: {test_email}")

        headers = {"Authorization": f"Bearer {token}"}

        # 2. Test Get Profile (/api/auth/me)
        me_res = await ac.get("/api/auth/me", headers=headers)
        assert me_res.status_code == 200
        assert me_res.json()["user"]["email"] == test_email
        print("  ✅ Profile Endpoint (/api/auth/me) Validated")

        # 3. Test User Login
        login_res = await ac.post("/api/auth/login", json={
            "email": test_email,
            "password": test_password
        })
        assert login_res.status_code == 200
        assert "access_token" in login_res.json()
        print("  ✅ Authentication Login (/api/auth/login) Validated")

        # 4. Save Quiz Bank
        quiz_res = await ac.post("/api/quizzes", headers=headers, json={
            "title": "Cell Biology & Genetics",
            "subject": "Biology",
            "original_file_name": "chapter4_worksheet.pdf",
            "questions": [
                {
                    "question_text": "What is the powerhouse of the cell?",
                    "answer_text": "Mitochondria",
                    "choices": ["Mitochondria", "Nucleus", "Ribosome", "Golgi Body"],
                    "rationale": "Mitochondria produce ATP through cellular respiration.",
                    "qtype": "mcq",
                    "difficulty": "easy"
                },
                {
                    "question_text": "DNA replication occurs during interphase.",
                    "answer_text": "True",
                    "choices": ["True", "False"],
                    "rationale": "DNA is replicated during the S phase of interphase.",
                    "qtype": "true_false",
                    "difficulty": "medium"
                }
            ]
        })
        assert quiz_res.status_code == 201
        quiz = quiz_res.json()["quiz"]
        quiz_id = quiz["id"]
        question_id = quiz["questions"][0]["id"]
        print(f"  ✅ Quiz Bank Created (ID: {quiz_id}) with {len(quiz['questions'])} Questions")

        # 5. List Quizzes
        list_res = await ac.get("/api/quizzes", headers=headers)
        assert list_res.status_code == 200
        assert len(list_res.json()["quizzes"]) >= 1
        print("  ✅ List Quiz Banks Validated")

        # 6. Update Question
        update_res = await ac.put(
            f"/api/quizzes/{quiz_id}/questions/{question_id}",
            headers=headers,
            json={"difficulty": "medium", "rationale": "Updated rationale for cell biology."}
        )
        assert update_res.status_code == 200
        assert update_res.json()["question"]["difficulty"] == "medium"
        print("  ✅ Question Update Endpoint Validated")

        # 7. Export Canvas QTI package zip
        qti_res = await ac.get(f"/api/quizzes/{quiz_id}/export/qti", headers=headers)
        assert qti_res.status_code == 200
        assert qti_res.headers["content-type"] == "application/zip"
        assert len(qti_res.content) > 100
        print("  ✅ Canvas QTI 2.1 Package Export (.zip) Generated Successfully")

        # 8. Export Printable Text
        text_res = await ac.get(f"/api/quizzes/{quiz_id}/export/text", headers=headers)
        assert text_res.status_code == 200
        assert "ANSWER KEY" in text_res.text
        print("  ✅ Printable Text & Answer Key Export (.txt) Generated Successfully")

if __name__ == "__main__":
    asyncio.run(test_auth_and_quizzes_flow())
    print("\n🎉 ALL BACKEND AUTH & QUIZ PERSISTENCE TESTS PASSED SUCCESSFULLY!")
