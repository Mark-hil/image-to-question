import os
from config import settings
from groq import Groq
import json

# Initialize Groq client
groq_client = Groq(api_key=settings.GROQ_API_KEY)

# Model configuration
MODEL_NAME = "llama-3.1-8b-instant"  # Using Groq's LLaMA 3 70B model


def build_prompt(
    text: str, 
    refined_text: str, 
    description: str, 
    qtype: str, 
    difficulty: str, 
    num_questions: int = 3,
    class_id: str = None,
    subject: str = None,
    blooms_level: str = "all"
) -> str:
    """
    Build a prompt for question generation using Groq.
    
    Args:
        text: The original text content
        refined_text: The text after OCR processing and refinement
        description: Description of the image (if any)
        qtype: Type of questions to generate
        difficulty: Difficulty level
        num_questions: Number of questions to generate
        class_id: The class/grade level the questions are for (e.g., 'Grade 5')
        subject: The subject of the questions (e.g., 'Math', 'Science')
        blooms_level: Target Bloom's Taxonomy cognitive level ('all', 'Remember', 'Understand', 'Apply', 'Analyze', 'Evaluate', 'Create')
    """
    # Add class and subject context to the prompt
    context_parts = []
    if class_id:
        context_parts.append(f"Class/Grade: {class_id}")
    if subject:
        context_parts.append(f"Subject: {subject}")
    
    context = "\n".join(context_parts)
    if context:
        context = f"CONTEXT:\n{context}\n\n"

    blooms_spec_instruction = ""
    if blooms_level and blooms_level.lower() != "all":
        target_cap = blooms_level.strip().capitalize()
        blooms_spec_instruction = f"\n5. MANDATORY BLOOM'S TAXONOMY SPECIFICATION:\n   - User target cognitive level: '{target_cap}'\n   - EVERY generated question MUST target the '{target_cap}' level of Bloom's Taxonomy cognitive domain.\n   - Set \"blooms_level\": \"{target_cap}\" in the JSON object for each question.\n"

    # Define question type specific instructions
    qtype_instructions = {
        'mcq': """
MULTIPLE CHOICE (MCQ) QUESTIONS - FOLLOW THESE RULES STRICTLY:

1. YOU MUST RETURN A JSON ARRAY OF QUESTION OBJECTS.
2. EACH QUESTION OBJECT MUST HAVE:
   - "question": The question text (string, required)
   - "answer": The correct answer ("A", "B", "C", or "D") (required)
   - "choices": An array of exactly 4 strings (required)
   - "rationale": Explanation of the answer (string, required)
   - "blooms_level": Bloom's Taxonomy cognitive level ("Remember", "Understand", "Apply", "Analyze", "Evaluate", or "Create") (string, required)

3. EXAMPLE OF A VALID RESPONSE:
```json
[
  {
    "question": "What is the main theme of the book?",
    "answer": "A",
    "choices": [
      "Financial education and wealth building",
      "Historical events",
      "Scientific discoveries",
      "Fictional stories"
    ],
    "rationale": "The book focuses on teaching financial literacy.",
    "blooms_level": "Understand"
  }
]
```

4. IMPORTANT RULES:
   - Return ONLY the JSON array, nothing else
   - No markdown formatting (no ```json or ```)
   - No additional text before or after the JSON
   - All questions must be different
   - All choices must be plausible but only one correct
   - The 'answer' must be one of: "A", "B", "C", or "D"
   - The 'choices' array must have exactly 4 items
   - Each choice should be a complete sentence or phrase
   - The rationale should explain why the answer is correct
   - Tag each question with its exact Bloom's Taxonomy level ("Remember", "Understand", "Apply", "Analyze", "Evaluate", or "Create")
""",
        'true_false': """
TRUE/FALSE QUESTIONS - FOLLOW THESE RULES:

1. RETURN A JSON ARRAY OF QUESTION OBJECTS
2. EACH QUESTION MUST HAVE:
   - "question": A statement (string)
   - "answer": "True" or "False" (exactly, case-sensitive)
   - "rationale": Explanation (string)
   - "blooms_level": Bloom's Taxonomy level ("Remember", "Understand", "Apply", "Analyze", "Evaluate", or "Create") (string)

EXAMPLE:
```json
[
  {
    "question": "The book was published in 2020.",
    "answer": "True",
    "rationale": "The book was indeed published in 2020.",
    "blooms_level": "Remember"
  }
]
```
""",
        'short_answer': """
SHORT ANSWER QUESTIONS - FOLLOW THESE RULES:

1. RETURN A JSON ARRAY OF QUESTION OBJECTS
2. EACH QUESTION MUST HAVE:
   - "question": The question (string)
   - "answer": A brief answer (1-2 sentences, string)
   - "rationale": Explanation (string)
   - "blooms_level": Bloom's Taxonomy level ("Remember", "Understand", "Apply", "Analyze", "Evaluate", or "Create") (string)

EXAMPLE:
```json
[
  {
    "question": "What is the main purpose of the book?",
    "answer": "To teach financial literacy and wealth building strategies.",
    "rationale": "The book focuses on financial education.",
    "blooms_level": "Analyze"
  }
]
```
"""
    }

    # Add difficulty-specific instructions
    difficulty_instructions = {
        'easy': "Use simple language and focus on basic concepts. Questions should test recall and basic understanding (Bloom's: Remember, Understand).",
        'medium': "Include some complexity in the questions and answers. Test application of concepts (Bloom's: Apply, Analyze).",
        'hard': "Create challenging questions that require analysis, evaluation, or synthesis of information (Bloom's: Evaluate, Create)."
    }

    return f"""{context}You are an expert educational content creator. Generate EXACTLY {num_questions} high-quality {qtype} questions at {difficulty} difficulty level for {class_id} in {subject}.

IMPORTANT INSTRUCTIONS - READ CAREFULLY:
1. CONTEXT TO USE (base your questions on this content):
   - ORIGINAL TEXT: {text[:1000]}{'...' if len(text) > 1000 else ''}
   - REFINED TEXT: {refined_text[:1000] if refined_text else 'N/A'}{'...' if refined_text and len(refined_text) > 1000 else ''}
   - IMAGE DESCRIPTION: {description if description else 'N/A'}

2. DIFFICULTY LEVEL: {difficulty_instructions.get(difficulty, '')}

3. QUESTION TYPE REQUIREMENTS:
{qtype_instructions.get(qtype, '')}
{blooms_spec_instruction}
4. RESPONSE FORMAT REQUIREMENTS:
   - Respond ONLY with a valid JSON array of question objects
   - Do NOT include any additional text or markdown formatting
   - The JSON must be properly formatted and parseable
   - Generate EXACTLY {num_questions} questions
   - Include "blooms_level" for every question
   - If you can't generate the requested number of questions, return an error object

5. FINAL REMINDER - YOUR RESPONSE MUST:
   - Be valid JSON that can be parsed with json.loads()
   - Include ALL required fields for each question type (including blooms_level)
   - Have no text before or after the JSON array
   - Be properly escaped and formatted

6. EXAMPLE OF A VALID RESPONSE (for {qtype}):
{qtype_instructions.get(qtype, '').split('EXAMPLE:')[-1].split('```json')[-1].split('```')[0].strip() if 'EXAMPLE:' in qtype_instructions.get(qtype, '') else '[]'}
"""


