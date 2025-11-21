import os
from dotenv import load_dotenv
from groq import Groq
import json

# Load environment variables
load_dotenv()

# Initialize Groq client
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Model configuration
MODEL_NAME = "llama-3.1-8b-instant"  # Using Groq's LLaMA 3 70B model


def build_prompt(text: str, refined_text: str, description: str, qtype: str, difficulty: str, num_questions: int = 3) -> str:
    """
    Build a prompt for question generation using Groq.
    """
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
    "rationale": "The book focuses on teaching financial literacy."
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
""",
        'true_false': """
TRUE/FALSE QUESTIONS - FOLLOW THESE RULES:

1. RETURN A JSON ARRAY OF QUESTION OBJECTS
2. EACH QUESTION MUST HAVE:
   - "question": A statement (string)
   - "answer": "True" or "False" (exactly, case-sensitive)
   - "rationale": Explanation (string)

EXAMPLE:
```json
[
  {
    "question": "The book was published in 2020.",
    "answer": "True",
    "rationale": "The book was indeed published in 2020."
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

EXAMPLE:
```json
[
  {
    "question": "What is the main purpose of the book?",
    "answer": "To teach financial literacy and wealth building strategies.",
    "rationale": "The book focuses on financial education."
  }
]
```
"""
    }

    # Add difficulty-specific instructions
    difficulty_instructions = {
        'easy': "Use simple language and focus on basic concepts. Questions should test recall and basic understanding.",
        'medium': "Include some complexity in the questions and answers. Test application of concepts.",
        'hard': "Create challenging questions that require analysis, evaluation, or synthesis of information."
    }

    return f"""You are an expert educational content creator. Generate EXACTLY {num_questions} high-quality {qtype} questions at {difficulty} difficulty level.

IMPORTANT INSTRUCTIONS - READ CAREFULLY:
1. CONTEXT TO USE (base your questions on this content):
   - ORIGINAL TEXT: {text[:1000]}{'...' if len(text) > 1000 else ''}
   - REFINED TEXT: {refined_text[:1000] if refined_text else 'N/A'}{'...' if refined_text and len(refined_text) > 1000 else ''}
   - IMAGE DESCRIPTION: {description if description else 'N/A'}

2. DIFFICULTY LEVEL: {difficulty_instructions.get(difficulty, '')}

3. QUESTION TYPE REQUIREMENTS:
{qtype_instructions.get(qtype, '')}

4. RESPONSE FORMAT REQUIREMENTS:
   - Respond ONLY with a valid JSON array of question objects
   - Do NOT include any additional text or markdown formatting
   - The JSON must be properly formatted and parseable
   - Generate EXACTLY {num_questions} questions
   - If you can't generate the requested number of questions, return an error object

5. FINAL REMINDER - YOUR RESPONSE MUST:
   - Be valid JSON that can be parsed with json.loads()
   - Include ALL required fields for each question type
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
    max_retries: int = 2
) -> str:
    """
    Generate questions from the given text using Groq's LLaMA model.
    
    Args:
        text: The original text content
        refined_text: The text after OCR processing and refinement (default: "")
        description: Description of the image (if any, default: "")
        qtype: Type of questions to generate ('mcq', 'true_false', 'short_answer')
        difficulty: Difficulty level ('easy', 'medium', 'hard')
        num_questions: Number of questions to generate (default: 3)
        max_retries: Maximum number of retry attempts if response is invalid
        
    Returns:
        str: JSON string containing generated questions or an error message
    """
    """
    Generate questions from the given text using Groq's LLaMA model.
    
    Args:
        text: The original text content
        refined_text: The text after OCR processing and refinement (default: "")
        description: Description of the image (if any, default: "")
        qtype: Type of questions to generate ('mcq', 'true_false', 'short_answer')
        difficulty: Difficulty level ('easy', 'medium', 'hard')
        num_questions: Number of questions to generate (default: 3)
        max_retries: Maximum number of retry attempts if response is invalid
        
    Returns:
        str: JSON string containing generated questions or an error message
    """
    if not text.strip() and not refined_text.strip():
        return json.dumps([{"error": "No text content provided"}])
    
    if not os.getenv("GROQ_API_KEY"):
        return json.dumps([{"error": "GROQ_API_KEY not found in environment variables"}])
    
    # If no refined text is provided, use the original text
    if not refined_text.strip():
        refined_text = text
        
    prompt = build_prompt(text, refined_text, description, qtype, difficulty, num_questions)
    
    for attempt in range(max_retries + 1):
        try:
            # Call Groq API
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
                max_tokens=2048,
                top_p=0.9,
                stream=False,
                stop=None,
            )
            
            # Extract content from response
            if not completion.choices or not completion.choices[0].message.content:
                if attempt == max_retries:
                    return json.dumps([{"error": "Empty response from Groq API"}])
                continue
                
            content = completion.choices[0].message.content.strip()
            
            # Clean up the response
            if '```json' in content:
                content = content.split('```json')[1].split('```')[0].strip()
            elif '```' in content:
                content = content.split('```')[1].strip()
                if content.startswith('json'):
                    content = content[4:].strip()
            
            # Parse the JSON
            questions = json.loads(content)
            
            # Ensure it's a list
            if not isinstance(questions, list):
                questions = [questions]
                
            # Process each question to ensure it has the required fields
            processed_questions = []
            for q in questions:
                if not isinstance(q, dict):
                    continue
                    
                # Create a new question with required fields
                processed_q = {
                    "question": q.get("question", "").strip() or "No question provided",
                    "answer": "",
                    "rationale": q.get("rationale", "No rationale provided.").strip(),
                    "qtype": qtype,
                    "difficulty": difficulty
                }
                
                # Handle different response formats
                if "answer" in q:
                    processed_q["answer"] = str(q["answer"]).strip()
                elif "correct" in q:
                    processed_q["answer"] = str(q["correct"]).strip()
                    
                # For MCQs, handle choices
                if qtype == "mcq":
                    if "choices" in q and isinstance(q["choices"], list):
                        processed_q["choices"] = [str(choice).strip() for choice in q["choices"][:4]]
                    elif "options" in q and isinstance(q["options"], list):
                        processed_q["choices"] = [str(option).strip() for option in q["options"][:4]]
                    else:
                        # Generate default choices if none provided
                        processed_q["choices"] = ["Option A", "Option B", "Option C", "Option D"]
                        
                    # Ensure we have exactly 4 choices
                    while len(processed_q["choices"]) < 4:
                        processed_q["choices"].append(f"Option {chr(65 + len(processed_q['choices']))}")
                        
                    # If answer is A, B, C, or D, map it to the corresponding choice
                    if processed_q["answer"] in ["A", "B", "C", "D"]:
                        idx = ord(processed_q["answer"].upper()) - ord('A')
                        if 0 <= idx < len(processed_q["choices"]):
                            processed_q["answer"] = processed_q["choices"][idx]
                
                # Ensure required fields are present
                if not processed_q["question"]:
                    print(f"Warning: Question is missing a question text: {q}")
                    continue
                    
                if not processed_q["answer"]:
                    print(f"Warning: Question is missing an answer: {q}")
                    continue
                    
                processed_questions.append(processed_q)
            
            return json.dumps(processed_questions[:num_questions])
                
        except json.JSONDecodeError as e:
            if attempt == max_retries:
                return json.dumps([{"error": f"Invalid JSON response: {str(e)}"}])
            continue
            
        except Exception as e:
            if attempt == max_retries:
                return json.dumps([{"error": f"Error generating questions: {str(e)}"}])
            continue
            
    return json.dumps([{"error": "Failed to generate questions after multiple attempts"}])
