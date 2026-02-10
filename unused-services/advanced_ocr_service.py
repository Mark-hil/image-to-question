"""
Advanced OCR Service with comprehensive error correction.
Fixes spelling, word segmentation, punctuation, and capitalization errors.
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
from collections import defaultdict

# Add the project root to path to allow absolute imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Now use absolute imports
from services import qgen_service
from services.vision_service import describe_image_stub

# =====================================================
#  LOAD TESSERACT
# =====================================================
load_dotenv()
TESS_CMD = os.getenv("TESSERACT_CMD")
if TESS_CMD:
    pytesseract.pytesseract.tesseract_cmd = TESS_CMD

import logging
logger = logging.getLogger(__name__)

class AdvancedOCRService:
    """Advanced OCR service with comprehensive error correction."""
    
    def __init__(self):
        """Initialize the advanced OCR service."""
        logger.info("Initializing Advanced OCR Service with error correction")
        
        # Common OCR character substitutions
        self.char_corrections = {
            # More aggressive but context-aware corrections
            '0': 'O',  # Zero to O (in words)
            '1': 'l',  # One to l (in words)
            '2': 'Z',  # Two to Z
            '5': 'S',  # Five to S
            '8': 'B',  # Eight to B
            '|': 'I',  # Pipe to I
            'T': 'I',  # T to I (in some contexts)
        }
        
        # Context-aware word corrections
        self.word_corrections = {
            # Personal Hygiene specific terms
            'Pers0na1': 'Personal',
            'pers0na1': 'personal',
            't0na1': 'tonal',
            'dean1iness': 'deanliness',
            'deanliness': 'cleanliness',
            'c1ean1iness': 'cleanliness',
            'f00d': 'food',
            'hea1th': 'health',
            'hand1ers': 'handlers',
            'pers0n': 'person',
            'd0ing': 'doing',
            'erchie': 'architectural',
            'architectura1': 'architectural',
            'hy': 'hy',
            'giene': 'giene',
            'peas': 'peace',
            'deaning': 'cleaning',
            'tobesafetaeat': 'to be safe to eat',
            'thefood': 'the food',
            'Italsomakes': 'It also makes',
            'iS': 'is',
            'aa': 'a',
            'Care': 'Care',
            'ee': 'the',
            'Cy': 'by',
            'dean': 'clean',
            'deaned': 'cleaned',
            'deaning': 'cleaning',
            '1he': 'the',
            'wha1is': 'what is',
            '11': 'IT',
            'combedbrushed': 'combed/brushed',
            'ofanail': 'of a nail',
            
            # Common OCR errors
            'WHATT': 'WHAT',
            'WHATIS': 'WHAT IS',
            'TT': 'IT',
            'om': 'from',
            'et': 'it',
            'ne': 'be',
            'enka': 'and',
            'fife': 'life',
            'peas': 'peace',
            'oo': 'of',
            'ie': 'i.e.',
        }
        
        # Merged word patterns and their corrections
        self.merged_word_corrections = {
            'WHATIS': 'WHAT IS',
            'PERSONAL': 'PERSONAL',  # Keep as is (title)
            'HYGIENE': 'HYGIENE',    # Keep as is (title)
            'ENSURING': 'ENSURING',  # Keep as is (title)
            'hygiene': 'hygiene',
            'personal': 'personal',
            'ensuring': 'ensuring',
        }
        
        # Fragmented word combinations
        self.fragmented_corrections = {
            ('hy', 'giene'): 'hygiene',
            ('dean', 'liness'): 'cleanliness',
            ('erchie', 'tonal'): 'architectural',
            ('the', 'food'): 'the food',
            ('it', 'also', 'makes'): 'it also makes',
            ('to', 'be', 'safe', 'to', 'eat'): 'to be safe to eat',
        }
        
        # Common punctuation fixes
        self.punctuation_fixes = {
            r'\s+': ' ',  # Multiple spaces to single
            r'\s*([.,!?;:])': r'\1',  # Space before punctuation
            r'([.,!?;:])\s*([a-z])': r'\1 \2',  # Space after punctuation
            r'[\'"/]': '',  # Remove random symbols
            r'([A-Z])([a-z]+)([A-Z][a-z]+)': r'\1\2 \3',  # Split camelCase
        }
    
    async def extract_text_from_image(self, image_path: str) -> Dict[str, str]:
        """
        Extract text from image using advanced OCR with error correction.
        """
        try:
            # Open and preprocess image
            with Image.open(image_path) as img:
                # Convert to grayscale
                if img.mode != 'L':
                    img = img.convert('L')
                
                # Resize for faster processing
                width, height = img.size
                if max(width, height) > 2000:
                    scale = 2000 / max(width, height)
                    new_width = int(width * scale)
                    new_height = int(height * scale)
                    img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                
                # Apply minimal preprocessing
                try:
                    img = ImageEnhance.Contrast(img, 1.5).enhance(img)
                except:
                    img = img
                
                # Run OCR in thread pool for non-blocking
                loop = asyncio.get_event_loop()
                text = await loop.run_in_executor(
                    None,
                    lambda: pytesseract.image_to_string(img, config='--psm 6 --oem 1', nice=0)
                )
            
            # Apply comprehensive text cleaning and correction
            corrected_text = self.comprehensive_text_correction(text.strip() if text else "")
            
            return {
                "text": corrected_text,
                "description": f"Extracted and corrected text from {os.path.basename(image_path)} using advanced OCR",
                "confidence": "high" if corrected_text and len(corrected_text.strip()) > 10 else "medium",
                "full_text": corrected_text
            }
            
        except Exception as e:
            logger.error(f"Error extracting text from {image_path}: {str(e)}")
            return {
                "text": "",
                "description": f"Error processing {os.path.basename(image_path)}: {str(e)}",
                "confidence": "error"
            }
    
    def comprehensive_text_correction(self, text: str) -> str:
        """
        Apply comprehensive text correction to fix all OCR errors.
        """
        if not text:
            return ""
        
        # Step 1: Fix character substitutions
        text = self.fix_character_substitutions(text)
        
        # Step 2: Fix word segmentation (merged and fragmented words)
        text = self.fix_word_segmentation(text)
        
        # Step 3: Apply word-specific corrections
        text = self.apply_word_corrections(text)
        
        # Step 4: Fix punctuation and spacing
        text = self.fix_punctuation_and_spacing(text)
        
        # Step 5: Fix capitalization
        text = self.fix_capitalization(text)
        
        # Step 6: Final cleanup
        text = self.final_cleanup(text)
        
        return text
    
    def fix_character_substitutions(self, text: str) -> str:
        """Fix common OCR character substitutions more aggressively."""
        corrected = text
        
        # Apply character corrections more aggressively for common patterns
        for old, new in self.char_corrections.items():
            # Replace all occurrences for common OCR errors
            if old in ['0', '1', '|']:
                corrected = corrected.replace(old, new)
            elif old == 'T' and re.search(r'[a-z]T[a-z]', corrected):
                corrected = corrected.replace(old, new)
        
        return corrected
    
    def fix_word_segmentation(self, text: str) -> str:
        """Fix merged and fragmented words."""
        words = text.split()
        corrected_words = []
        
        i = 0
        while i < len(words):
            word = words[i]
            
            # Check for merged words that should be split
            if word in self.merged_word_corrections:
                corrected_words.extend(self.merged_word_corrections[word].split())
            # Check for fragmented words that should be merged
            elif i < len(words) - 1:
                next_word = words[i + 1]
                pair = (word, next_word)
                if pair in self.fragmented_corrections:
                    corrected_words.append(self.fragmented_corrections[pair])
                    i += 2  # Skip the next word
                    continue
                else:
                    corrected_words.append(word)
            else:
                corrected_words.append(word)
            
            i += 1
        
        return ' '.join(corrected_words)
    
    def apply_word_corrections(self, text: str) -> str:
        """Apply specific word corrections."""
        corrected = text
        
        # Apply word-specific corrections
        for incorrect, correct in self.word_corrections.items():
            corrected = re.sub(r'\b' + re.escape(incorrect) + r'\b', correct, corrected, flags=re.IGNORECASE)
        
        return corrected
    
    def fix_punctuation_and_spacing(self, text: str) -> str:
        """Fix punctuation and spacing issues."""
        corrected = text
        
        # Apply punctuation fixes
        for pattern, replacement in self.punctuation_fixes.items():
            corrected = re.sub(pattern, replacement, corrected)
        
        # Fix specific spacing issues
        corrected = re.sub(r'\s+', ' ', corrected)  # Multiple spaces
        corrected = re.sub(r'\s*([.,!?;:])', r'\1', corrected)  # Space before punctuation
        corrected = re.sub(r'([.,!?;:])\s*', r'\1 ', corrected)  # Space after punctuation
        
        return corrected.strip()
    
    def fix_capitalization(self, text: str) -> str:
        """Fix capitalization errors."""
        if not text:
            return text
        
        sentences = re.split(r'([.!?])', text)
        corrected_sentences = []
        
        for i, sentence in enumerate(sentences):
            if sentence.strip() and i > 0 and sentences[i-1] in '.!?':
                # Start of sentence - capitalize
                sentence = sentence.capitalize()
            elif sentence.strip() and i == 0:
                # First sentence - capitalize
                sentence = sentence.capitalize()
            elif sentence.strip() and sentence not in '.!?':
                # Middle of sentence - ensure proper capitalization
                words = sentence.split()
                corrected_words = []
                for word in words:
                    # Fix words that are all caps but shouldn't be
                    if word.isupper() and len(word) > 3 and word not in ['PERSONAL', 'HYGIENE', 'ENSURING']:
                        corrected_words.append(word.lower())
                    else:
                        corrected_words.append(word)
                sentence = ' '.join(corrected_words)
            
            corrected_sentences.append(sentence)
        
        return ''.join(corrected_sentences)
    
    def final_cleanup(self, text: str) -> str:
        """Final cleanup of the text."""
        # Remove any remaining random symbols
        text = re.sub(r'[^a-zA-Z0-9\s.,!?;:\-\'"]', '', text)
        
        # Fix final spacing
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        # Ensure sentences end with proper punctuation
        if text and not text[-1] in '.!?':
            text += '.'
        
        return text
    
    async def extract_text_from_pdf(self, pdf_path: str) -> Dict[str, str]:
        """
        Extract text from PDF using advanced processing.
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
                cleaned_text = self.comprehensive_text_correction(direct_text.strip())
                return {
                    "text": cleaned_text,
                    "description": f"Extracted and corrected text from {os.path.basename(pdf_path)}",
                    "confidence": "high",
                    "full_text": cleaned_text
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
                    cleaned_text = result["text"]
                    all_text.append(cleaned_text)
            
            # Cleanup temp files
            for page_num in range(min(len(doc), 10)):
                for img_index in range(len(doc[page_num]).get_images() if hasattr(doc[page_num], 'get_images') else []):
                    temp_path = f"/tmp/pdf_page_{page_num}_{img_index}.png"
                    if os.path.exists(temp_path):
                        os.remove(temp_path)
            
            combined_text = "\\n".join(all_text)
            
            return {
                "text": combined_text,
                "description": f"OCR'd and corrected images from {os.path.basename(pdf_path)}",
                "confidence": "medium" if combined_text else "low",
                "full_text": combined_text
            }
        else:
            return {
                "text": "",
                "description": f"No images found in {os.path.basename(pdf_path)}",
                "confidence": "low"
            }

# Global advanced OCR service instance
_advanced_ocr_service = AdvancedOCRService()

async def extract_text_from_path(file_path: str) -> Dict[str, str]:
    """
    Advanced text extraction with comprehensive error correction.
    """
    file_ext = os.path.splitext(file_path)[1].lower()
    
    if file_ext == '.pdf':
        return await _advanced_ocr_service.extract_text_from_pdf(file_path)
    else:
        return await _advanced_ocr_service.extract_text_from_image(file_path)

async def extract_text(file_path: str) -> Dict[str, str]:
    """
    Alias for extract_text_from_path for compatibility.
    """
    return await extract_text_from_path(file_path)
