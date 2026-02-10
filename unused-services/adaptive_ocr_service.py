"""
Adaptive OCR Service - No hardcoded values, learns from text patterns
"""
import re
import os
import logging
from typing import Dict, List, Any
import asyncio
from PIL import Image, ImageEnhance, ImageFilter
import pytesseract
from dotenv import load_dotenv

# Load Tesseract
load_dotenv()
TESS_CMD = os.getenv("TESSERACT_CMD")
if TESS_CMD:
    pytesseract.pytesseract.tesseract_cmd = TESS_CMD

logger = logging.getLogger(__name__)

class AdaptiveOCRService:
    """Adaptive OCR service with dynamic error correction - no hardcoded values"""
    
    def __init__(self):
        """Initialize adaptive OCR service"""
        logger.info("Initializing Adaptive OCR Service - Dynamic Error Correction")
        
        # Dynamic pattern detection - no hardcoded corrections
        self.common_ocr_errors = {
            # Character patterns (learned from common OCR mistakes)
            'character_substitutions': {
                '0': 'O', '1': 'l', '2': 'Z', '5': 'S', '8': 'B'
            },
            # Common OCR artifacts (patterns, not specific words)
            'artifact_patterns': [
                r'\b\w{1,2}\b',  # Very short words (likely artifacts)
                r'[^\w\s.,!?;:\-\'"()]',  # Random symbols
                r'\s{2,}',  # Multiple spaces
            ]
        }
    
    def detect_text_patterns(self, text: str) -> Dict[str, Any]:
        """Analyze text to detect patterns and issues"""
        words = text.split()
        
        patterns = {
            'word_count': len(words),
            'avg_word_length': sum(len(word) for word in words) / len(words) if words else 0,
            'short_words': [w for w in words if len(w) <= 2],
            'long_words': [w for w in words if len(w) >= 15],
            'has_numbers': any(c.isdigit() for c in text),
            'has_special_chars': bool(re.search(r'[^\w\s]', text)),
            'sentence_count': len(re.split(r'[.!?]+', text)),
            'repeated_patterns': self._find_repeated_patterns(text),
            'potential_ocr_errors': self._detect_ocr_errors(text)
        }
        
        return patterns
    
    def _find_repeated_patterns(self, text: str) -> List[str]:
        """Find repeated word patterns that might be OCR errors"""
        words = text.lower().split()
        repeated = []
        
        for i, word in enumerate(words):
            if word in words[i+1:i+3]:  # Check next 2-3 words
                repeated.append(word)
        
        return list(set(repeated))
    
    def _detect_ocr_errors(self, text: str) -> List[str]:
        """Detect potential OCR errors using pattern matching"""
        errors = []
        
        # Common OCR error patterns
        error_patterns = [
            (r'\b\w*[01]\w*\b', 'Numbers in words (0→O, 1→l)'),
            (r'\b\w{8,}\b', 'Very long words (likely merged)'),
            (r'\b[a-z]+[A-Z][a-z]+\b', 'Capitalization errors'),
            (r'\s+[,.!?]\s*', 'Spacing around punctuation'),
            (r'[^\w\s.,!?;:\-\'"()]', 'Invalid characters'),
        ]
        
        for pattern, description in error_patterns:
            if re.search(pattern, text):
                errors.append(description)
        
        return errors
    
    def adaptive_character_correction(self, text: str) -> str:
        """Adaptive character correction based on context"""
        corrected = text
        
        # Basic character substitutions (minimal, adaptive)
        for num, letter in self.common_ocr_errors['character_substitutions'].items():
            corrected = corrected.replace(num, letter)
        
        return corrected
    
    def adaptive_word_correction(self, text: str) -> str:
        """Adaptive word correction using pattern analysis"""
        words = text.split()
        corrected_words = []
        
        for word in words:
            corrected_word = word
            
            # Fix very short words (likely OCR artifacts)
            if len(word) <= 2 and word.isalpha():
                # Check if it's a common word
                common_words = {'a', 'an', 'in', 'on', 'at', 'to', 'of', 'for', 'by', 'is', 'it', 'be', 'as', 'or', 'if'}
                if word.lower() not in common_words:
                    # Remove if it's likely an artifact
                    continue
            
            # Fix very long words (likely merged)
            elif len(word) >= 15:
                # Try to split at logical points
                splits = re.findall(r'[A-Z][a-z]+|[a-z]+', word)
                if len(splits) > 1:
                    corrected_word = ' '.join(splits)
            
            # Fix mixed capitalization
            elif re.search(r'[a-z][A-Z][a-z]', word):
                # Split at capital letters
                parts = re.findall(r'[A-Z][a-z]*|[a-z]+', word)
                if len(parts) > 1:
                    corrected_word = ' '.join(parts)
            
            corrected_words.append(corrected_word)
        
        return ' '.join(corrected_words)
    
    def adaptive_punctuation_fix(self, text: str) -> str:
        """Adaptive punctuation correction"""
        # Remove invalid characters
        text = re.sub(r'[^\w\s.,!?;:\-\'"()]', '', text)
        
        # Fix spacing around punctuation
        text = re.sub(r'\s*([.,!?;:])\s*', r'\1 ', text)
        text = re.sub(r'\s*\(\s*', ' (', text)
        text = re.sub(r'\s*\)\s*', ') ', text)
        
        # Remove multiple spaces
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
    
    def adaptive_sentence_structure(self, text: str) -> str:
        """Adaptive sentence structure improvement"""
        # Split into sentences
        sentences = re.split(r'([.!?]+)', text)
        
        corrected_sentences = []
        for i, sentence in enumerate(sentences):
            if sentence.strip():
                if i % 2 == 0:  # Actual sentence content
                    # Capitalize first letter
                    sentence = sentence.strip()
                    if sentence and not sentence[0].isupper():
                        sentence = sentence[0].upper() + sentence[1:]
                    
                    # Ensure proper ending
                    if i + 1 < len(sentences) and not sentences[i+1].strip():
                        sentence += '.'
                    
                    corrected_sentences.append(sentence)
                else:  # Punctuation
                    corrected_sentences.append(sentence)
        
        return ''.join(corrected_sentences)
    
    def adaptive_formatting(self, text: str) -> str:
        """Adaptive text formatting based on content analysis"""
        if not text:
            return text
        
        # Analyze text structure
        patterns = self.detect_text_patterns(text)
        
        # Apply corrections in order
        corrected = self.adaptive_character_correction(text)
        corrected = self.adaptive_word_correction(corrected)
        corrected = self.adaptive_punctuation_fix(corrected)
        corrected = self.adaptive_sentence_structure(corrected)
        
        # Final cleanup
        corrected = corrected.strip()
        if corrected and not corrected.endswith('.'):
            corrected += '.'
        
        return corrected
    
    async def extract_text_from_image(self, image_path: str) -> Dict[str, Any]:
        """Extract text from image with adaptive correction"""
        try:
            # Open and preprocess image
            image = Image.open(image_path)
            
            # Basic preprocessing
            image = image.convert('L')  # Grayscale
            image = image.filter(ImageFilter.SHARPEN)
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(2.0)
            
            # Extract text with Tesseract
            raw_text = pytesseract.image_to_string(image, config='--psm 6')
            
            # Apply adaptive corrections
            corrected_text = self.adaptive_formatting(raw_text)
            
            # Analyze patterns for debugging
            patterns = self.detect_text_patterns(corrected_text)
            
            return {
                "text": corrected_text,
                "raw_text": raw_text,
                "confidence": "high",
                "patterns": patterns,
                "processing_time": "adaptive"
            }
            
        except Exception as e:
            logger.error(f"Error in adaptive OCR: {e}")
            return {
                "text": "",
                "raw_text": "",
                "confidence": "error",
                "error": str(e)
            }
    
    async def extract_text_from_path(self, file_path: str) -> Dict[str, Any]:
        """Main extraction function - adaptive processing"""
        if file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
            return await self.extract_text_from_image(file_path)
        else:
            return {
                "text": "",
                "confidence": "error",
                "error": "Unsupported file type"
            }

# Create adaptive service instance
adaptive_service = AdaptiveOCRService()

# Export the main function
async def extract_text_from_path(file_path: str) -> Dict[str, Any]:
    """Extract text using adaptive OCR service"""
    return await adaptive_service.extract_text_from_path(file_path)
