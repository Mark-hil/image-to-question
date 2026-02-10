"""
Simple OCR Service with optimizations but using Tesseract.
This provides better performance than the original implementation.
"""
import os
import re
from PIL import Image, ImageEnhance, ImageFilter
import pytesseract
from dotenv import load_dotenv
from typing import List, Tuple, Optional, Dict, Any, Union
import json
import sys
import asyncio
import io
import string

# Add the project root to path to allow absolute imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Now use absolute imports
from services import qgen_service
from services.vision_service import describe_image_stub

# =====================================================
#  TEXT CLEANING FUNCTION
# =====================================================
def clean_extracted_text(text: str) -> str:
    """
    Clean and format extracted OCR text for better readability.
    More conservative approach to preserve actual content.
    """
    if not text or not text.strip():
        return ""
    
    # Remove common OCR errors and artifacts (more conservative)
    cleaned = text.strip()
    
    # Fix only the most common OCR character substitutions
    # Be very careful not to replace valid characters
    replacements = {
        # Only fix obvious OCR errors, not all occurrences
        'l0': 'lo',  # l0 -> lo
        'l1': 'li',  # l1 -> li
        'l2': 'lz',  # l2 -> lz
        'cl': 'd',   # Only when cl is clearly wrong context
        'rn': 'm',   # Only when rn is clearly wrong context
        'vv': 'w',   # Only when vv is clearly wrong context
    }
    
    # Apply character replacements more carefully
    for old, new in replacements.items():
        cleaned = cleaned.replace(old, new)
    
    # Normalize whitespace (conservative)
    cleaned = re.sub(r'\s+', ' ', cleaned)  # Multiple spaces to single space
    cleaned = re.sub(r'\n\s*\n', '\n\n', cleaned)  # Multiple newlines to double newline
    
    # Fix obvious word breaks only
    cleaned = re.sub(r'(\w+)\s*-\s*(\w+)', r'\1-\2', cleaned)  # word-word to word-word
    
    # Remove leading/trailing whitespace
    cleaned = cleaned.strip()
    
    return cleaned

# =====================================================
#  LOAD TESSERACT
# =====================================================
load_dotenv()
TESS_CMD = os.getenv("TESSERACT_CMD")
if TESS_CMD:
    pytesseract.pytesseract.tesseract_cmd = TESS_CMD

import logging
logger = logging.getLogger(__name__)

