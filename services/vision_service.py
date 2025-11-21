# services/vision_service.py
import os
import base64
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv
from groq import Groq

from services.diagram_utils import contains_diagram, extract_diagram_text
from typing import Optional

# Load environment variables
load_dotenv()

# Configuration
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
MODEL_NAME = "llama-3.1-8b-instant"  # Using a supported Groq model

# Validate API key
if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY not found in environment variables")

# Initialize Groq client
client = Groq(api_key=GROQ_API_KEY)

async def refine_ocr_text(text: str) -> str:
    """
    Refines the OCR-extracted text using the Groq model to correct errors
    and improve readability while preserving the original content.
    Uses context-aware correction without hardcoded replacements.
    """
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {
                    "role": "system", 
                    "content": "You are a text cleaning assistant that fixes OCR errors. "
                             "Your task is to correct common OCR mistakes while preserving the original meaning and structure.\n"
                             "GUIDELINES:\n"
                             "1. Fix only obvious OCR errors (e.g., 'nat' → 'not', 'tne' → 'the', 'w1th' → 'with')\n"
                             "2. Preserve proper nouns, names, and specialized terminology\n"
                             "3. Maintain original punctuation and formatting\n"
                             "4. Do NOT add any new information or change the meaning\n"
                             "5. Return ONLY the corrected text, with no additional commentary"
                },
                {
                    "role": "user",
                    "content": f"Please correct any OCR errors in the following text while preserving its original meaning and structure. Return ONLY the corrected text with no additional commentary.\n\nTEXT TO CORRECT:\n{text}"
                }
            ],
            temperature=0.1,  # Low temperature for consistent, minimal changes
            top_p=0.9,       # Slightly higher top_p for better handling of OCR errors
            max_tokens=2000,
        )
        
        if response.choices and len(response.choices) > 0:
            # Extract the cleaned text
            cleaned_text = response.choices[0].message.content.strip()
            
            # Basic post-processing to ensure clean output
            cleaned_text = (
                cleaned_text
                .replace('```', '')  # Remove markdown code blocks
                .replace('TEXT TO CORRECT:', '')  # Remove any prompt artifacts
                .strip()
            )
            
            # If the model somehow added commentary, try to extract just the corrected text
            lines = cleaned_text.split('\n')
            if len(lines) > 1 and ':' in lines[0]:
                # If the first line looks like a header (e.g., 'Corrected text:'), skip it
                return '\n'.join(lines[1:]).strip()
            
            return cleaned_text.strip() or text  # Fallback to original if empty
        
    except Exception as e:
        print(f"Error refining OCR text: {str(e)}")
        return text

async def describe_image_groq(image_path: str) -> str:
    """
    Extracts and refines text from an image using OCR and Groq.
    
    Args:
        image_path: Path to the image file
        
    Returns:
        str: Both original and refined text from the image
    """
    if not os.path.exists(image_path):
        return f"Error: Image file not found at {os.path.abspath(image_path)}"
    
    try:
        from services.ocr_service import extract_text_from_path
        
        print("Extracting text from image...")
        # First, extract text using OCR
        extracted_text = extract_text_from_path(image_path)
        
        if not extracted_text or extracted_text.startswith("[error]"):
            raise ValueError(f"Failed to extract text from image: {extracted_text}")
        
        # Make a copy of the original text for output
        original_text = extracted_text.strip()
        
        print("Refining extracted text...")
        # Refine the OCR text to fix common errors
        refined_text = await refine_ocr_text(extracted_text)
        
        # Return both original and refined text with clear separation
        return f"ORIGINAL TEXT:\n{'-'*40}\n{original_text}\n\n\nREFINED TEXT:\n{'-'*40}\n{refined_text.strip()}"
            
    except Exception as e:
        error_msg = f"[Error] {str(e)}"
        print(error_msg)
        raise  # Re-raise to trigger fallback
            
    except Exception as e:
        error_msg = f"[Groq Error] {str(e)}"
        print(error_msg)
        raise  # Re-raise to trigger fallback

async def describe_image_stub(path: str) -> str:
    """
    Main function to extract and process text from an image.
    Returns both original and refined text, with fallback to basic OCR if needed.
    """
    try:
        # Get both original and refined text from the image
        result = await describe_image_groq(path)
        if not result:
            raise ValueError("No text could be extracted from the image")
        return result
        
    except Exception as e:
        # On failure, try basic OCR without refinement
        try:
            from services.ocr_service import extract_text_from_path
            extracted_text = extract_text_from_path(path)
            if not extracted_text:
                raise ValueError("No text could be extracted")
                
            return f"ORIGINAL TEXT (FALLBACK):\n{'-'*40}\n{extracted_text.strip()}\n\n\nREFINED TEXT:\n{'-'*40}\n[Refinement not available - showing original text]"
                
        except Exception as oe:
            return f"[Error] Failed to process image: {str(oe)}"


async def describe_image_groq(image_path: str) -> str:
    """
    Enhanced image description that handles both text and diagrams.
    
    Args:
        image_path: Path to the image file
        
    Returns:
        str: Formatted string with extracted text and/or diagram description
    """
    if not os.path.exists(image_path):
        return f"Error: Image file not found at {os.path.abspath(image_path)}"
    
    try:
        from services.ocr_service import extract_text_from_path
        
        # Check if image contains diagrams
        if contains_diagram(image_path):
            print("Diagram detected in image, using specialized processing...")
            # Extract and refine text from diagram
            extracted_text = await extract_diagram_text(image_path)
            refined_text = await refine_ocr_text(extracted_text)
            
            # Get description of the diagram
            try:
                diagram_desc = await describe_with_groq(
                    image_path,
                    "Describe this diagram in detail, including the type of diagram, "
                    "key elements, and their relationships. Be factual and objective."
                )
            except Exception as e:
                print(f"Diagram description error: {str(e)}")
                diagram_desc = "Could not generate description for the diagram."
            
            return (
                "DIAGRAM DETECTED\n"
                "---------------\n"
                f"ORIGINAL TEXT:\n{'-'*40}\n{extracted_text}\n\n"
                f"REFINED TEXT:\n{'-'*40}\n{refined_text}\n\n"
                f"DIAGRAM DESCRIPTION:\n{'-'*40}\n{diagram_desc}\n"
                "--------------\n"
            )
        else:
            # Standard text extraction
            print("Processing as standard text image...")
            extracted_text = extract_text_from_path(image_path)
            refined_text = await refine_ocr_text(extracted_text)
            
            return (
                "TEXT EXTRACTION\n"
                "--------------\n"
                f"ORIGINAL TEXT:\n{'-'*40}\n{extracted_text}\n\n"
                
                f"REFINED TEXT:\n{'-'*40}\n{refined_text}\n\n"
            )
            
    except Exception as e:
        error_msg = f"[Error] {str(e)}"
        print(error_msg)
        raise

async def describe_with_groq(image_path: str, prompt: str) -> str:
    """Helper function to get description from Groq API."""
    try:
        # Read image as base64
        with open(image_path, "rb") as img_file:
            img_base64 = base64.b64encode(img_file.read()).decode('utf-8')
        
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": f"data:image/jpeg;base64,{img_base64}"
                        }
                    ]
                }
            ],
            max_tokens=1000,
        )
        
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Could not generate description: {str(e)}"