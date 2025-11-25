import fitz  # PyMuPDF
from pdf2image import convert_from_path
import os
from typing import List, Tuple
from pathlib import Path

class PDFService:
    @staticmethod
    async def pdf_to_images(pdf_path: str, output_dir: str = "temp_images") -> List[str]:
        """Convert PDF pages to images and return list of image paths"""
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Convert PDF to images
        images = convert_from_path(pdf_path)
        image_paths = []
        
        # Save each page as an image
        for i, image in enumerate(images):
            image_path = os.path.join(output_dir, f"page_{i+1}.jpg")
            image.save(image_path, "JPEG")
            image_paths.append(image_path)
            
        return image_paths

    @staticmethod
    def extract_text_from_pdf(pdf_path: str) -> str:
        """Extract text directly from PDF"""
        text = ""
        with fitz.open(pdf_path) as doc:
            for page in doc:
                text += page.get_text()
        return text