class SimpleOCRService:
    """Optimized OCR service using Tesseract with better performance."""
    
    def __init__(self):
        """Initialize the simple OCR service."""
        logger.info("Initializing Simple OCR Service (Tesseract)")
    
    async def extract_text_from_image(self, image_path: str) -> Dict[str, str]:
        """
        Extract text from image using optimized Tesseract processing.
        """
        try:
            # Open and preprocess image
            with Image.open(image_path) as img:
                # Convert to grayscale
                if img.mode != 'L':
                    img = img.convert('L')
                
                # Resize for faster processing (Tesseract works well with moderate sizes)
                width, height = img.size
                if max(width, height) > 2000:
                    scale = 2000 / max(width, height)
                    new_width = int(width * scale)
                    new_height = int(height * scale)
                    img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                
                # Apply minimal preprocessing for speed
                # Just use basic contrast enhancement
                try:
                    img = ImageEnhance.Contrast(img, 1.5).enhance(img)
                except:
                    # If enhancement fails, use original image
                    img = img
                
                # Run OCR in thread pool for non-blocking
                loop = asyncio.get_event_loop()
                text = await loop.run_in_executor(
                    None,
                    lambda: pytesseract.image_to_string(img, config='--psm 6 --oem 1', nice=0)
                )
            
            # Clean the extracted text
            cleaned_text = clean_extracted_text(text.strip() if text else "")
            
            return {
                "text": cleaned_text,
                "description": f"Extracted text from {os.path.basename(image_path)} using optimized Tesseract",
                "confidence": "high" if cleaned_text and len(cleaned_text.strip()) > 10 else "medium",
                "full_text": cleaned_text  # Add full text for debugging
            }
            
        except Exception as e:
            logger.error(f"Error extracting text from {image_path}: {str(e)}")
            return {
                "text": "",
                "description": f"Error processing {os.path.basename(image_path)}: {str(e)}",
                "confidence": "error"
            }
    
    async def extract_text_from_pdf(self, pdf_path: str) -> Dict[str, str]:
        """
        Extract text from PDF using optimized processing.
        """
        try:
            # Import PyMuPDF here to avoid circular imports
            import fitz
            
            # Open PDF
            doc = fitz.open(pdf_path)
            
            # Extract text directly from PDF (much faster than OCR for PDFs with text)
            direct_text = ""
            for page_num in range(len(doc)):
                page = doc[page_num]
                page_text = page.get_text()
                if page_text.strip():
                    direct_text += page_text + "\\n"
            
            if direct_text.strip():
                cleaned_text = clean_extracted_text(direct_text.strip())
                return {
                    "text": cleaned_text,
                    "description": f"Extracted direct text from {os.path.basename(pdf_path)}",
                    "confidence": "high",
                    "full_text": cleaned_text  # Add full text for debugging
                }
            
            # If no direct text, extract images and OCR them
            return await self._ocr_pdf_images(doc, pdf_path)
        
        except Exception as e:
            logger.error(f"Error extracting text from {pdf_path}: {str(e)}")
            return {
                "text": "",
                "description": f"Error processing PDF {os.path.basename(pdf_path)}: {str(e)}",
                "confidence": "error"
            }
    
    async def _ocr_pdf_images(self, doc, pdf_path: str) -> Dict[str, str]:
        """Extract images from PDF and OCR them in parallel."""
        image_tasks = []
        
        for page_num in range(min(len(doc), 10)):  # Limit to first 10 pages for speed
            page = doc[page_num]
            images = page.get_images()
            
            for img_index, img in enumerate(images):
                xref = img[0]
                pix = fitz.Pixmap(doc, xref)
                
                if pix.n - pix.alpha < 4:  # GRAY or RGB
                    img_data = pix.tobytes("png")
                    pil_image = Image.open(io.BytesIO(img_data))
                    
                    # Save temp image and OCR
                    temp_path = f"/tmp/pdf_page_{page_num}_{img_index}.png"
                    pil_image.save(temp_path)
                    
                    # Create OCR task
                    task = self.extract_text_from_image(temp_path)
                    image_tasks.append(task)
        
        # Run all OCR tasks in parallel
        if image_tasks:
            results = await asyncio.gather(*image_tasks, return_exceptions=True)
            
            # Combine results with text cleaning
            all_text = []
            for result in results:
                if isinstance(result, dict) and result.get("text"):
                    cleaned_text = clean_extracted_text(result["text"])
                    all_text.append(cleaned_text)
            
            combined_text = "\\n".join(all_text)
            
            # Cleanup temp files
            for page_num in range(min(len(doc), 10)):
                for img_index in range(len(doc[page_num].get_images())):
                    temp_path = f"/tmp/pdf_page_{page_num}_{img_index}.png"
                    if os.path.exists(temp_path):
                        os.remove(temp_path)
            
            return {
                "text": combined_text,
                "description": f"OCR'd images from {os.path.basename(pdf_path)}",
                "confidence": "medium" if combined_text else "low",
                "full_text": combined_text  # Add full text for debugging
            }
        else:
            return {
                "text": "",
                "description": f"No images found in {os.path.basename(pdf_path)}",
                "confidence": "low"
            }

# Global simple OCR service instance
_simple_ocr_service = SimpleOCRService()

async def extract_text_from_path(file_path: str) -> Dict[str, str]:
    """
    Simple text extraction using optimized Tesseract service.
    """
    file_ext = os.path.splitext(file_path)[1].lower()
    
    if file_ext == '.pdf':
        return await _simple_ocr_service.extract_text_from_pdf(file_path)
    else:
        return await _simple_ocr_service.extract_text_from_image(file_path)

async def extract_text(file_path: str) -> Dict[str, str]:
    """
    Alias for extract_text_from_path for compatibility.
    """
    return await extract_text_from_path(file_path)
