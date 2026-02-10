"""
Optimized OCR Service using PaddleOCR for much faster processing.
This replaces the slow Tesseract OCR service.
"""
import os
import cv2
import numpy as np
from typing import List, Dict, Any, Optional, Tuple, Union
from PIL import Image
import fitz  # PyMuPDF
from paddleocr import PaddleOCR
import logging
import asyncio
from concurrent.futures import ThreadPoolExecutor
import time
import io

# Set environment variable to bypass PaddleOCR model download check
os.environ['PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK'] = 'True'

logger = logging.getLogger(__name__)

class OptimizedOCRService:
    """Optimized OCR service using PaddleOCR for fast processing."""
    
    def __init__(self, use_gpu: bool = False, lang: str = 'en'):
        """
        Initialize the optimized OCR service.
        
        Args:
            use_gpu: Whether to use GPU for inference (requires CUDA)
            lang: Language code for OCR (e.g., 'en', 'fr', 'es')
        """
        self.use_gpu = use_gpu
        self.lang = lang
        self.ocr_engine = None
        self.executor = ThreadPoolExecutor(max_workers=4)  # For parallel processing
        
    def initialize(self):
        """Lazy initialization of the OCR engine."""
        if self.ocr_engine is None:
            logger.info(f"Initializing PaddleOCR (GPU: {self.use_gpu}, Language: {self.lang})")
            start_time = time.time()
            
            try:
                self.ocr_engine = PaddleOCR(
                    use_angle_cls=True,
                    lang=self.lang,
                )
                
                init_time = time.time() - start_time
                logger.info(f"PaddleOCR initialized successfully in {init_time:.2f} seconds")
                
            except Exception as e:
                logger.error(f"Failed to initialize PaddleOCR: {str(e)}")
                raise
    
    def preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """
        Fast image preprocessing optimized for OCR speed.
        """
        # Convert to grayscale if needed
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()
        
        # Resize for faster processing (PaddleOCR works well with 720p)
        height, width = gray.shape
        if max(height, width) > 720:
            scale = 720 / max(height, width)
            new_width = int(width * scale)
            new_height = int(height * scale)
            gray = cv2.resize(gray, (new_width, new_height), interpolation=cv2.INTER_AREA)
        
        # Apply minimal preprocessing for speed
        # Skip heavy preprocessing that slows down Tesseract
        return gray
    
    async def extract_text_from_image(self, image_path: str) -> Dict[str, str]:
        """
        Extract text from image using optimized PaddleOCR.
        """
        self.initialize()
        
        try:
            # Read image
            image = cv2.imread(image_path)
            if image is None:
                raise ValueError(f"Could not read image: {image_path}")
            
            # Preprocess
            processed_image = self.preprocess_image(image)
            
            # Run OCR in thread pool for non-blocking
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                self.executor, 
                self._run_ocr, 
                processed_image
            )
            
            # Extract text from PaddleOCR result
            text_parts = []
            if result and len(result) > 0:
                # PaddleOCR returns different formats, handle both
                ocr_result = result[0] if isinstance(result, list) and len(result) > 0 else result
                
                if ocr_result:
                    for line in ocr_result:
                        if line and len(line) >= 2:
                            # Handle different PaddleOCR result formats
                            if isinstance(line[1], (list, tuple)) and len(line[1]) > 0:
                                text = line[1][0]  # Format: [[x1,y1,x2,y2], [text, confidence]]
                            elif isinstance(line[1], str):
                                text = line[1]  # Format: [[x1,y1,x2,y2], text]
                            else:
                                continue
                            
                            if text and text.strip():
                                text_parts.append(text.strip())
            
            extracted_text = "\\n".join(text_parts)
            
            return {
                "text": extracted_text,
                "description": f"Extracted text from {os.path.basename(image_path)} using PaddleOCR",
                "confidence": "high" if extracted_text else "low"
            }
            
        except Exception as e:
            logger.error(f"Error extracting text from {image_path}: {str(e)}")
            return {
                "text": "",
                "description": f"Error processing {os.path.basename(image_path)}: {str(e)}",
                "confidence": "error"
            }
    
    def _run_ocr(self, image: np.ndarray) -> List:
        """Run PaddleOCR on preprocessed image."""
        return self.ocr_engine.ocr(image)
    
    async def extract_text_from_pdf(self, pdf_path: str) -> Dict[str, str]:
        """
        Extract text from PDF using optimized processing.
        """
        try:
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
                return {
                    "text": direct_text.strip(),
                    "description": f"Extracted direct text from {os.path.basename(pdf_path)}",
                    "confidence": "high"
                }
            
            # If no direct text, extract images and OCR them
            return await self._ocr_pdf_images(doc, pdf_path)
            
        except Exception as e:
            logger.error(f"Error extracting text from PDF {pdf_path}: {str(e)}")
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
            
            # Combine results
            all_text = []
            for result in results:
                if isinstance(result, dict) and result.get("text"):
                    all_text.append(result["text"])
            
            # Cleanup temp files
            for page_num in range(min(len(doc), 10)):
                for img_index in range(len(doc[page_num].get_images())):
                    temp_path = f"/tmp/pdf_page_{page_num}_{img_index}.png"
                    if os.path.exists(temp_path):
                        os.remove(temp_path)
            
            combined_text = "\\n".join(all_text)
            
            return {
                "text": combined_text,
                "description": f"OCR'd images from {os.path.basename(pdf_path)}",
                "confidence": "medium" if combined_text else "low"
            }
        
        return {
            "text": "",
            "description": f"No images found in {os.path.basename(pdf_path)}",
            "confidence": "low"
        }

# Global optimized OCR service instance
_optimized_ocr_service = OptimizedOCRService(use_gpu=False, lang='en')

async def extract_text_from_path(file_path: str) -> Dict[str, str]:
    """
    Fast text extraction using optimized PaddleOCR service.
    """
    file_ext = os.path.splitext(file_path)[1].lower()
    
    if file_ext == '.pdf':
        return await _optimized_ocr_service.extract_text_from_pdf(file_path)
    else:
        return await _optimized_ocr_service.extract_text_from_image(file_path)

async def extract_text(file_path: str) -> Dict[str, str]:
    """
    Alias for extract_text_from_path for compatibility.
    """
    return await extract_text_from_path(file_path)