def generate_questions_from_content(
    text: str,
    refined_text: str = "",
    description: str = "",
    qtype: str = "mcq",
    difficulty: str = "medium",
    num_questions: int = 3,
    max_retries: int = 2,
    class_id: str = None,
    subject: str = None,
    blooms_level: str = "all"
) -> str:
    """
    Generate questions from the given text using Groq's LLaMA model.
    """
    if not text.strip() and not refined_text.strip():
        return json.dumps([{"error": "No text content provided"}])
    
    if not settings.GROQ_API_KEY:
        return json.dumps([{"error": "GROQ_API_KEY not found in environment variables"}])
    
    # If no refined text is provided, use the original text
    if not refined_text.strip():
        refined_text = text
        
    BATCH_SIZE = 10
    total_needed = max(1, num_questions)
    all_processed = []

    # Loop through batches to handle large requests (e.g. 50 questions) without LLM token truncation
    remaining = total_needed
    while remaining > 0:
        chunk_count = min(BATCH_SIZE, remaining)
        prompt = build_prompt(text, refined_text, description, qtype, difficulty, chunk_count, class_id, subject, blooms_level)
        
        batch_success = False
        for attempt in range(max_retries + 1):
            try:
                completion = groq_client.chat.completions.create(
                    model=MODEL_NAME,
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a helpful assistant that generates educational questions in JSON format. Follow all instructions precisely."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    temperature=0.3,
                    max_tokens=4096,
                    top_p=0.9,
                    stream=False,
                    stop=None,
                )
                
                if not completion.choices or not completion.choices[0].message.content:
                    continue
                    
                content = completion.choices[0].message.content.strip()
                
                if '```json' in content:
                    content = content.split('```json')[1].split('```')[0].strip()
                elif '```' in content:
                    content = content.split('```')[1].strip()
                    if content.startswith('json'):
                        content = content[4:].strip()
                
                questions = json.loads(content)
                if not isinstance(questions, list):
                    questions = [questions]
                    
                for q in questions:
                    if not isinstance(q, dict):
                        continue
                        
                    valid_blooms = ["Remember", "Understand", "Apply", "Analyze", "Evaluate", "Create"]
                    
                    if blooms_level and blooms_level.lower() != "all":
                        target_blooms = blooms_level.strip().capitalize()
                        final_blooms = target_blooms if target_blooms in valid_blooms else "Understand"
                    else:
                        default_blooms = "Understand"
                        if difficulty == "easy":
                            default_blooms = "Remember"
                        elif difficulty == "hard":
                            default_blooms = "Analyze"
                        raw_blooms = str(q.get("blooms_level", "")).strip().capitalize()
                        final_blooms = raw_blooms if raw_blooms in valid_blooms else default_blooms

                    processed_q = {
                        "question": q.get("question", "").strip() or "No question provided",
                        "answer": "",
                        "rationale": q.get("rationale", "No rationale provided.").strip(),
                        "qtype": qtype,
                        "difficulty": difficulty,
                        "blooms_level": final_blooms
                    }
                    
                    if "answer" in q:
                        processed_q["answer"] = str(q["answer"]).strip()
                    elif "correct" in q:
                        processed_q["answer"] = str(q["correct"]).strip()
                        
                    if qtype == "mcq":
                        if "choices" in q and isinstance(q["choices"], list):
                            processed_q["choices"] = [str(choice).strip() for choice in q["choices"][:4]]
                        elif "options" in q and isinstance(q["options"], list):
                            processed_q["choices"] = [str(option).strip() for option in q["options"][:4]]
                        else:
                            processed_q["choices"] = ["Option A", "Option B", "Option C", "Option D"]
                            
                        while len(processed_q["choices"]) < 4:
                            processed_q["choices"].append(f"Option {chr(65 + len(processed_q['choices']))}")
                            
                        if processed_q["answer"] in ["A", "B", "C", "D"]:
                            idx = ord(processed_q["answer"].upper()) - ord('A')
                            if 0 <= idx < len(processed_q["choices"]):
                                processed_q["answer"] = processed_q["choices"][idx]
                    
                    if not processed_q["question"] or not processed_q["answer"]:
                        continue
                        
                    all_processed.append(processed_q)
                
                batch_success = True
                break
                    
            except Exception as e:
                if attempt == max_retries:
                    print(f"Batch generation error: {str(e)}")
                continue

        if not batch_success:
            break
            
        remaining -= chunk_count

    if not all_processed:
        return json.dumps([{"error": "Failed to generate questions"}])

    return json.dumps(all_processed[:num_questions])
