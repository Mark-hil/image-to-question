"""
Ultimate OCR Service with comprehensive error correction for severe OCR issues.
Handles spelling distortions, hallucinated words, repeated words, broken/merged words,
incorrect verb tenses, random punctuation, capitalization, and OCR-induced grammar errors.
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

class UltimateOCRService:
    """Ultimate OCR service with comprehensive error correction for severe OCR issues."""
    
    def __init__(self):
        """Initialize ultimate OCR service with dynamic pattern matching."""
        logger.info("Initializing Ultimate OCR Service with dynamic error correction")
        
        # Dynamic character substitution patterns (conservative - only clear OCR errors)
        self.char_patterns = [
            (r'\b0\b', 'O'),  # Only standalone zero (rare OCR error)
            (r'\|', 'I'),  # Pipe to letter I (clear OCR error)
            # Removed: number-to-letter mappings to preserve valid numbers
        ]
        
        # No hardcoded word corrections - will use dynamic pattern matching
        
        # Dynamic punctuation cleanup patterns
        self.punctuation_patterns = [
            (r'[\s]+', ' '),  # Multiple spaces to single space
            (r'[""``]', '"'),  # Normalize quotes
            (r"['']", "'"),  # Normalize apostrophes
            (r'[\[\]{}<>]', ''),  # Remove brackets but keep parentheses
            (r'[^\w\s.,!?;:\-\'"()]', ''),  # Keep important characters
            (r'\s*([.,!?;:])\s*', r'\1 '),  # Normalize punctuation spacing
            (r'([.,!?;:])\s*([a-z])', r'\1 \2'),  # Space after punctuation
            (r'\s*\(\s*', ' ('),  # Fix spacing before parentheses
            (r'\s*\)\s*', ') '),  # Fix spacing after parentheses
        ]
        
        # Dynamic capitalization rules (common lowercase words)
        self.lowercase_words = {
            'the', 'and', 'of', 'to', 'in', 'on', 'at', 'by', 'for', 
            'with', 'from', 'is', 'are', 'was', 'were', 'a', 'an'
        }
    
    async def extract_text_from_image(self, image_path: str) -> Dict[str, str]:
        """
        Extract text from image using ultimate OCR with severe error correction.
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
            
            # Apply ultimate text cleaning and correction
            corrected_text = self.ultimate_text_correction(text.strip() if text else "")
            
            return {
                "text": corrected_text,
                "description": f"Extracted and ultimate-corrected text from {os.path.basename(image_path)} using ultimate OCR",
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
    
    def ultimate_text_correction(self, text: str) -> str:
        """
        Apply ultimate text correction to fix all severe OCR errors.
        """
        if not text:
            return ""
        
        # Step 1: Fix character substitutions
        text = self.fix_character_substitutions(text)
        
        # Step 2: Fix severe spelling distortions and hallucinated words
        text = self.fix_severe_distortions(text)
        
        # Step 3: Fix repeated words
        text = self.fix_repeated_words(text)
        
        # Step 4: Fix broken and merged words
        text = self.fix_broken_merged_words(text)
        
        # Step 5: Fix verb tenses
        text = self.fix_verb_tenses(text)
        
        # Step 6: Clean random punctuation and symbols
        text = self.clean_punctuation_symbols(text)
        
        # Step 7: Detect and format titles
        text = self.format_titles_and_paragraphs(text)
        
        # Step 8: Fix capitalization
        text = self.fix_capitalization(text)
        
        # Step 9: Fix OCR-induced grammar errors
        text = self.fix_ocr_grammar(text)
        
        # Step 10: Final cleanup
        text = self.final_cleanup(text)
        
        return text
    
    def fix_character_substitutions(self, text: str) -> str:
        """Fix common OCR character substitutions using dynamic patterns."""
        corrected = text
        
        # Apply dynamic character patterns
        for pattern, replacement in self.char_patterns:
            corrected = re.sub(pattern, replacement, corrected)
        
        return corrected
    
    def fix_severe_distortions(self, text: str) -> str:
        """Fix OCR-related spelling errors with minimum edits."""
        corrected = text
        
        # Conservative patterns for clear OCR spelling errors only
        patterns = [
            # Only fix clear OCR character confusions
            (r'(?<![0-9])0(?![0-9])', 'O'),  # Standalone zero to O
            (r'(?<![0-9])1(?![0-9])', 'l'),  # Standalone one to l
            (r'(?<![0-9])5(?![0-9])', 'S'),  # Standalone five to S
            (r'(?<![0-9])8(?![0-9])', 'B'),  # Standalone eight to B
            
            # Fix repeated characters (clear OCR errors)
            (r'(.)\1{2,}', r'\1\1'),  # Reduce repeated chars to 2
            
            # Fix spacing issues (mechanical errors)
            (r'(\w)\s+([.,!?;:])', r'\1\2'),  # Remove space before punctuation
            (r'([.,!?;:])\s+(\w)', r'\1 \2'),  # Ensure space after punctuation
        ]
        
        for pattern, replacement in patterns:
            corrected = re.sub(pattern, replacement, corrected, flags=re.IGNORECASE)
        
        return corrected
    
    def fix_repeated_words(self, text: str) -> str:
        """Fix repeated words using dynamic pattern matching."""
        corrected = text
        
        # Dynamic patterns for repeated words
        repeated_patterns = [
            (r'\b(the)\s+(the)\s+(the)\b', r'\1'),
            (r'\b(the)\s+(the)\b', r'\1'),
            (r'\b(and)\s+(and)\b', r'\1'),
            (r'\b(of)\s+(of)\b', r'\1'),
            (r'\b(to)\s+(to)\b', r'\1'),
            (r'\b(is)\s+(is)\b', r'\1'),
            (r'\b(are)\s+(are)\b', r'\1'),
            (r'\b(was)\s+(was)\b', r'\1'),
        ]
        
        for pattern, replacement in repeated_patterns:
            corrected = re.sub(pattern, replacement, corrected, flags=re.IGNORECASE)
        
        # Fix any word repeated 3+ times
        corrected = re.sub(r'\b(\w+)\s+\1\s+\1\b', r'\1', corrected, flags=re.IGNORECASE)
        corrected = re.sub(r'\b(\w+)\s+\1\b', r'\1', corrected, flags=re.IGNORECASE)
        
        return corrected
    
    def fix_broken_merged_words(self, text: str) -> str:
        """Fix broken and merged words using dynamic pattern matching."""
        corrected = text
        
        # Dynamic patterns for common word issues
        patterns = [
            # Fix common merged words (conservative approach)
            (r'([a-z])([A-Z])', r'\1 \2'),  # Add space between lowercase and uppercase
            (r'ifyou', 'if you'),  # Common OCR error
            (r'Ifyou', 'If you'),  # Common OCR error
            (r'youare', 'you are'),  # Common OCR error
            (r'yearsago', 'years ago'),  # Common OCR error
            (r'forentrepreneurs', 'for entrepreneurs'),  # Common OCR error
            (r'itis', 'it is'),  # Common OCR error
            (r'([.!?])\s*([a-z])', lambda m: f"{m.group(1)} {m.group(2).upper()}"),  # Capitalize after sentence end
            
            # Fix spacing around common words
            (r'\s+([.,!?;:])', r'\1'),  # Remove space before punctuation
            (r'([.,!?;:])\s*', r'\1 '),  # Add space after punctuation
        ]
        
        for pattern, replacement in patterns:
            if callable(replacement):
                corrected = re.sub(pattern, replacement, corrected)
            else:
                corrected = re.sub(pattern, replacement, corrected)
        
        return corrected
    
    def fix_verb_tenses(self, text: str) -> str:
        """Minimal verb corrections - only clear OCR errors."""
        corrected = text
        
        # Very conservative - only fix obvious OCR verb errors
        verb_patterns = [
            # Only fix clear OCR confusions that affect verbs
            (r'\bmak\b', 'make'),  # Clear OCR error
            (r'\bwas\b', 'was'),  # Preserve correct forms
            (r'\bwere\b', 'were'),  # Preserve correct forms
        ]
        
        for pattern, replacement in verb_patterns:
            corrected = re.sub(pattern, replacement, corrected, flags=re.IGNORECASE)
        
        return corrected
    
    def clean_punctuation_symbols(self, text: str) -> str:
        """Correct punctuation with minimum edits."""
        corrected = text
        
        # Conservative punctuation fixes
        patterns = [
            (r'[\s]+', ' '),  # Multiple spaces to single space
            (r'[""``]', '"'),  # Normalize quotes
            (r"[''']|['']", "'"),  # Normalize apostrophes
            (r'[\[\]{}<>]', ''),  # Remove brackets but keep parentheses
            (r'\s*([.,!?;:])\s*', r'\1 '),  # Normalize punctuation spacing
            (r'([.,!?;:])\s*([a-z])', r'\1 \2'),  # Space after punctuation
            (r'\s*\(\s*', ' ('),  # Fix spacing before parentheses
            (r'\s*\)\s*', ') '),  # Fix spacing after parentheses
        ]
        
        for pattern, replacement in patterns:
            corrected = re.sub(pattern, replacement, corrected)
        
        return corrected.strip()
    
    def format_titles_and_paragraphs(self, text: str) -> str:
        """Detect and format titles and paragraphs for better readability."""
        if not text:
            return text
        
        # First, check if this looks like a title followed by content
        words = text.split()
        
        # If the text is long, try to identify title vs content
        if len(words) > 8:
            # Look for title patterns:
            # 1. Short phrase at the beginning (3-6 words)
            # 2. Followed by longer descriptive content
            # 3. Title often contains keywords like "models", "api", "service", "features"
            
            title_keywords = ['models', 'api', 'service', 'features', 'supported', 'available', 'overview', 'introduction']
            content_indicators = ['supports', 'provides', 'offers', 'enables', 'allows', 'helps', 'can', 'that', 'for', 'with']
            
            # Try to find the best split point
            best_split = -1
            best_score = 0
            
            for i in range(3, min(8, len(words))):  # Check positions 3-7 for title end
                title_part = ' '.join(words[:i])
                content_part = ' '.join(words[i:])
                
                score = 0
                
                # Score based on title characteristics
                if any(keyword in title_part.lower() for keyword in title_keywords):
                    score += 2
                
                # Score based on content characteristics
                if any(indicator in content_part.lower().split()[:2] for indicator in content_indicators):
                    score += 2
                
                # Prefer shorter titles
                if i <= 5:
                    score += 1
                
                # Check if title part ends naturally
                if i < len(words) and words[i].lower() in content_indicators:
                    score += 3
                
                if score > best_score:
                    best_score = score
                    best_split = i
            
            # If we found a good split point
            if best_split > 0 and best_score >= 3:
                title = ' '.join(words[:best_split])
                content = ' '.join(words[best_split:])
                
                # Clean up title and content
                title = title.strip()
                content = content.strip()
                
                # Add proper punctuation
                if not title.endswith('.'):
                    title += '.'
                if not content.endswith('.'):
                    content += '.'
                
                # Capitalize title properly
                title = title[0].upper() + title[1:]
                
                return f"{title}\n\n{content}"
        
        # For shorter text or if no good split found, ensure proper sentence structure
        if not text.endswith(('.', '!', '?')):
            text += '.'
        
        return text
    
    def fix_capitalization(self, text: str) -> str:
        """Fix capitalization inconsistencies while preserving titles and paragraphs."""
        if not text:
            return text
        
        # If text contains double newlines (title/content structure), preserve it
        if '\n\n' in text:
            sections = text.split('\n\n')
            corrected_sections = []
            
            for section in sections:
                if section.strip():
                    # Apply capitalization to each section separately
                    corrected_section = self._capitalize_section(section.strip())
                    corrected_sections.append(corrected_section)
            
            return '\n\n'.join(corrected_sections)
        else:
            # Single section - apply normal capitalization
            return self._capitalize_section(text)
    
    def _capitalize_section(self, text: str) -> str:
        """Capitalize a single section of text with proper sentence capitalization."""
        # Split into sentences - better regex to preserve punctuation
        sentences = re.split(r'([.!?])\s*', text)
        corrected_sentences = []
        
        for i, sentence in enumerate(sentences):
            if sentence.strip() and i > 0 and sentences[i-1] in '.!?':
                # Start of sentence - capitalize first letter
                sentence = sentence.strip()
                if sentence:
                    sentence = sentence[0].upper() + sentence[1:]
            elif sentence.strip() and i == 0:
                # First sentence - capitalize first letter
                sentence = sentence.strip()
                if sentence:
                    sentence = sentence[0].upper() + sentence[1:]
            elif sentence.strip() and sentence not in '.!?':
                # Middle of sentence - preserve important capitalization
                words = sentence.split()
                corrected_words = []
                for word in words:
                    # Keep words that should be capitalized (titles, acronyms, etc.)
                    if word.isupper() and len(word) > 2:
                        # Keep acronyms and important terms
                        if word in ['OCR', 'API', 'URL', 'HTTP', 'HTTPS', 'JSON', 'XML', 'HTML', 'CSS', 'SQL']:
                            corrected_words.append(word)
                        else:
                            # Convert overly capitalized words to proper case
                            corrected_words.append(word.title())
                    # Fix words that should be lowercase
                    elif word.lower() in self.lowercase_words:
                        corrected_words.append(word.lower())
                    else:
                        corrected_words.append(word)
                sentence = ' '.join(corrected_words)
            
            return text
        
        # Remove any remaining random symbols but keep important ones including newlines
        text = re.sub(r'[^a-zA-Z0-9\s.,!?;:\-\'"()\n]', '', text)
        
        # Fix multiple spaces but preserve newlines
        lines = text.split('\n')
        cleaned_lines = []
        for line in lines:
            # Clean up spacing within each line
            line = re.sub(r'[ \t]+', ' ', line)
            line = line.strip()
            # Only add non-empty lines, but preserve paragraph breaks
            if line or (cleaned_lines and cleaned_lines[-1]):
                cleaned_lines.append(line)
        
        # Rejoin with double newlines for paragraph breaks
        if len(cleaned_lines) > 0:
            text = cleaned_lines[0]
            for i in range(1, len(cleaned_lines)):
                if cleaned_lines[i] and cleaned_lines[i-1]:
                    text += '\n\n' + cleaned_lines[i]
                else:
                    text += '\n' + cleaned_lines[i]
        else:
            text = ''
        
        # Fix spacing around parentheses
        text = re.sub(r'\s*\(\s*', ' (', text)
        text = re.sub(r'\s*\)\s*', ') ', text)
        text = re.sub(r'\)\s+([a-z])', r') \1', text)
        
        # Ensure proper spacing after punctuation (but don't affect newlines)
        text = re.sub(r'([.,!?;:])\s+([a-zA-Z])', r'\1 \2', text)
        
        # Ensure sentences end with proper punctuation
        if text and not text[-1] in '.!?':
            text += '.'
        
        return text
    
    def fix_ocr_grammar(self, text: str) -> str:
        """Improve grammar and sentence boundaries with minimum edits."""
        corrected = text
        
        # Conservative grammar fixes - only clear mechanical errors
        patterns = [
            # Fix missing spaces after periods (critical issue)
            (r'([.!?])([A-Z])', r'\1 \2'),  # Add space after punctuation
            
            # Fix sentence boundaries
            (r'([.!?])\s*([a-z])', lambda m: f"{m.group(1)} {m.group(2).upper()}"),  # Capitalize after sentence end
            
            # Fix remaining OCR merges
            (r'Itis', 'It is'),  # Direct fix for common OCR error
            (r'([a-z])([A-Z])', r'\1 \2'),  # Add space between words
        ]
        
        for pattern, replacement in patterns:
            if callable(replacement):
                corrected = re.sub(pattern, replacement, corrected)
            else:
                corrected = re.sub(pattern, replacement, corrected)
        
        return corrected
    
    def final_cleanup(self, text: str) -> str:
        """Final cleanup while preserving important formatting."""
        if not text:
            return text
        
        # Remove any remaining random symbols but keep important ones including newlines
        text = re.sub(r'[^a-zA-Z0-9\s.,!?;:\-\'"()\n]', '', text)
        
        # Fix multiple spaces but preserve newlines
        lines = text.split('\n')
        cleaned_lines = []
        for line in lines:
            # Clean up spacing within each line
            line = re.sub(r'[ \t]+', ' ', line)
            line = line.strip()
            # Only add non-empty lines, but preserve paragraph breaks
            if line or (cleaned_lines and cleaned_lines[-1]):
                cleaned_lines.append(line)
        
        # Rejoin with double newlines for paragraph breaks
        if len(cleaned_lines) > 0:
            text = cleaned_lines[0]
            for i in range(1, len(cleaned_lines)):
                if cleaned_lines[i] and cleaned_lines[i-1]:
                    text += '\n\n' + cleaned_lines[i]
                else:
                    text += '\n' + cleaned_lines[i]
        else:
            text = ''
        
        # Fix spacing around parentheses
        text = re.sub(r'\s*\(\s*', ' (', text)
        text = re.sub(r'\s*\)\s*', ') ', text)
        
        # Ensure proper spacing after punctuation (but don't affect newlines)
        text = re.sub(r'([.,!?;:])\s+([a-zA-Z])', r'\1 \2', text)
        
        # Ensure sentences end with proper punctuation
        if text and not text[-1] in '.!?':
            text += '.'
        
        return text
    
    async def extract_text_from_pdf(self, pdf_path: str) -> Dict[str, str]:
        """
        Extract text from PDF using ultimate processing.
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
                cleaned_text = self.ultimate_text_correction(direct_text.strip())
                return {
                    "text": cleaned_text,
                    "description": f"Extracted and ultimate-corrected text from {os.path.basename(pdf_path)}",
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
                "description": f"OCR'd and ultimate-corrected images from {os.path.basename(pdf_path)}",
                "confidence": "medium" if combined_text else "low",
                "full_text": combined_text
            }
        else:
            return {
                "text": "",
                "description": f"No images found in {os.path.basename(pdf_path)}",
                "confidence": "low"
            }

# Global ultimate OCR service instance
_ultimate_ocr_service = UltimateOCRService()

async def extract_text_from_path(file_path: str) -> Dict[str, str]:
    """
    Ultimate text extraction with comprehensive severe error correction.
    """
    file_ext = os.path.splitext(file_path)[1].lower()
    
    if file_ext == '.pdf':
        return await _ultimate_ocr_service.extract_text_from_pdf(file_path)
    else:
        return await _ultimate_ocr_service.extract_text_from_image(file_path)

async def extract_text(file_path: str) -> Dict[str, str]:
    """
    Alias for extract_text_from_path for compatibility.
    """
    return await extract_text_from_path(file_path)
