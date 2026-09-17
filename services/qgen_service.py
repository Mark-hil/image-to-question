import os
import random
from typing import Optional, List
from config import settings
from groq import Groq
import json

# Initialize Groq client
groq_client = Groq(api_key=settings.GROQ_API_KEY)

# Model configuration
MODEL_NAME = "openai/gpt-oss-120b"  # Using Groq's LLaMA 3 70B model

# Industry-standard cognitive focus angles for dynamic question variety
FOCUS_ANGLES: List[str] = [
    "Focus on scenario-based application and real-world problem-solving situations.",
    "Focus on cause-and-effect relationships, underlying mechanisms, and sequential processes.",
    "Focus on comparative evaluation, distinguishing similar concepts, and nuanced technical differences.",
    "Focus on core principles, foundational definitions, and critical conceptual rules.",
    "Focus on synthesis, interpreting diagrams/descriptions, and multi-step logical deduction.",
    "Focus on common edge cases, exceptions to rules, and subtle misconception traps."
]


def sample_document_context(
    content: str,
    max_chars: int = 3500,
    chunk_index: int = 0,
    total_chunks: int = 1,
    random_jitter: bool = True
) -> str:
    """
    Intelligently samples representative content across the entire uploaded document.
    If the text exceeds max_chars, it distributes windows across the document length
    based on chunk_index / total_chunks, ensuring multi-page PDFs and slides are assessed.
    """
    if not content:
        return ""
    cleaned = content.strip()
    if len(cleaned) <= max_chars:
        return cleaned

    usable_range = len(cleaned) - max_chars
    stride = usable_range // max(1, total_chunks)
    base_start = min(usable_range, chunk_index * stride)

    if random_jitter and usable_range > 300:
        jitter = random.randint(-120, 120)
        start_idx = max(0, min(usable_range, base_start + jitter))
    else:
        start_idx = base_start

    excerpt = cleaned[start_idx:start_idx + max_chars]
    section_num = (start_idx * total_chunks // usable_range) + 1 if usable_range > 0 else 1
    return f"[Document Excerpt (Section {section_num} of {total_chunks}, ~{len(cleaned)} total characters)]:\n...{excerpt}..."


def build_prompt(
    text: str, 
    refined_text: str, 
    description: str, 
    qtype: str, 
    difficulty: str, 
    num_questions: int = 3,
    class_id: str = None,
    subject: str = None,
    blooms_level: str = "all",
    mode: str = "exam",
    chunk_index: int = 0,
    total_chunks: int = 1,
    variation_seed: Optional[int] = None
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
        mode: 'exam' (summative assessment with plausible distractors) or 'practice' (formative self-study with hints)
        chunk_index: Current batch window index
        total_chunks: Total batches across the document
        variation_seed: Optional seed for cognitive angle rotation
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

    # Parse multi-select question formats
    if isinstance(qtype, list):
        selected_types = [t.strip().lower() for t in qtype if t.strip()]
    else:
        selected_types = [t.strip().lower() for t in str(qtype).split(",") if t.strip()]
    if not selected_types:
        selected_types = ['mcq']

    # Parse multi-select difficulty levels
    if isinstance(difficulty, list):
        selected_diffs = [d.strip().lower() for d in difficulty if d.strip()]
    else:
        selected_diffs = [d.strip().lower() for d in str(difficulty).split(",") if d.strip()]
    if not selected_diffs:
        selected_diffs = ['medium']

    # Parse multi-select Bloom's cognitive levels
    if isinstance(blooms_level, list):
        selected_blooms = [b.strip().capitalize() for b in blooms_level if b.strip()]
    else:
        selected_blooms = [b.strip().capitalize() for b in str(blooms_level).split(",") if b.strip()]
    if not selected_blooms:
        selected_blooms = ['All']

    is_all_blooms = any(b.lower() == 'all' for b in selected_blooms)

    blooms_spec_instruction = ""
    if not is_all_blooms:
        blooms_str = ", ".join(selected_blooms)
        blooms_spec_instruction = f"""
MANDATORY BLOOM'S TAXONOMY SPECIFICATION:
- Target cognitive level(s): {blooms_str}
- EVERY generated question MUST target one of these selected Bloom's cognitive domain levels: {blooms_str}.
- Set "blooms_level" to the exact matched level ("Remember", "Understand", "Apply", "Analyze", "Evaluate", or "Create") in each question object.
"""

    # Generation Mode Specification
    mode_normalized = (mode or "exam").lower()
    if mode_normalized == "practice":
        mode_header = "SELF-STUDY & PRACTICE MODE (Formative Mastery)"
        mode_instruction = """- Design formative questions optimized for student self-study, active recall, and conceptual review.
- Reinforce foundational comprehension, key definitions, and step-by-step logic.
- Rationales must be rich, encouraging, and detailed to guide student self-correction and mastery.
- Frame answer explanations with clear hints and educational reasoning."""
    else:
        mode_header = "EXAM & ASSESSMENT MODE (Summative Rigor)"
        mode_instruction = """- Design rigorous, exam-grade assessment items for tests, quizzes, and LMS exams.
- Craft highly plausible, realistic distractors (wrong choices) that deliberately target common student misconceptions, subtle calculation traps, or false cognates.
- Use novel situational scenarios and applied problem statements rather than direct verbatim quotes, preventing students from guessing by pure rote recall.
- Ensure all questions are defensible with pedagogical rationales."""

    # Dynamic cognitive focus angle
    seed_idx = variation_seed if variation_seed is not None else random.randint(0, len(FOCUS_ANGLES) - 1)
    focus_angle = FOCUS_ANGLES[seed_idx % len(FOCUS_ANGLES)]

    # Difficulty instructions mapping
    difficulty_instructions = {
        'easy': "Easy: Use simple language and focus on basic concepts. Questions test recall and foundational understanding.",
        'medium': "Medium: Include analytical depth. Test application and comprehension of concepts.",
        'hard': "Hard: Create challenging questions requiring critical analysis, evaluation, or multi-step reasoning."
    }
    diff_text = " / ".join([difficulty_instructions.get(d, d.capitalize()) for d in selected_diffs])

    # Question format rules and examples
    format_rules = {
        'mcq': """- MULTIPLE CHOICE (MCQ):
  * "qtype": "mcq"
  * "question": The question text (string)
  * "answer": The correct choice letter ("A", "B", "C", or "D") OR the full text of the correct choice
  * "choices": An array of EXACTLY 4 distinct option strings
  * "rationale": Clear pedagogical explanation of why the answer is correct
  * "blooms_level": Cognitive level ("Remember", "Understand", "Apply", "Analyze", "Evaluate", or "Create")""",
        'true_false': """- TRUE / FALSE:
  * "qtype": "true_false"
  * "question": A definitive factual statement to evaluate (string)
  * "answer": EXACTLY "True" or "False"
  * "choices": ["True", "False"]
  * "rationale": Factual explanation referencing the source text
  * "blooms_level": Cognitive level ("Remember", "Understand", "Apply", "Analyze", "Evaluate", or "Create")""",
        'short_answer': """- SHORT ANSWER (Open Response):
  * "qtype": "short_answer"
  * "question": An open-ended question testing understanding (string)
  * "answer": A concise, exemplary model answer (1-2 sentences)
  * "choices": [] (empty array)
  * "rationale": Rubric or key concepts needed for full credit
  * "blooms_level": Cognitive level ("Remember", "Understand", "Apply", "Analyze", "Evaluate", or "Create")"""
    }

    # Generate format requirements block
    if len(selected_types) == 1:
        single_type = selected_types[0]
        type_reqs = format_rules.get(single_type, format_rules['mcq'])
        qtype_header = f"{single_type.upper()} format"
        mix_instruction = f"All {num_questions} questions must be {single_type.upper()}."
    else:
        types_joined = ", ".join([t.upper() for t in selected_types])
        type_reqs = "\n".join([format_rules[t] for t in selected_types if t in format_rules])
        qtype_header = f"MIXED FORMATS ({types_joined})"
        mix_instruction = f"Distribute the {num_questions} questions evenly across the selected formats: {types_joined}. You MUST include the correct 'qtype' property ('{'', ''.join(selected_types)}') on every single question object."

    sample_items = []
    if 'mcq' in selected_types:
        sample_items.append({
            "qtype": "mcq",
            "question": "What is the primary function of mitochondria?",
            "choices": ["ATP energy production", "Protein synthesis", "Lipid digestion", "Cell division"],
            "answer": "A",
            "rationale": "Mitochondria generate most of the chemical energy needed by the cell.",
            "blooms_level": "Remember",
            "difficulty": selected_diffs[0]
        })
    if 'true_false' in selected_types:
        sample_items.append({
            "qtype": "true_false",
            "question": "Mitochondria possess their own independent circular DNA.",
            "choices": ["True", "False"],
            "answer": "True",
            "rationale": "Mitochondria contain mitochondrial DNA (mtDNA) inherited maternally.",
            "blooms_level": "Understand",
            "difficulty": selected_diffs[min(1, len(selected_diffs) - 1)]
        })
    if 'short_answer' in selected_types:
        sample_items.append({
            "qtype": "short_answer",
            "question": "Explain why mitochondria are referred to as the powerhouse of the cell.",
            "choices": [],
            "answer": "They generate adenosine triphosphate (ATP) through cellular respiration to fuel cellular activities.",
            "rationale": "Students should identify ATP synthesis and aerobic respiration.",
            "blooms_level": "Analyze",
            "difficulty": selected_diffs[-1]
        })

    example_json = json.dumps(sample_items, indent=2)

    # Intelligently sample multi-page document context
    sampled_text = sample_document_context(text, max_chars=3500, chunk_index=chunk_index, total_chunks=total_chunks)
    sampled_refined = sample_document_context(refined_text, max_chars=3500, chunk_index=chunk_index, total_chunks=total_chunks) if refined_text else ""

    return f"""{context}You are an expert pedagogical exam architect and assessment designer.
OPERATIONAL DIRECTIVE: {mode_header}
{mode_instruction}

COGNITIVE DIVERSITY ANGLE:
{focus_angle}

Generate EXACTLY {num_questions} high-quality questions at [{', '.join(selected_diffs).upper()}] difficulty for {class_id or 'Secondary/High School'} in {subject or 'General Studies'}.

1. CONTEXT CONTENT:
- ORIGINAL TEXT:
{sampled_text}
- REFINED OCR/EXTRACTION TEXT:
{sampled_refined if sampled_refined else 'N/A'}
- IMAGE/DIAGRAM DESCRIPTION:
{description if description else 'N/A'}

2. DIFFICULTY SPECIFICATION:
{diff_text}

3. QUESTION FORMAT REQUIREMENTS ({qtype_header}):
{mix_instruction}

Each question object in your JSON output must follow these schemas:
{type_reqs}
{blooms_spec_instruction}
4. STRICT OUTPUT RULES:
- Respond ONLY with a valid JSON array of question objects
- Do NOT output markdown ticks or conversational text
- Generate EXACTLY {num_questions} questions
- Ensure all questions are derived strictly from the provided text context
- Set "qtype", "difficulty", and "blooms_level" on each question object

EXAMPLE VALID JSON ARRAY:
{example_json}
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
    blooms_level: str = "all",
    mode: str = "exam"
) -> str:
    """
    Generate questions from the given text using Groq's model with multi-selection support,
    intelligent multi-chunk document sampling, and exam vs practice mode separation.
    """
    if not text.strip() and not refined_text.strip():
        return json.dumps([{"error": "No text content provided"}])
    
    if not settings.GROQ_API_KEY:
        return json.dumps([{"error": "GROQ_API_KEY not found in environment variables"}])
    
    # If no refined text is provided, use the original text
    if not refined_text.strip():
        refined_text = text

    # Parse multi-select collections
    if isinstance(qtype, list):
        selected_types = [t.strip().lower() for t in qtype if t.strip()]
    else:
        selected_types = [t.strip().lower() for t in str(qtype).split(",") if t.strip()]
    if not selected_types:
        selected_types = ["mcq"]

    if isinstance(difficulty, list):
        selected_diffs = [d.strip().lower() for d in difficulty if d.strip()]
    else:
        selected_diffs = [d.strip().lower() for d in str(difficulty).split(",") if d.strip()]
    if not selected_diffs:
        selected_diffs = ["medium"]

    if isinstance(blooms_level, list):
        selected_blooms = [b.strip().capitalize() for b in blooms_level if b.strip()]
    else:
        selected_blooms = [b.strip().capitalize() for b in str(blooms_level).split(",") if b.strip()]
    if not selected_blooms:
        selected_blooms = ["All"]

    BATCH_SIZE = 10
    total_needed = max(1, num_questions)
    total_batches = max(1, (total_needed + BATCH_SIZE - 1) // BATCH_SIZE)
    all_processed = []

    # Temperature 0.6 balances factual grounding with question/distractor diversity
    effective_temp = 0.6 if mode == "exam" else 0.5

    remaining = total_needed
    while remaining > 0:
        chunk_count = min(BATCH_SIZE, remaining)
        batch_idx = len(all_processed) // BATCH_SIZE
        prompt = build_prompt(
            text=text,
            refined_text=refined_text,
            description=description,
            qtype=qtype,
            difficulty=difficulty,
            num_questions=chunk_count,
            class_id=class_id,
            subject=subject,
            blooms_level=blooms_level,
            mode=mode,
            chunk_index=batch_idx,
            total_chunks=total_batches,
            variation_seed=random.randint(1, 1000000)
        )
        
        batch_success = False
        for attempt in range(max_retries + 1):
            try:
                completion = groq_client.chat.completions.create(
                    model=MODEL_NAME,
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a helpful educational assessment generator that outputs strictly valid JSON arrays of question objects."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    temperature=effective_temp,
                    max_tokens=2048,
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
                    
                valid_blooms = ["Remember", "Understand", "Apply", "Analyze", "Evaluate", "Create"]
                valid_types = ["mcq", "true_false", "short_answer"]
                valid_diffs = ["easy", "medium", "hard"]

                for q in questions:
                    if not isinstance(q, dict):
                        continue
                    
                    # 1. Resolve Question Type
                    raw_type = str(q.get("qtype") or q.get("type", "")).strip().lower()
                    if raw_type in valid_types:
                        item_qtype = raw_type
                    elif "choices" in q and isinstance(q["choices"], list) and len(q["choices"]) >= 3:
                        item_qtype = "mcq"
                    elif str(q.get("answer", "")).strip().lower() in ["true", "false"]:
                        item_qtype = "true_false"
                    elif "short_answer" in selected_types:
                        item_qtype = "short_answer"
                    else:
                        item_qtype = selected_types[len(all_processed) % len(selected_types)]

                    # 2. Resolve Difficulty
                    raw_diff = str(q.get("difficulty", "")).strip().lower()
                    if raw_diff in valid_diffs:
                        item_diff = raw_diff
                    else:
                        item_diff = selected_diffs[len(all_processed) % len(selected_diffs)]

                    # 3. Resolve Bloom's Level
                    raw_bloom = str(q.get("blooms_level", "")).strip().capitalize()
                    if raw_bloom in valid_blooms:
                        item_bloom = raw_bloom
                    elif not any(b.lower() == 'all' for b in selected_blooms) and selected_blooms:
                        valid_selected = [b for b in selected_blooms if b in valid_blooms]
                        item_bloom = valid_selected[len(all_processed) % len(valid_selected)] if valid_selected else "Understand"
                    else:
                        if item_diff == "easy":
                            item_bloom = "Remember"
                        elif item_diff == "hard":
                            item_bloom = "Analyze"
                        else:
                            item_bloom = "Understand"

                    processed_q = {
                        "question": q.get("question", "").strip() or "No question provided",
                        "answer": "",
                        "rationale": q.get("rationale", "No rationale provided.").strip(),
                        "qtype": item_qtype,
                        "difficulty": item_diff,
                        "blooms_level": item_bloom,
                        "choices": []
                    }
                    
                    if "answer" in q:
                        processed_q["answer"] = str(q["answer"]).strip()
                    elif "correct" in q:
                        processed_q["answer"] = str(q["correct"]).strip()

                    # Handle type-specific fields
                    if item_qtype == "mcq":
                        if "choices" in q and isinstance(q["choices"], list):
                            processed_q["choices"] = [str(c).strip() for c in q["choices"][:4]]
                        elif "options" in q and isinstance(q["options"], list):
                            processed_q["choices"] = [str(o).strip() for o in q["options"][:4]]
                        else:
                            processed_q["choices"] = ["Option A", "Option B", "Option C", "Option D"]
                            
                        while len(processed_q["choices"]) < 4:
                            processed_q["choices"].append(f"Option {chr(65 + len(processed_q['choices']))}")
                            
                        if processed_q["answer"] in ["A", "B", "C", "D"]:
                            idx = ord(processed_q["answer"].upper()) - ord('A')
                            if 0 <= idx < len(processed_q["choices"]):
                                processed_q["answer"] = processed_q["choices"][idx]
                    elif item_qtype == "true_false":
                        processed_q["choices"] = ["True", "False"]
                        ans_lower = processed_q["answer"].lower()
                        if ans_lower in ["true", "t"]:
                            processed_q["answer"] = "True"
                        elif ans_lower in ["false", "f"]:
                            processed_q["answer"] = "False"
                        else:
                            processed_q["answer"] = "True"
                    else:  # short_answer
                        processed_q["choices"] = []
                    
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
