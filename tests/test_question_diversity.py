import sys
import uuid
import asyncio
from unittest.mock import patch, AsyncMock, MagicMock
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select

from main import app
from database import engine, Base, async_session_maker
from models.user import User
from services.qgen_service import (
    sample_document_context,
    build_prompt,
    generate_questions_from_content,
    FOCUS_ANGLES
)

async def test_question_diversity_and_modes():
    print("\n🎯 ===============================================================")
    print("   STARTING QUESTION DIVERSITY & GENERATION MODES TEST SUITE")
    print("=================================================================\n")

    # -----------------------------------------------------------------
    # TEST 1: Intelligent Multi-Chunk Document Sampling
    # -----------------------------------------------------------------
    print("👉 Test 1: Testing Multi-Chunk Document Sampling...")
    # Short document (< 3500 chars)
    short_doc = "Photosynthesis is the process by which green plants make food."
    sampled_short = sample_document_context(short_doc, max_chars=3500)
    assert sampled_short == short_doc
    print("  ✅ Short document preserved completely without truncation")

    # Long document (10,000 characters across multiple pages)
    long_doc = (
        "SECTION 1: Introduction to Cellular Respiration and Glycolysis. " * 50 +
        "SECTION 2: The Krebs Cycle and Citric Acid Pathway in Mitochondria. " * 50 +
        "SECTION 3: The Electron Transport Chain and ATP Synthase Mechanism. " * 50
    )
    assert len(long_doc) > 6000

    # Sample batch 0 of 3 (early section)
    chunk_0 = sample_document_context(long_doc, max_chars=1500, chunk_index=0, total_chunks=3, random_jitter=False)
    # Sample batch 2 of 3 (later section)
    chunk_2 = sample_document_context(long_doc, max_chars=1500, chunk_index=2, total_chunks=3, random_jitter=False)

    assert "SECTION 1" in chunk_0
    assert "SECTION 3" in chunk_2
    assert chunk_0 != chunk_2
    print("  ✅ Long document sampled across different sections (Section 1 in batch 0, Section 3 in batch 2)")

    # -----------------------------------------------------------------
    # TEST 2: Distinct Prompt Architectures for Exam vs. Practice Modes
    # -----------------------------------------------------------------
    print("\n👉 Test 2: Testing Prompt Differentiation for Exam vs Practice Modes...")
    exam_prompt = build_prompt(
        text=short_doc,
        refined_text="",
        description="",
        qtype="mcq",
        difficulty="medium",
        num_questions=5,
        mode="exam",
        variation_seed=0
    )
    assert "EXAM & ASSESSMENT MODE (Summative Rigor)" in exam_prompt
    assert "plausible, realistic distractors" in exam_prompt
    assert "preventing students from guessing by pure rote recall" in exam_prompt
    assert FOCUS_ANGLES[0] in exam_prompt

    practice_prompt = build_prompt(
        text=short_doc,
        refined_text="",
        description="",
        qtype="mcq",
        difficulty="medium",
        num_questions=5,
        mode="practice",
        variation_seed=1
    )
    assert "SELF-STUDY & PRACTICE MODE (Formative Mastery)" in practice_prompt
    assert "student self-study, active recall, and conceptual review" in practice_prompt
    assert "Rationales must be rich, encouraging" in practice_prompt
    assert FOCUS_ANGLES[1] in practice_prompt
    assert exam_prompt != practice_prompt
    print("  ✅ Exam Mode and Practice Mode generate distinct pedagogical operational directives")

    # -----------------------------------------------------------------
    # TEST 3: Temperature and Parameter Passing to Groq
    # -----------------------------------------------------------------
    print("\n👉 Test 3: Verifying Groq Model Temperature Tuning (0.6 for Exam, 0.5 for Practice)...")
    mock_response = MagicMock()
    mock_choice = MagicMock()
    mock_choice.message.content = '[{"question": "What is ATP?", "answer": "A", "choices": ["Energy", "Water", "Gas", "Lipid"], "rationale": "ATP stores energy.", "qtype": "mcq", "difficulty": "medium", "blooms_level": "Remember"}]'
    mock_response.choices = [mock_choice]

    with patch("services.qgen_service.groq_client.chat.completions.create", return_value=mock_response) as mock_groq:
        # Exam mode call -> temperature must be 0.6
        generate_questions_from_content(text=short_doc, num_questions=1, mode="exam")
        assert mock_groq.call_count == 1
        call_kwargs = mock_groq.call_args[1]
        assert call_kwargs["temperature"] == 0.6
        assert call_kwargs["top_p"] == 0.9

        # Practice mode call -> temperature must be 0.5
        generate_questions_from_content(text=short_doc, num_questions=1, mode="practice")
        assert mock_groq.call_count == 2
        call_kwargs_practice = mock_groq.call_args[1]
        assert call_kwargs_practice["temperature"] == 0.5
    print("  ✅ Optimal temperature tuning verified (0.6 for Exam, 0.5 for Practice)")

    # -----------------------------------------------------------------
    # TEST 4: FastAPI Endpoints Acceptance of Mode
    # -----------------------------------------------------------------
    print("\n👉 Test 4: Testing Endpoints Integration with Mode Parameter...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Register test user
        user_email = f"diversity_{uuid.uuid4().hex[:6]}@edtech.com"
        reg_res = await ac.post("/api/auth/register", json={
            "email": user_email,
            "password": "Password123!",
            "full_name": "Dr. Sarah Connor"
        })
        token = reg_res.json()["access_token"]
        auth_headers = {"Authorization": f"Bearer {token}"}

        mock_generated = [
            {
                "question": "Which organelle synthesizes ATP?",
                "answer": "A",
                "choices": ["Mitochondria", "Ribosome", "Nucleus", "Vacuole"],
                "rationale": "Mitochondria carry out oxidative phosphorylation.",
                "blooms_level": "Remember",
                "difficulty": "medium",
                "qtype": "mcq"
            }
        ]

        # 4A. Synchronous endpoint /api/generate/upload-and-generate with mode="exam"
        with patch("routers.upload_and_generate.process_image", new_callable=AsyncMock) as mock_img, \
             patch("routers.upload_and_generate.generate_questions_from_content", return_value=mock_generated) as mock_gen:
            mock_img.return_value = {"text": "Cell Biology Text", "description": "", "file_path": "uploads/bio.png"}

            files = {"files": ("biology.png", b"fake_content", "image/png")}
            res_exam = await ac.post(
                "/api/generate/upload-and-generate",
                files=files,
                data={"qtype": "mcq", "num_questions": 1, "mode": "exam"},
                headers=auth_headers
            )
            assert res_exam.status_code == 200, res_exam.text
            assert mock_gen.call_args[1]["mode"] == "exam"
            print("  ✅ /api/generate/upload-and-generate accepted mode='exam'")

            # 4B. Synchronous endpoint with mode="practice"
            res_practice = await ac.post(
                "/api/generate/upload-and-generate",
                files={"files": ("biology.png", b"fake_content", "image/png")},
                data={"qtype": "mcq", "num_questions": 1, "mode": "practice"},
                headers=auth_headers
            )
            assert res_practice.status_code == 200, res_practice.text
            assert mock_gen.call_args[1]["mode"] == "practice"
            print("  ✅ /api/generate/upload-and-generate accepted mode='practice'")

        # 4C. Async endpoint /api/tasks/generate-async with mode parameter
        with patch("routers.tasks.process_image", new_callable=AsyncMock) as mock_task_img:
            mock_task_img.return_value = {"text": "Async Bio Text", "description": "", "file_path": "uploads/bio.png"}
            res_async = await ac.post(
                "/api/tasks/generate-async",
                files={"files": ("biology.png", b"fake_content", "image/png")},
                data={"qtype": "mcq", "num_questions": 1, "mode": "practice"},
                headers=auth_headers
            )
            assert res_async.status_code == 202, res_async.text
            task_data = res_async.json()
            assert "task_id" in task_data
            assert task_data["status"] == "queued"
            print(f"  ✅ /api/tasks/generate-async accepted mode='practice' (Task ID: {task_data['task_id'][:8]}...)")

    print("\n🎉 ALL QUESTION DIVERSITY & MODE TESTS PASSED PERFECTLY!\n")

if __name__ == "__main__":
    asyncio.run(test_question_diversity_and_modes())
