import os
import cv2
import numpy as np
from PIL import Image
import pytesseract
from dotenv import load_dotenv

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
def extract_text_from_path(path: str) -> str:
    # Expanded character set to include more special characters and symbols
    valid_chars = set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789 .,!?()[]{}:;-_'\"@#$%&*+=/\\•-–—")
    min_line_length = 2
    min_confidence = 0.4  # More lenient confidence threshold
    min_char_ratio = 0.5  # More lenient character validation

    # Enhanced image preprocessing
    def preprocess_image(img):
        # Convert to grayscale if needed
        if len(img.shape) == 3:
            img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Increase contrast using CLAHE
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        img = clahe.apply(img)
        
        # Denoise
        img = cv2.fastNlMeansDenoising(img, None, 30, 7, 21)
        
        # Thresholding
        _, img = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # Scale up for better recognition
        img = cv2.resize(img, None, fx=1.5, fy=1.5, interpolation=cv2.INTER_CUBIC)
        
        return img

    try:
        # Read and preprocess the image
        img = cv2.imread(path)
        if img is None:
            return "[error] Could not read the image file"
            
        # Generate multiple preprocessed versions
        images = [
            preprocess_image(img),  # Basic preprocessing
            preprocess_image(cv2.bitwise_not(img)),  # Inverted colors
        ]

        # Try different Tesseract configurations
        # Using a simpler character whitelist to avoid parsing issues
        tesseract_configs = [
            '--oem 3 --psm 6 -c preserve_interword_spaces=1',
            '--oem 3 --psm 4 -c preserve_interword_spaces=1',
            '--oem 3 --psm 11 -c preserve_interword_spaces=1',
            '--oem 3 --psm 3 -c preserve_interword_spaces=1',
        ]

        best_text = ""
        best_score = 0

        for img in images:
            for config in tesseract_configs:
                try:
                    # Get text with confidence data
                    data = pytesseract.image_to_data(
                        img, 
                        config=config,
                        output_type=pytesseract.Output.DICT
                    )
                    
                    # Process each text element
                    text_blocks = []
                    for i in range(len(data['text'])):
                        text = data['text'][i].strip()
                        conf = int(data['conf'][i]) / 100.0
                        
                        if not text or (len(text) < 3 and conf < 0.7):
                            continue
                            
                        # More lenient character validation
                        valid_count = sum(1 for c in text if c in valid_chars)
                        if valid_count / max(1, len(text)) >= min_char_ratio:
                            text_blocks.append((
                                text,
                                conf,
                                data['left'][i],
                                data['top'][i],
                                data['width'][i],
                                data['height'][i]
                            ))
                    
                    if not text_blocks:
                        continue
                    
                    # Sort by position (top to bottom, left to right)
                    text_blocks.sort(key=lambda x: (x[3], x[2]))
                    
                    # Group into lines
                    lines = []
                    if text_blocks:
                        current_line = [text_blocks[0]]
                        for block in text_blocks[1:]:
                            if abs(block[3] - current_line[-1][3]) < (current_line[-1][5] * 0.8):
                                current_line.append(block)
                            else:
                                lines.append(current_line)
                                current_line = [block]
                        if current_line:
                            lines.append(current_line)
                    
                    # Reconstruct text
                    current_text = []
                    for line in lines:
                        line.sort(key=lambda x: x[2])
                        line_text = ' '.join(block[0] for block in line)
                        current_text.append(line_text)
                    
                    current_text = '\n'.join(current_text)
                    
                    # Score the text
                    if current_text:
                        valid = sum(c.isalnum() for c in current_text)
                        invalid = sum(1 for c in current_text if c not in valid_chars)
                        score = valid - (invalid * 1.2)  # Reduced penalty
                        
                        if score > best_score:
                            best_score = score
                            best_text = current_text

                except Exception as e:
                    print(f"Warning in OCR processing: {str(e)}")
                    continue

        if not best_text.strip():
            return "[error] No readable text extracted"

        # Post-processing
        final_lines = []
        for line in best_text.splitlines():
            line = line.strip()
            # Keep lines with meaningful content
            if any(c.isalnum() for c in line):
                # Clean up common OCR errors
                line = line.replace("Grog", "Groq")
                line = line.replace("quesiion", "question")
                line = ' '.join(word for word in line.split() if len(word) > 1 or word.isalnum())
                final_lines.append(line)

        return '\n'.join(final_lines).strip()

    except Exception as e:
        return f"[error] {str(e)}"