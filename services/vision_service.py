# services/vision_service.py
import os
import re
import base64
import json
import asyncio
import logging
import mimetypes
from pathlib import Path
from typing import Optional, Dict, Any
from config import settings
from groq import Groq

from services.diagram_utils import contains_diagram, extract_diagram_text

logger = logging.getLogger(__name__)

# Configuration
GROQ_API_KEY = settings.GROQ_API_KEY
MODEL_NAME = "qwen/qwen3.6-27b"  # Using supported Groq vision model

# Validate API key
if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY not found in environment variables")

# Initialize Groq client
client = Groq(api_key=GROQ_API_KEY)

async def extract_text_and_description_with_vision(image_path: str) -> Dict[str, str]:
    """
    Extracts text and visual descriptions directly from an image using
    Groq Multimodal Vision Model (qwen/qwen3.6-27b).
    Falls back to UltimateOCRService (PyTesseract OCR) if API fails.
    """
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image file not found at {os.path.abspath(image_path)}")

    try:
        logger.info(f"Extracting content with Groq Vision LLM for: {image_path}")
        
        # Determine MIME type
        mime_type, _ = mimetypes.guess_type(image_path)
        if not mime_type:
            mime_type = "image/jpeg"

        # Base64 encode image
        with open(image_path, "rb") as img_file:
            b64_img = base64.b64encode(img_file.read()).decode("utf-8")

        prompt = (
            "Analyze this image thoroughly for educational quiz and test generation.\n"
            "Return ONLY valid JSON (no code blocks or markdown wrappers) with exactly two keys:\n"
            "{\n"
            '  "text": "Complete, accurate text transcription preserving headings, tables, and sentence structure.",\n'
            '  "description": "Detailed description of any visual figures, charts, diagrams, or math formulas."\n'
            "}"
        )

        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: client.chat.completions.create(
                model=MODEL_NAME,
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
                temperature=0.1,
                max_tokens=2048,
            )
        )

        raw = response.choices[0].message.content
        cleaned = re.sub(r"<think>.*?</think>", "", raw, flags=re.DOTALL).strip()
        cleaned = re.sub(r"^```json\s*", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"^```\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned).strip()

        try:
            data = json.loads(cleaned)
            extracted_text = data.get("text", "").strip()
            description = data.get("description", "").strip()
        except Exception:
            extracted_text = cleaned
            description = f"Extracted via Groq Vision from {os.path.basename(image_path)}"

        if extracted_text and not extracted_text.startswith("Error"):
            logger.info(f"Successfully extracted {len(extracted_text)} chars with Groq Vision")
            return {
                "text": extracted_text,
                "description": description,
                "file_path": image_path
            }
        else:
            raise ValueError(f"Vision model returned empty text: {cleaned}")

    except Exception as e:
        logger.warning(f"Vision model extraction failed for {image_path}: {e}. Falling back to OCR...")
        from services.ultimate_ocr_service import extract_text_from_path
        ocr_result = await extract_text_from_path(image_path)
        return {
            "text": ocr_result.get("text", ""),
            "description": ocr_result.get("description", ""),
            "file_path": image_path
        }

async def refine_ocr_text(text: str) -> str:
    """
    Refines the OCR-extracted text using the Groq model to correct errors
    and improve readability while preserving the original content.
    """
    try:
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: client.chat.completions.create(
                model=MODEL_NAME,
                messages=[
                    {
                        "role": "system", 
                        "content": "You are a text cleaning assistant that fixes OCR errors. "
                                 "Your task is to correct common OCR mistakes while preserving original meaning.\n"
                                 "1. Fix obvious OCR errors\n"
                                 "2. Preserve proper nouns and technical terms\n"
                                 "3. Return ONLY corrected text"
                    },
                    {
                        "role": "user",
                        "content": f"Correct OCR errors in the following text:\n\n{text}"
                    }
                ],
                temperature=0.1,
                max_tokens=2000,
            )
        )
        
        if response.choices and len(response.choices) > 0:
            cleaned_text = response.choices[0].message.content.strip()
            cleaned_text = re.sub(r"<think>.*?</think>", "", cleaned_text, flags=re.DOTALL).strip()
            return cleaned_text or text
        
    except Exception as e:
        logger.error(f"Error refining OCR text: {str(e)}")
        return text

async def describe_image_groq(image_path: str) -> str:
    """
    Extracts and refines text from an image using Vision LLM.
    """
    res = await extract_text_and_description_with_vision(image_path)
    return f"ORIGINAL TEXT:\n{'-'*40}\n{res['text']}\n\n\nDESCRIPTION:\n{'-'*40}\n{res['description']}"

async def describe_image_stub(path: str) -> str:
    """Async stub for processing image description."""
    return await describe_image_groq(path)

def describe_image_stub_sync(path: str) -> str:
    """Synchronous stub for processing image description."""
    try:
        return asyncio.run(describe_image_stub(path))
    except RuntimeError:
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(describe_image_stub(path))

async def describe_with_groq(image_path: str, prompt: str) -> str:
    """Helper function to get description from Groq API."""
    try:
        mime_type, _ = mimetypes.guess_type(image_path)
        if not mime_type:
            mime_type = "image/jpeg"
        with open(image_path, "rb") as img_file:
            img_base64 = base64.b64encode(img_file.read()).decode('utf-8')
        
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: client.chat.completions.create(
                model=MODEL_NAME,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:{mime_type};base64,{img_base64}"}
                            }
                        ]
                    }
                ],
                max_tokens=1000,
            )
        )
        raw = response.choices[0].message.content.strip()
        cleaned = re.sub(r"<think>.*?</think>", "", raw, flags=re.DOTALL).strip()
        return cleaned
    except Exception as e:
        return f"Could not generate description: {str(e)}"