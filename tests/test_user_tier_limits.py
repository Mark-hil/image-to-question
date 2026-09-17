import sys
import uuid
import asyncio
from datetime import datetime, timedelta, timezone
from unittest.mock import patch, AsyncMock
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select

from main import app
from database import engine, Base, async_session_maker
from models.user import User
from utils.exceptions import AppError
from utils.usage_limits import (
    USER_TIER_LIMITS,
    USER_TIER_MAX_QUESTIONS,
    USER_TIER_MAX_MONTHLY_QUESTIONS,
    CallerIdentity,
    validate_question_count,
    get_user_quota_info,
    check_user_quota,
    refresh_user_quota_if_due,
    deduct_usage,
)

async def test_user_tier_limits_suite():
    print("\n🎯 ===============================================================")
    print("   STARTING COMPREHENSIVE USER TIER & LIMITS TEST SUITE")
    print("=================================================================\n")

    # -----------------------------------------------------------------
    # TEST 1: Industry-Standard Tier Configuration Constants
    # -----------------------------------------------------------------
    print("👉 Test 1: Verifying Industry-Standard Tier Limit Constants...")
    assert USER_TIER_LIMITS["free"] == 6
    assert USER_TIER_LIMITS["pro"] == 50
    assert USER_TIER_LIMITS["team"] == 250
    assert USER_TIER_LIMITS["institution"] == 750

    assert USER_TIER_MAX_QUESTIONS["guest"] == 5
    assert USER_TIER_MAX_QUESTIONS["free"] == 20
    assert USER_TIER_MAX_QUESTIONS["pro"] == 35
    assert USER_TIER_MAX_QUESTIONS["team"] == 50
    assert USER_TIER_MAX_QUESTIONS["institution"] == 100

    assert USER_TIER_MAX_MONTHLY_QUESTIONS["free"] == 120
    assert USER_TIER_MAX_MONTHLY_QUESTIONS["pro"] == 1000
    assert USER_TIER_MAX_MONTHLY_QUESTIONS["team"] == 5000
    assert USER_TIER_MAX_MONTHLY_QUESTIONS["institution"] == 15000
    print("  ✅ Test 1 Passed: All tier limit constants adhere to industry standard.")

    # -----------------------------------------------------------------
    # TEST 2: Per-Upload Question Ceiling (validate_question_count)
    # -----------------------------------------------------------------
    print("\n👉 Test 2: Testing Per-Upload Question Ceiling for Every Tier...")
    tiers = [
        ("guest", "guest", 5),
        ("user", "free", 20),
        ("user", "pro", 35),
        ("user", "team", 50),
        ("user", "institution", 100),
    ]

    for kind, tier_name, max_q in tiers:
        identity = CallerIdentity(kind=kind, tier=tier_name, max_questions=max_q)

        # Asking for valid questions within limit should succeed
        valid_res = validate_question_count(identity, max_q)
        assert valid_res == max_q

        # Asking for 1 question beyond limit must raise TIER_QUESTION_LIMIT_EXCEEDED
        try:
            validate_question_count(identity, max_q + 1)
            assert False, f"Expected AppError for {tier_name} requesting {max_q + 1} questions"
        except AppError as e:
            assert e.status_code == 400
            assert e.error_code == "TIER_QUESTION_LIMIT_EXCEEDED"
            assert str(max_q) in e.message
            assert str(max_q + 1) in e.message
        print(f"  ✅ {tier_name.capitalize()} ceiling enforced: allowed up to {max_q}, blocked at {max_q + 1}")

    # -----------------------------------------------------------------
    # TEST 3: Monthly Question Budget Validation (validate_question_count)
    # -----------------------------------------------------------------
    print("\n👉 Test 3: Testing Monthly Question Budget Enforcement...")
    now = datetime.now(timezone.utc)
    mock_pro_user = User(
        id=str(uuid.uuid4()),
        email="budget_test@school.org",
        tier="pro",
        monthly_generations_used=5,
        monthly_questions_generated=990,  # 990 / 1000 used -> 10 remaining
        quota_reset_at=now,
        created_at=now,
        is_active=True
    )
    pro_identity = CallerIdentity(kind="user", user=mock_pro_user, max_questions=35, tier="pro")

    # Requesting 10 questions (exact remainder) should succeed
    assert validate_question_count(pro_identity, 10) == 10

    # Requesting 11 questions (exceeds 10 remaining budget) -> 400 MONTHLY_QUESTION_BUDGET_EXCEEDED
    try:
        validate_question_count(pro_identity, 11)
        assert False, "Expected MONTHLY_QUESTION_BUDGET_EXCEEDED error"
    except AppError as e:
        assert e.status_code == 400
        assert e.error_code == "MONTHLY_QUESTION_BUDGET_EXCEEDED"
        assert "10 questions left" in e.message
    print("  ✅ Monthly question budget exceeded error enforced (400 MONTHLY_QUESTION_BUDGET_EXCEEDED)")

    # When quota is fully exhausted (1000 / 1000 used) -> 402 PLAN_LIMIT_REACHED
    mock_pro_user.monthly_questions_generated = 1000
    try:
        validate_question_count(pro_identity, 5)
        assert False, "Expected PLAN_LIMIT_REACHED error"
    except AppError as e:
        assert e.status_code == 402
        assert e.error_code == "PLAN_LIMIT_REACHED"
        assert "1000 questions" in e.message
    print("  ✅ Monthly question exhaustion enforced (402 PLAN_LIMIT_REACHED)")

    # -----------------------------------------------------------------
    # TEST 4: 30-Day Auto Reset Logic (refresh_user_quota_if_due)
    # -----------------------------------------------------------------
    print("\n👉 Test 4: Testing 30-Day Billing Cycle Quota Auto-Reset...")
    stale_date = now - timedelta(days=32)
    stale_user = User(
        id=str(uuid.uuid4()),
        email="reset_test@school.org",
        tier="pro",
        monthly_generations_used=50,
        monthly_questions_generated=1000,
        quota_reset_at=stale_date,
        created_at=stale_date,
        is_active=True
    )

    # Before reset: exhausted
    quota_before = get_user_quota_info(stale_user)
    # Note: get_user_quota_info calls refresh_user_quota_if_due internally!
    assert stale_user.monthly_generations_used == 0
    assert stale_user.monthly_questions_generated == 0
    assert stale_user.quota_reset_at > stale_date
    assert quota_before["is_quota_exhausted"] is False
    assert quota_before["generations_remaining"] == 50
    assert quota_before["total_questions_remaining"] == 1000
    print("  ✅ 30-day elapsed cycle automatically reset generations and question counters to 0")

    # -----------------------------------------------------------------
    # TEST 5: End-to-End API Generation Across All User Tiers
    # -----------------------------------------------------------------
    print("\n👉 Test 5: End-to-End HTTP API Validation Across All Tiers...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # A. Register new Free User
        test_email = f"tier_eval_{uuid.uuid4().hex[:6]}@academy.edu"
        reg_res = await ac.post("/api/auth/register", json={
            "email": test_email,
            "password": "SecurePassword123!",
            "full_name": "Tier Evaluation User"
        })
        assert reg_res.status_code == 201
        reg_json = reg_res.json()
        token = reg_json["access_token"]
        user_id = reg_json["user"]["id"]
        auth_headers = {"Authorization": f"Bearer {token}"}

        # Check Free Tier profile
        free_me = (await ac.get("/api/auth/me", headers=auth_headers)).json()["user"]
        assert free_me["tier"] == "free"
        assert free_me["monthly_limit"] == 6
        assert free_me["max_questions_per_quiz"] == 20
        assert free_me["monthly_questions_limit"] == 120
        assert free_me["generations_remaining"] == 6
        assert free_me["total_questions_remaining"] == 120
        print(f"  ✅ Free Tier Verified via API: {free_me['generations_remaining']}/{free_me['monthly_limit']} uploads, max {free_me['max_questions_per_quiz']} Qs/quiz")

        # Free tier upload requesting 25 questions -> must be rejected with 400
        mock_fake_questions = [{"question": "Q?", "answer": "A", "choices": ["A", "B"], "rationale": "R"}]
        with patch("routers.upload_and_generate.process_image", new_callable=AsyncMock) as mock_img, \
             patch("routers.upload_and_generate.generate_questions_from_content", return_value=mock_fake_questions):
            mock_img.return_value = {"text": "Content", "description": "", "file_path": "uploads/t.png"}

            files = {"files": ("test.png", b"fake_bytes", "image/png")}
            over_free_res = await ac.post(
                "/api/generate/upload-and-generate",
                files=files,
                data={"qtype": "mcq", "num_questions": 25},
                headers=auth_headers
            )
            assert over_free_res.status_code == 400
            assert over_free_res.json()["error_code"] == "TIER_QUESTION_LIMIT_EXCEEDED"
            print("  ✅ Free user generation of 25 questions blocked (exceeds max 20)")

            # Free tier valid generation of 10 questions
            valid_free_res = await ac.post(
                "/api/generate/upload-and-generate",
                files={"files": ("test.png", b"fake_bytes", "image/png")},
                data={"qtype": "mcq", "num_questions": 10},
                headers=auth_headers
            )
            assert valid_free_res.status_code == 200
            usage_free = valid_free_res.json()["usage"]
            assert usage_free["monthly_generations_used"] == 1
            assert usage_free["generations_remaining"] == 5
            assert usage_free["monthly_questions_generated"] == 1
            print("  ✅ Free user generation of allowed questions succeeded, quota deducted")

        # B. Test Pro Tier Limits
        async with async_session_maker() as session:
            stmt = select(User).where(User.id == user_id)
            db_user = (await session.execute(stmt)).scalar_one()
            db_user.tier = "pro"
            db_user.monthly_generations_used = 0
            db_user.monthly_questions_generated = 0
            await session.commit()

        pro_me = (await ac.get("/api/auth/me", headers=auth_headers)).json()["user"]
        assert pro_me["tier"] == "pro"
        assert pro_me["monthly_limit"] == 50
        assert pro_me["max_questions_per_quiz"] == 35
        assert pro_me["monthly_questions_limit"] == 1000
        print(f"  ✅ Pro Tier Verified via API: {pro_me['monthly_limit']} uploads/mo, max {pro_me['max_questions_per_quiz']} Qs/quiz, {pro_me['monthly_questions_limit']} monthly Qs")

        with patch("routers.upload_and_generate.process_image", new_callable=AsyncMock) as mock_img, \
             patch("routers.upload_and_generate.generate_questions_from_content", return_value=mock_fake_questions):
            mock_img.return_value = {"text": "Content", "description": "", "file_path": "uploads/t.png"}

            # Pro requesting 40 questions -> exceeds 35 ceiling -> 400
            over_pro_res = await ac.post(
                "/api/generate/upload-and-generate",
                files={"files": ("test.png", b"fake_bytes", "image/png")},
                data={"qtype": "mcq", "num_questions": 40},
                headers=auth_headers
            )
            assert over_pro_res.status_code == 400
            assert over_pro_res.json()["error_code"] == "TIER_QUESTION_LIMIT_EXCEEDED"
            print("  ✅ Pro user generation of 40 questions blocked (exceeds max 35)")

        # C. Test Team Tier Limits
        async with async_session_maker() as session:
            stmt = select(User).where(User.id == user_id)
            db_user = (await session.execute(stmt)).scalar_one()
            db_user.tier = "team"
            await session.commit()

        team_me = (await ac.get("/api/auth/me", headers=auth_headers)).json()["user"]
        assert team_me["tier"] == "team"
        assert team_me["monthly_limit"] == 250
        assert team_me["max_questions_per_quiz"] == 50
        assert team_me["monthly_questions_limit"] == 5000
        print(f"  ✅ Team Tier Verified via API: {team_me['monthly_limit']} uploads/mo, max {team_me['max_questions_per_quiz']} Qs/quiz, {team_me['monthly_questions_limit']} monthly Qs")

        # D. Test Institution Tier Limits
        async with async_session_maker() as session:
            stmt = select(User).where(User.id == user_id)
            db_user = (await session.execute(stmt)).scalar_one()
            db_user.tier = "institution"
            await session.commit()

        inst_me = (await ac.get("/api/auth/me", headers=auth_headers)).json()["user"]
        assert inst_me["tier"] == "institution"
        assert inst_me["monthly_limit"] == 750
        assert inst_me["max_questions_per_quiz"] == 100
        assert inst_me["monthly_questions_limit"] == 15000
        print(f"  ✅ Institution Tier Verified via API: {inst_me['monthly_limit']} uploads/mo, max {inst_me['max_questions_per_quiz']} Qs/quiz, {inst_me['monthly_questions_limit']} monthly Qs")

        # E. Test Guest Tier (Unauthenticated)
        with patch("routers.upload_and_generate.process_image", new_callable=AsyncMock) as mock_img, \
             patch("routers.upload_and_generate.generate_questions_from_content", return_value=mock_fake_questions):
            mock_img.return_value = {"text": "Content", "description": "", "file_path": "uploads/t.png"}

            # Guest requesting 10 questions -> blocked by 5 guest limit
            guest_over = await ac.post(
                "/api/generate/upload-and-generate",
                files={"files": ("test.png", b"fake_bytes", "image/png")},
                data={"qtype": "mcq", "num_questions": 10}
            )
            assert guest_over.status_code == 400
            assert guest_over.json()["error_code"] == "TIER_QUESTION_LIMIT_EXCEEDED"
            print("  ✅ Unauthenticated Guest blocked at 10 questions (exceeds guest ceiling of 5)")

            # Guest requesting 5 questions -> succeeds
            guest_valid = await ac.post(
                "/api/generate/upload-and-generate",
                files={"files": ("test.png", b"fake_bytes", "image/png")},
                data={"qtype": "mcq", "num_questions": 5}
            )
            assert guest_valid.status_code == 200
            assert guest_valid.json()["usage"]["kind"] == "guest"
            print("  ✅ Unauthenticated Guest succeeds with 5 questions")

    print("\n🎉 ALL USER TIER & LIMIT TESTS PASSED PERFECTLY!\n")

if __name__ == "__main__":
    asyncio.run(test_user_tier_limits_suite())
