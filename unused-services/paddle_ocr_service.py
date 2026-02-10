"""
PaddleOCR Service for text extraction from images and PDFs.
This service provides an alternative to Tesseract OCR with potentially better accuracy for certain types of documents.
"""
import os
import cv2
import numpy as np
from typing import List, Dict, Any, Optional, Tuple, Union
from PIL import Image
import fitz  # PyMuPDF
from paddleocr import PaddleOCR
import logging

logger = logging.getLogger(__name__)

class PaddleOCRService:
    """Service for handling OCR operations using PaddleOCR."""
    
    def __init__(self, use_gpu: bool = False, lang: str = 'en'):
        """
        Initialize the PaddleOCR service.
        
        Args:
            use_gpu: Whether to use GPU for inference (requires CUDA)
            lang: Language code for OCR (e.g., 'en', 'fr', 'es')
        """
        self.use_gpu = use_gpu
        self.lang = lang
        self.ocr_engine = None
        
    def initialize(self):
        """Lazy initialization of the OCR engine."""
        if self.ocr_engine is None:
            logger.info(f"Initializing PaddleOCR (GPU: {self.use_gpu}, Language: {self.lang})")
            try:
                self.ocr_engine = PaddleOCR(
                    use_angle_cls=True,
                    lang=self.lang,
                    use_gpu=self.use_gpu,
                    show_log=False,
                    enable_mkldnn=False,
                    use_tensorrt=False,
                    drop_score=0.5
                )
                logger.info("PaddleOCR initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize PaddleOCR: {str(e)}")
                raise
    
    def preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """
        Preprocess image to improve OCR accuracy.
        
        Args:
            image: Input image as numpy array (BGR format from OpenCV)
            
        Returns:
            Preprocessed image as numpy array
        """
        # Convert to grayscale
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
            
        # Apply adaptive thresholding
        processed = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY, 11, 2
        )
        
        # Apply slight blur to reduce noise
        processed = cv2.GaussianBlur(processed, (3, 3), 0)
        
        # Convert back to 3 channels for PaddleOCR
        if len(processed.shape) == 2:
            processed = cv2.cvtColor(processed, cv2.COLOR_GRAY2BGR)
            
        return processed
    
    def extract_text(self, image_path: str) -> Dict[str, Any]:
        """Extract text from an image using PaddleOCR."""
        self.initialize()
        
        try:
            # Read image
            img = cv2.imread(image_path)
            if img is None:
                raise ValueError(f"Could not read image at {image_path}")
                
            # Run OCR
            result = self.ocr_engine.ocr(img, cls=True)
            
            # Process results
            text_blocks = []
            words = []
            
            if result and len(result) > 0:
                for line in result[0]:
                    if line and len(line) >= 2:
                        try:
                            # Extract text and confidence
                            text = str(line[1][0]) if len(line) > 1 and len(line[1]) > 0 else ""
                            confidence = float(line[1][1]) if len(line) > 1 and len(line[1]) > 1 else 0.0
                            bbox = [list(map(float, point)) for point in line[0]] if line[0] else []
                            
                            if text.strip():  # Only add non-empty text
                                words.append({
                                    'text': text,
                                    'confidence': confidence,
                                    'bbox': bbox
                                })
                                text_blocks.append(text)
                        except Exception as e:
                            logger.warning(f"Error processing OCR line: {str(e)}")
                            continue
            
            return {
                'text': '\n'.join(text_blocks) if text_blocks else "",
                'words': words,
                'full_result': result[0] if result else []
            }
            
        except Exception as e:
            logger.error(f"Error in PaddleOCR text extraction: {str(e)}", exc_info=True)
            return {
                'text': '',
                'words': [],
                'full_result': [],
                'error': str(e)
            }
    
    def extract_text_from_pdf(self, pdf_path: str, dpi: int = 300) -> Dict[str, Any]:
        """
        Extract text from a PDF file.
        
        Args:
            pdf_path: Path to the PDF file
            dpi: DPI for rendering PDF pages
            
        Returns:
            Dictionary with page-wise text extraction results
        """
        self.initialize()
        
        try:
            import fitz  # PyMuPDF
            from pdf2image import convert_from_path
            
            results = {
                'pages': [],
                'full_text': '',
                'total_pages': 0
            }
            
            # Get total pages
            with fitz.open(pdf_path) as doc:
                total_pages = len(doc)
                results['total_pages'] = total_pages
            
            # Process each page
            for page_num in range(total_pages):
                try:
                    # Convert PDF page to image
                    images = convert_from_path(
                        pdf_path, 
                        first_page=page_num + 1, 
                        last_page=page_num + 1,
                        dpi=dpi,
                        fmt='jpeg'
                    )
                    
                    if not images:
                        continue
                        
                    # Save temp image
                    temp_img_path = f"temp_page_{page_num + 1}.jpg"
                    images[0].save(temp_img_path, 'JPEG')
                    
                    # Extract text from the image
                    page_result = self.extract_text(temp_img_path)
                    
                    # Clean up
                    if os.path.exists(temp_img_path):
                        os.remove(temp_img_path)
                    
                    # Add to results
                    results['pages'].append({
                        'page': page_num + 1,
                        'text': page_result.get('text', ''),
                        'words': page_result.get('words', []),
                        'error': page_result.get('error')
                    })
                    
                    results['full_text'] += f"\n\n--- Page {page_num + 1} ---\n{page_result.get('text', '')}"
                    
                except Exception as e:
                    logger.error(f"Error processing PDF page {page_num + 1}: {str(e)}", exc_info=True)
                    results['pages'].append({
                        'page': page_num + 1,
                        'error': str(e)
                    })
            
            return results
            
        except Exception as e:
            logger.error(f"Error in PDF text extraction: {str(e)}", exc_info=True)
            return {
                'error': str(e),
                'pages': [],
                'full_text': ''
            }

# Initialize PaddleOCR service with default settings
paddle_ocr_service = PaddleOCRService(
    use_gpu=os.getenv("PADDLE_USE_GPU", "false").lower() == "true",
    lang=os.getenv("PADDLE_LANG", "en")
)

# Initialize immediately if Paddle is the selected engine
if os.getenv("OCR_ENGINE", "paddle").lower() == "paddle":
    try:
        paddle_ocr_service.initialize()
        logger.info("PaddleOCR service initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize PaddleOCR: {str(e)}")
        logger.warning("PaddleOCR will be initialized on first use")

def extract_text_with_paddle_ocr(image_path: str, preprocess: bool = True) -> str:
    """
    Convenience function to extract text using PaddleOCR.
    
    Args:
        image_path: Path to the image file
        preprocess: Whether to apply preprocessing
        
    Returns:
        Extracted text as a single string
    """
    return paddle_ocr_service.extract_text(image_path, preprocess)['text']

def extract_text_from_pdf_with_paddle_ocr(pdf_path: str, dpi: int = 300) -> str:
    """
    Convenience function to extract text from PDF using PaddleOCR.
    
    Args:
        pdf_path: Path to the PDF file
        dpi: DPI for rendering PDF pages
        
    Returns:
        Extracted text from all pages as a single string
    """
    result = paddle_ocr_service.extract_text_from_pdf(pdf_path, dpi)
    return result.get('full_text', '')
