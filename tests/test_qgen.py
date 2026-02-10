#!/usr/bin/env python3
# test_qgen.py - Test script for question generation service

import os
import sys
import json
import argparse
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Add project root to path to allow absolute imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.qgen_service import generate_questions_from_content

# Load environment variables
load_dotenv()

def test_question_generation(
    text: str,
    refined_text: str = "",
    description: str = "",
    qtype: str = "true_false",
    difficulty: str = "medium",
    num_questions: int = 5
) -> Dict[str, Any]:
    """
    Test the question generation with the given parameters.
    
    Args:
        text: Original text content
        refined_text: Refined/cleaned text (if available)
        description: Description of the content (if any)
        qtype: Type of questions ('mcq', 'true_false', 'short_answer')
        difficulty: Difficulty level ('easy', 'medium', 'hard')
        num_questions: Number of questions to generate
        
    Returns:
        Dictionary containing the test results
    """
    print(f"\n{'='*50}")
    print(f"Testing question generation with {num_questions} {qtype} questions ({difficulty} difficulty)")
    print(f"{'='*50}")
    
    if refined_text:
        print("\n=== Using REFINED TEXT ===")
        print(refined_text[:500] + ("..." if len(refined_text) > 500 else ""))
    else:
        print("\n=== Using ORIGINAL TEXT ===")
        print(text[:500] + ("..." if len(text) > 500 else ""))
    
    if description:
        print("\n=== IMAGE DESCRIPTION ===")
        print(description)
    
    print("\n=== GENERATING QUESTIONS ===")
    
    # Generate questions
    result = generate_questions_from_content(
        text=text,
        refined_text=refined_text,
        description=description,
        qtype=qtype,
        difficulty=difficulty,
        num_questions=num_questions
    )
    
    # Prepare response
    response = {
        'success': False,
        'error': None,
        'questions': None,
        'raw_output': result
    }
    
    # Try to parse the JSON response
    try:
        questions = json.loads(result)
        response.update({
            'success': True,
            'questions': questions
        })
        
        print("\n=== GENERATION SUCCESSFUL ===")
        print(f"Generated {len(questions) if isinstance(questions, list) else 1} question(s)")
        print("\n=== FORMATTED QUESTIONS ===")
        print(json.dumps(questions, indent=2, ensure_ascii=False))
        
    except json.JSONDecodeError as e:
        response['error'] = f"Failed to parse JSON response: {str(e)}"
        print("\n=== GENERATION FAILED ===")
        print(f"Error: {response['error']}")
        print("\n=== RAW OUTPUT ===")
        print(result)
    
    return response

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Test question generation service')
    parser.add_argument('--num', type=int, default=3, help='Number of questions to generate (default: 3)')
    parser.add_argument('--qtype', default='mcq', choices=['mcq', 'true_false', 'short_answer'], 
                       help='Type of questions to generate (default: mcq)')
    parser.add_argument('--difficulty', default='medium', choices=['easy', 'medium', 'hard'],
                       help='Difficulty level (default: medium)')
    args = parser.parse_args()
    
    # Sample data
    sample_text = """
    Photosynthesis is the process by which green plants, algae, and some bacteria convert light energy into chemical energy. 
    This process occurs in the chloroplasts of plant cells, where chlorophyll captures sunlight. 
    The overall reaction can be summarized as: 6CO2 + 6H2O + light energy → C6H12O6 + 6O2.
    """
    
    # This would typically come from your OCR processing
    refined_text = """
    [REFINED TEXT]
    Photosynthesis is the process by which green plants, algae, and some bacteria convert light energy into chemical energy.
    This process occurs in the chloroplasts of plant cells, where chlorophyll captures sunlight.
    The overall reaction can be summarized as: 6CO2 + 6H2O + light energy → C6H12O6 + 6O2.
    [END REFINED TEXT]
    """
    
    sample_description = "A diagram showing a green leaf with chloroplasts and the photosynthesis process."
    
    # Run the test
    test_question_generation(
        text=sample_text,
        refined_text=refined_text,
        description=sample_description,
        qtype=args.qtype,
        difficulty=args.difficulty,
        num_questions=args.num
    )

if __name__ == "__main__":
    main()