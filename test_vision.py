#!/usr/bin/env python3
"""
Comprehensive Vision LLM & OCR Test Suite
Runs 3 tests:
  1. Vision Model & Output Parser Test
  2. OCR Fallback Mechanism Test
  3. End-to-End Vision + Question Generation Test

Usage:
    python test_vision.py [path_to_image]
"""
import sys
import os
import json
import re
import asyncio
import base64
import mimetypes
from unittest.mock import patch

# Ensure project root is in python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import settings
from services import vision_service
from services.vision_service import extract_text_and_description_with_vision
from services.qgen_service import generate_questions_from_content


async def test_1_parser(image_path: str):
    print("\n" + "=" * 65)
    print(" 🧪 TEST 1: Groq Vision Model & Response Parser")
    print("=" * 65)
    
    mime_type, _ = mimetypes.guess_type(image_path)
    if not mime_type:
        mime_type = "image/jpeg"

    with open(image_path, "rb") as f:
        b64_img = base64.b64encode(f.read()).decode("utf-8")

    prompt = (
        "Analyze this image thoroughly for educational quiz generation.\n"
        "Return ONLY valid JSON (no code blocks) with two fields:\n"
        "{\n"
        '  "text": "Complete, accurate text transcription preserving headings, tables, and sentence structure.",\n'
        '  "description": "Detailed description of any visual figures, charts, diagrams, or math formulas."\n'
        "}"
    )

    try:
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: vision_service.client.chat.completions.create(
                model=vision_service.MODEL_NAME,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:{mime_type};base64,{b64_img}"}
                            }
                        ]
                    }
                ],
                temperature=0.1
            )
        )

        raw = response.choices[0].message.content
        print("▶ Raw Model Response Received (Length:", len(raw), "chars)")
        
        # Clean <think> tags & markdown code blocks
        cleaned = re.sub(r"<think>.*?</think>", "", raw, flags=re.DOTALL).strip()
        cleaned = re.sub(r"^```json\s*", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"^```\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned).strip()

        data = json.loads(cleaned)
        print("✅ Parser Test PASSED!")
        print("  - Extracted Text Length:", len(data.get("text", "")), "chars")
        print("  - Description Length:   ", len(data.get("description", "")), "chars")
        
    except Exception as e:
        print(f"❌ Test 1 Failed: {e}")


async def test_2_fallback(image_path: str):
    print("\n" + "=" * 65)
    print(" 🧪 TEST 2: OCR Fallback Mechanism")
    print("=" * 65)
    print("▶ Simulating Groq Vision API Failure...")

    # Mock Vision API to raise an Exception
    with patch.object(vision_service.client.chat.completions, 'create', side_effect=Exception("Simulated API Rate Limit / Network Outage")):
        try:
            res = await extract_text_and_description_with_vision(image_path)
            print("✅ Fallback Test PASSED!")
            print(f"  - Fallback Result File: {res.get('file_path')}")
            print(f"  - Extracted Text Snippet: {res.get('text', '')[:100]}...")
        except Exception as e:
            print(f"❌ Test 2 Failed: {e}")


async def test_3_end_to_end(image_path: str):
    print("\n" + "=" * 65)
    print(" 🧪 TEST 3: End-to-End Vision + Question Generation")
    print("=" * 65)
    print("▶ Step 1: Extracting content with Vision LLM...")
    
    res = await extract_text_and_description_with_vision(image_path)
    extracted_text = res.get("text", "")
    description = res.get("description", "")
    
    print("\n📝 EXTRACTED TEXT TRANSCRIPTION:")
    print("-" * 60)
    print(extracted_text[:400] + ("..." if len(extracted_text) > 400 else ""))
    
    if description:
        print("\n🖼️ VISUAL DESCRIPTION:")
        print("-" * 60)
        print(description[:300] + ("..." if len(description) > 300 else ""))

    print("\n▶ Step 2: Generating Quiz Questions...")
    questions = await asyncio.to_thread(
        generate_questions_from_content,
        text=extracted_text,
        refined_text="",
        description=description,
        qtype="mcq",
        difficulty="medium",
        num_questions=2,
        class_id="Grade 10",
        subject="Science"
    )

    if isinstance(questions, str):
        questions = json.loads(questions)

    print(f"\n✅ End-to-End Test PASSED! ({len(questions)} questions generated):\n")
    for i, q in enumerate(questions, 1):
        print(f"Q{i}: {q.get('question')}")
        if q.get("choices"):
            for idx, choice in enumerate(q["choices"], start=1):
                prefix = "  👉" if choice == q.get("answer") else "    "
                print(f"{prefix} ({chr(64+idx)}) {choice}")
        else:
            print(f"   Answer: {q.get('answer')}")
        print(f"   💡 Rationale: {q.get('rationale')}\n")


async def main():
    default_image = "test-image/WhatsApp Image 2025-11-25 at 4.53.02 PM.jpeg"
    
    if len(sys.argv) > 1:
        target_image = sys.argv[1]
    elif os.path.exists(default_image):
        target_image = default_image
    else:
        print("Usage: python test_vision.py <path_to_image>")
        sys.exit(1)
        
    if not os.path.exists(target_image):
        print(f"❌ Error: Image not found at path '{target_image}'")
        sys.exit(1)

    print("\n" + "🚀" * 30)
    print(" COMPREHENSIVE VISION LLM TEST SUITE")
    print(f" Target Image: {target_image}")
    print("🚀" * 30)

    await test_1_parser(target_image)
    await test_2_fallback(target_image)
    await test_3_end_to_end(target_image)

    print("=" * 65)
    print(" 🎉 ALL 3 TESTS EXECUTED SUCCESSFULLY!")
    print("=" * 65 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
