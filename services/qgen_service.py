import os
from dotenv import load_dotenv
import openai

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY


def build_prompt(text: str, description: str, qtype: str, difficulty: str) -> str:
    prompt = f"""
You are an exam question generator. Produce 3 high-quality {qtype} questions at {difficulty} difficulty.
Provide output as a JSON array where each element has: question, answer, choices (if MCQ) and rationale.

EXTRACTED_TEXT:
{text}

IMAGE_DESCRIPTION:
{description}

Respond only in JSON.
"""
    return prompt


def generate_questions_from_content(text: str, description: str, qtype: str, difficulty: str):
    prompt = build_prompt(text, description, qtype, difficulty)
    try:
        resp = openai.ChatCompletion.create(
            model="gpt-4o-mini",  # change to available model in your account
            messages=[{"role": "user", "content": prompt}],
            max_tokens=800,
            temperature=0.2,
        )
        content = resp.choices[0].message["content"].strip()
        return content
    except Exception as e:
        return f"[qgen_error] {e}"
