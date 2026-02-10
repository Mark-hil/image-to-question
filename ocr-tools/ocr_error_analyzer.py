"""
OCR Error Analysis Tool
Analyzes OCR text and identifies specific OCR-related errors.
"""
import re
from typing import Dict, List, Tuple
import string

class OCRErrorAnalyzer:
    """Analyzes OCR text and categorizes errors."""
    
    def __init__(self):
        # Common OCR character substitutions
        self.ocr_char_errors = {
            '0': 'O', '1': 'I', '2': 'Z', '5': 'S', '8': 'B',
            'l': '1', 'o': '0', '|': 'I', 'rn': 'm', 'vv': 'w',
            'cl': 'd', 'nn': 'm', 'ii': 'u', 'vv': 'w'
        }
        
        # Common word patterns that indicate OCR errors
        self.suspicious_patterns = [
            r'[A-Z]{2,}',  # Multiple consecutive capitals
            r'[a-z][A-Z][a-z]',  # Mixed case in middle of word
            r'\w{15,}',  # Very long words (likely merged)
            r'[a-z]{1,2}\s+[a-z]{1,2}\s+[a-z]{1,2}',  # Many short words
            r'[A-Z][a-z]+[A-Z][a-z]+',  # CamelCase words
        ]
        
        # Common OCR punctuation errors
        self.punctuation_errors = [
            r'[\s]{2,}',  # Multiple spaces
            r'[.!?]{2,}',  # Multiple punctuation
            r'[^a-zA-Z0-9\s.,!?;:\-\'"]',  # Random symbols
        ]
    
    def analyze_text(self, text: str) -> Dict:
        """Analyze OCR text and categorize errors."""
        errors = {
            'spelling_errors': [],
            'word_segmentation_errors': [],
            'grammar_errors': [],
            'punctuation_capitalization_errors': [],
            'statistics': {
                'total_words': 0,
                'error_count': 0,
                'error_percentage': 0
            }
        }
        
        words = text.split()
        errors['statistics']['total_words'] = len(words)
        
        # Analyze each word for errors
        for i, word in enumerate(words):
            word_errors = self._analyze_word(word, i, words)
            
            if word_errors['spelling']:
                errors['spelling_errors'].extend(word_errors['spelling'])
            
            if word_errors['segmentation']:
                errors['word_segmentation_errors'].extend(word_errors['segmentation'])
            
            if word_errors['grammar']:
                errors['grammar_errors'].extend(word_errors['grammar'])
            
            if word_errors['punctuation']:
                errors['punctuation_capitalization_errors'].extend(word_errors['punctuation'])
        
        # Analyze punctuation and spacing
        punctuation_errors = self._analyze_punctuation(text)
        errors['punctuation_capitalization_errors'].extend(punctuation_errors)
        
        # Calculate statistics
        total_errors = sum(len(errors[key]) for key in errors if key != 'statistics')
        errors['statistics']['error_count'] = total_errors
        errors['statistics']['error_percentage'] = (total_errors / len(words)) * 100 if words else 0
        
        return errors
    
    def _analyze_word(self, word: str, index: int, all_words: List[str]) -> Dict:
        """Analyze a single word for various error types."""
        errors = {
            'spelling': [],
            'segmentation': [],
            'grammar': [],
            'punctuation': []
        }
        
        # Check for spelling errors (character substitutions)
        if self._has_ocr_char_errors(word):
            errors['spelling'].append({
                'word': word,
                'position': index,
                'type': 'character_substitution',
                'suggested_fix': self._fix_ocr_chars(word)
            })
        
        # Check for word segmentation errors
        if self._is_merged_word(word):
            errors['segmentation'].append({
                'word': word,
                'position': index,
                'type': 'merged_word',
                'suggested_fix': self._split_merged_word(word)
            })
        
        if self._is_fragmented_word(word, index, all_words):
            errors['segmentation'].append({
                'word': word,
                'position': index,
                'type': 'fragmented_word',
                'context': f"...{all_words[max(0,index-1):index+2]}..."
            })
        
        # Check for capitalization errors
        if self._has_capitalization_error(word, index, all_words):
            errors['punctuation'].append({
                'word': word,
                'position': index,
                'type': 'capitalization_error',
                'suggested_fix': self._fix_capitalization(word, index, all_words)
            })
        
        return errors
    
    def _has_ocr_char_errors(self, word: str) -> bool:
        """Check if word has OCR character substitution errors."""
        for old, new in self.ocr_char_errors.items():
            if old in word:
                return True
        return False
    
    def _fix_ocr_chars(self, word: str) -> str:
        """Fix OCR character substitutions."""
        fixed = word
        for old, new in self.ocr_char_errors.items():
            fixed = fixed.replace(old, new)
        return fixed
    
    def _is_merged_word(self, word: str) -> bool:
        """Check if word is likely multiple words merged together."""
        # Very long words are likely merged
        if len(word) > 15:
            return True
        
        # Check for camel case patterns
        if re.search(r'[a-z][A-Z][a-z]', word):
            return True
        
        # Check for multiple capital letters
        if re.search(r'[A-Z]{2,}', word):
            return True
        
        return False
    
    def _split_merged_word(self, word: str) -> List[str]:
        """Suggest how to split a merged word."""
        # Split at capital letters
        parts = re.findall(r'[A-Z][a-z]*|[a-z]+', word)
        return parts if len(parts) > 1 else [word]
    
    def _is_fragmented_word(self, word: str, index: int, all_words: List[str]) -> bool:
        """Check if word is likely a fragment of a larger word."""
        # Very short words in the middle of text
        if len(word) <= 2 and 0 < index < len(all_words) - 1:
            return True
        
        # Words that look like they should be combined with neighbors
        if index > 0 and index < len(all_words) - 1:
            prev_word = all_words[index - 1]
            next_word = all_words[index + 1]
            
            # Check if combining makes sense
            combined = prev_word + word
            if len(combined) <= 12 and combined.lower() in ['personal', 'hygiene', 'cleanliness']:
                return True
        
        return False
    
    def _has_capitalization_error(self, word: str, index: int, all_words: List[str]) -> bool:
        """Check for capitalization errors."""
        # Random capitalization in middle of sentence
        if index > 0 and word.isupper() and len(word) > 2:
            prev_word = all_words[index - 1]
            if not prev_word.endswith(('.', '!', '?')):
                return True
        
        # Lowercase at beginning of sentence
        if index == 0 and word and word[0].islower():
            return True
        
        return False
    
    def _fix_capitalization(self, word: str, index: int, all_words: List[str]) -> str:
        """Suggest capitalization fix."""
        if index == 0:
            return word.capitalize()
        elif word.isupper() and len(word) > 2:
            return word.lower()
        return word
    
    def _analyze_punctuation(self, text: str) -> List[Dict]:
        """Analyze punctuation and spacing errors."""
        errors = []
        
        # Multiple spaces
        if re.search(r'\s{3,}', text):
            errors.append({
                'type': 'excessive_spacing',
                'example': 'multiple spaces found',
                'suggested_fix': 'normalize spacing'
            })
        
        # Random symbols
        symbols = re.findall(r'[^a-zA-Z0-9\s.,!?;:\-\'"]', text)
        if symbols:
            errors.append({
                'type': 'random_symbols',
                'examples': list(set(symbols))[:5],
                'suggested_fix': 'remove non-text symbols'
            })
        
        # Missing punctuation at sentence end
        sentences = re.split(r'[.!?]', text)
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) > 20 and sentence and not sentence.endswith(('.', '!', '?')):
                errors.append({
                    'type': 'missing_punctuation',
                    'example': sentence[:30] + '...',
                    'suggested_fix': 'add sentence-ending punctuation'
                })
        
        return errors
    
    def generate_report(self, errors: Dict) -> str:
        """Generate a readable error analysis report."""
        report = []
        report.append("🔍 OCR ERROR ANALYSIS REPORT")
        report.append("=" * 50)
        
        # Statistics
        stats = errors['statistics']
        report.append(f"📊 STATISTICS:")
        report.append(f"   Total Words: {stats['total_words']}")
        report.append(f"   Error Count: {stats['error_count']}")
        report.append(f"   Error Percentage: {stats['error_percentage']:.1f}%")
        report.append("")
        
        # Spelling Errors
        if errors['spelling_errors']:
            report.append(f"🔤 SPELLING ERRORS ({len(errors['spelling_errors'])}):")
            for error in errors['spelling_errors'][:10]:  # Show first 10
                report.append(f"   '{error['word']}' → '{error['suggested_fix']}' (pos {error['position']})")
            if len(errors['spelling_errors']) > 10:
                report.append(f"   ... and {len(errors['spelling_errors']) - 10} more")
            report.append("")
        
        # Word Segmentation Errors
        if errors['word_segmentation_errors']:
            report.append(f"📝 WORD SEGMENTATION ERRORS ({len(errors['word_segmentation_errors'])}):")
            for error in errors['word_segmentation_errors'][:10]:
                if error['type'] == 'merged_word':
                    report.append(f"   '{error['word']}' → {' '.join(error['suggested_fix'])} (merged)")
                else:
                    report.append(f"   '{error['word']}' (fragmented) {error.get('context', '')}")
            if len(errors['word_segmentation_errors']) > 10:
                report.append(f"   ... and {len(errors['word_segmentation_errors']) - 10} more")
            report.append("")
        
        # Grammar Errors
        if errors['grammar_errors']:
            report.append(f"📚 GRAMMAR ERRORS ({len(errors['grammar_errors'])}):")
            for error in errors['grammar_errors'][:5]:
                report.append(f"   '{error['word']}' (pos {error['position']})")
            report.append("")
        
        # Punctuation & Capitalization Errors
        if errors['punctuation_capitalization_errors']:
            report.append(f"📖 PUNCTUATION & CAPITALIZATION ERRORS ({len(errors['punctuation_capitalization_errors'])}):")
            for error in errors['punctuation_capitalization_errors'][:10]:
                if error['type'] == 'capitalization_error':
                    report.append(f"   '{error['word']}' → '{error['suggested_fix']}' (capitalization)")
                else:
                    report.append(f"   {error['type']}: {error.get('example', error.get('examples', ''))}")
            if len(errors['punctuation_capitalization_errors']) > 10:
                report.append(f"   ... and {len(errors['punctuation_capitalization_errors']) - 10} more")
            report.append("")
        
        if not any(errors[key] for key in errors if key != 'statistics'):
            report.append("✅ No significant OCR errors detected!")
        
        return "\n".join(report)

def analyze_ocr_text(text: str) -> str:
    """Analyze OCR text and return formatted report."""
    analyzer = OCRErrorAnalyzer()
    errors = analyzer.analyze_text(text)
    return analyzer.generate_report(errors)

if __name__ == "__main__":
    # Test with sample OCR text
    sample_text = """TT WHATIS PERSONAL HYGIENE? Personal hygiene is the science a erchie tonal deanliness ie. and Practice of preserving, health of food handlers person doing the cooking enka personal hy giene is the deanliness of the cook or any fife preparation of food peas nees food. Personal deanliness is very essential in even! gi : a a thefood. Italsomakes thefood tobesafetaeat. et? om being transferred into iS aa ENSURING PERSONAL HYGIENE ./ Care of the ee The hands must be washed thoroughly and frequently; always washed your hands: each time you enter the work area, after nose blowing or sneezing, after touching spots Cy cuts, after visiting the toilet, after handling dirty store and stock items and chemical deaning agents."""
    
    print(analyze_ocr_text(sample_text))
