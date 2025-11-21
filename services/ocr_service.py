import os
import re
import cv2
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter
import pytesseract
from dotenv import load_dotenv
from typing import List, Tuple, Optional, Dict, Any, Union
import json
import sys

# Add the project root to the path to allow absolute imports
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


# =====================================================
#  HELPER: Deskew the image (important for stylized text)
# =====================================================
def deskew_image(gray_np):
    coords = np.column_stack(np.where(gray_np > 0))
    angle = cv2.minAreaRect(coords)[-1]

    # Correct the angle
    if angle < -45:
        angle = -(90 + angle)
    else:
        angle = -angle

    (h, w) = gray_np.shape
    M = cv2.getRotationMatrix2D((w // 2, h // 2), angle, 1.0)
    deskewed = cv2.warpAffine(gray_np, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
    return deskewed


# =====================================================
#  PREPROCESSING PIPELINE
# =====================================================
def generate_preprocessed_images(image_path: str) -> list[Image.Image]:
    """Generates multiple enhanced versions of the image to increase OCR accuracy."""

    pil_img = Image.open(image_path)
    img_gray = pil_img.convert("L")
    img_np = np.array(img_gray)

    # Normalize brightness / contrast
    img_np = cv2.normalize(img_np, None, 0, 255, cv2.NORM_MINMAX)

    # Deskew the image
    try:
        img_np = deskew_image(img_np)
    except:
        pass  # skip deskew if problematic

    # Resize for sharper OCR (Tesseract likes >300 DPI)
    scale_factor = 2.0
    img_np = cv2.resize(img_np, None, fx=scale_factor, fy=scale_factor, interpolation=cv2.INTER_CUBIC)

    # CLAHE (Adaptive histogram equalization)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    img_clahe = clahe.apply(img_np)

    # Denoise
    denoised = cv2.fastNlMeansDenoising(img_clahe, None, 30, 7, 21)

    # Sharpen
    kernel_sharp = np.array([[-1,-1,-1], [-1, 9,-1], [-1,-1,-1]])
    sharpened = cv2.filter2D(denoised, -1, kernel_sharp)

    # Threshold types
    _, thresh_otsu = cv2.threshold(sharpened, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    thresh_gauss = cv2.adaptiveThreshold(
        sharpened, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY, 31, 5
    )

    # Morphological enhancements
    kernel = np.ones((2, 2), np.uint8)
    thick = cv2.dilate(thresh_gauss, kernel, iterations=1)
    thin = cv2.erode(thresh_gauss, kernel, iterations=1)

    # Collect all variants
    images = [
        pil_img,
        Image.fromarray(img_np),
        Image.fromarray(sharpened),
        Image.fromarray(thresh_otsu),
        Image.fromarray(thresh_gauss),
        Image.fromarray(thick),
        Image.fromarray(thin)
    ]

    return images


# =====================================================
#  OCR HANDLER
# =====================================================
def preprocess_image(img: np.ndarray, method: str = 'default') -> np.ndarray:
    """Apply various preprocessing techniques to enhance text visibility."""
    # Convert to grayscale if needed
    if len(img.shape) == 3:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    if method == 'adaptive':
        # Adaptive thresholding
        img = cv2.adaptiveThreshold(
            img, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY, 11, 2
        )
    elif method == 'clahe':
        # CLAHE for better contrast
        clahe = cv2.createCLAHE(clipLimit=4.0, tileGridSize=(8, 8))
        img = clahe.apply(img)
    
    # Apply denoising
    img = cv2.fastNlMeansDenoising(img, None, h=10, templateWindowSize=7, searchWindowSize=21)
    
    # Resize for better recognition (maintain aspect ratio)
    height, width = img.shape
    if max(height, width) < 1500:  # Only scale up smaller images
        scale = 2.0
        img = cv2.resize(img, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
    
    # Apply sharpening
    kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
    img = cv2.filter2D(img, -1, kernel)
    
    return img

def get_tesseract_configs() -> List[Tuple[str, str]]:
    """Generate different Tesseract configurations to try."""
    configs = []
    
    # Try different page segmentation modes
    psms = [
        '3',  # Fully automatic page segmentation, no OSD
        '4',  # Assume a single column of text of variable sizes
        '6',  # Assume a single uniform block of text
        '11',  # Sparse text with OSD
        '12',  # Sparse text
    ]
    
    # Try different OEMs (OCR Engine Modes)
    oems = ['1', '3']  # 1 = Legacy, 3 = Default (LSTM)
    
    # Generate all combinations
    for psm in psms:
        for oem in oems:
            configs.append(f'--oem {oem} --psm {psm} -c preserve_interword_spaces=1')
    
    return configs

def process_ocr_result(data: dict, min_confidence: float = 0.3) -> List[dict]:
    """Process Tesseract OCR results into structured data."""
    text_blocks = []
    
    for i in range(len(data['text'])):
        text = data['text'][i].strip()
        if not text:
            continue
            
        conf = float(data['conf'][i]) / 100.0
        if conf < min_confidence and len(text) < 3:
            continue
            
        text_blocks.append({
            'text': text,
            'conf': conf,
            'x': data['left'][i],
            'y': data['top'][i],
            'w': data['width'][i],
            'h': data['height'][i],
            'block_num': data['block_num'][i],
            'line_num': data['line_num'][i],
            'word_num': data['word_num'][i]
        })
    
    return text_blocks

def group_text_blocks(blocks: List[dict]) -> List[List[dict]]:
    """Group text blocks into lines and sort them."""
    if not blocks:
        return []
    
    # Sort by vertical position, then horizontal
    blocks.sort(key=lambda b: (b['y'], b['x']))
    
    # Group into lines
    lines = []
    current_line = [blocks[0]]
    
    for block in blocks[1:]:
        # Check if block is on the same line (with some tolerance)
        last_block = current_line[-1]
        y_diff = abs(block['y'] - last_block['y'])
        
        if y_diff < (last_block['h'] * 0.5):  # 50% height tolerance
            current_line.append(block)
        else:
            # Sort line by x-coordinate
            current_line.sort(key=lambda b: b['x'])
            lines.append(current_line)
            current_line = [block]
    
    if current_line:
        current_line.sort(key=lambda b: b['x'])
        lines.append(current_line)
    
    return lines

def post_process_text(text: str) -> str:
    """Clean and normalize the extracted text."""
    if not text:
        return ""
    
    # Common OCR error corrections
    corrections = {
        r'\bGrog\b': 'Groq',
        r'\bquesiion\b': 'question',
        r'\bteh\b': 'the',
        r'\bth e\b': 'the',
        r'\bwi th\b': 'with',
        r'\bw1th\b': 'with',
        r'\btne\b': 'the',
        r'\bnat\b': 'not',
        r'\bdeforiied\b': 'deformed',
        r'\b1s\b': 'is',
        r'\bwh1ch\b': 'which',
        r'\bth1s\b': 'this',
        r'\b0r\b': 'or',
        r'\b1n\b': 'in',
        r'\b1t\b': 'it',
        r'\bw1ll\b': 'will',
    }
    
    # Apply corrections
    for pattern, replacement in corrections.items():
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    
    # Remove isolated characters and normalize spaces
    words = []
    for word in text.split():
        if len(word) > 1 or word.isalnum():
            words.append(word)
    
    return ' '.join(words)

def extract_text_from_path(
    path: str, 
    generate_questions: bool = False, 
    qtype: str = "mcq", 
    difficulty: str = "medium"
) -> Union[str, Dict[str, Any]]:
    """
    Extract text from an image using Tesseract OCR with enhanced preprocessing.
    
    Args:
        path: Path to the image file
        generate_questions: If True, generates questions from the extracted text
        qtype: Type of questions to generate (e.g., 'mcq', 'true_false', 'short_answer')
        difficulty: Difficulty level of questions ('easy', 'medium', 'hard')
        
    Returns:
        If generate_questions is False, returns the extracted text as a string.
        If generate_questions is True, returns a dictionary containing both the 
        extracted text and the generated questions.
    """
    try:
        # Read the image
        img = cv2.imread(path)
        if img is None:
            return "[error] Could not read the image file"
        
        # Initialize variables
        best_text = ""
        best_score = 0
        
        # Generate multiple preprocessed versions
        preprocess_methods = ['default', 'adaptive', 'clahe']
        images = [preprocess_image(img, method) for method in preprocess_methods]
        images.append(cv2.bitwise_not(images[0]))  # Add inverted version
        
        # Get Tesseract configurations
        tesseract_configs = get_tesseract_configs()
        
        best_text = ""
        best_score = 0
        
        for img in images:
            for config in tesseract_configs:
                try:
                    # Run Tesseract
                    data = pytesseract.image_to_data(
                        img,
                        config=config,
                        output_type=pytesseract.Output.DICT
                    )
                    
                    # Process results
                    text_blocks = process_ocr_result(data)
                    if not text_blocks:
                        continue
                    
                    # Group into lines and reconstruct text
                    lines = group_text_blocks(text_blocks)
                    current_text = '\n'.join(
                        ' '.join(block['text'] for block in line)
                        for line in lines
                    )
                    
                    # Score the text (favor more alphanumeric characters)
                    if current_text:
                        alpha_count = sum(c.isalnum() for c in current_text)
                        total_chars = max(1, len(current_text))
                        score = (alpha_count / total_chars) * 100
                        
                        if score > best_score:
                            best_score = score
                            best_text = current_text
                
                except Exception as e:
                    print(f"Warning in OCR processing: {str(e)}")
                    continue
        
        if not best_text.strip():
            return "[error] No readable text could be extracted"
        
        # Post-process the best result
        final_lines = []
        for line in best_text.splitlines():
            line = post_process_text(line.strip())
            if any(c.isalnum() for c in line):
                final_lines.append(line)
        
        return '\n'.join(final_lines).strip()
    
    except Exception as e:
        return f"[error] {str(e)}"