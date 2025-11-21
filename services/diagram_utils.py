# services/diagram_utils.py
import cv2
import numpy as np
import pytesseract
from typing import Tuple, Optional

def contains_diagram(image_path: str, edge_threshold: float = 0.15, line_threshold: int = 10) -> bool:
    """
    Detect if an image contains diagrams, charts, or other non-text elements.
    
    Args:
        image_path: Path to the image file
        edge_threshold: Ratio of edge pixels to total pixels to consider as diagram (0-1)
        line_threshold: Minimum number of lines to consider as diagram
        
    Returns:
        bool: True if diagram is detected
    """
    try:
        img = cv2.imread(image_path)
        if img is None:
            return False
            
        # Convert to grayscale and resize for faster processing
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        height, width = gray.shape
        
        # Edge detection with adaptive thresholding
        edges = cv2.Canny(gray, 50, 150, apertureSize=3)
        edge_ratio = np.count_nonzero(edges) / (height * width)
        
        # Line detection with adjusted parameters
        lines = cv2.HoughLinesP(edges, 1, np.pi/180, 
                              threshold=50,  # Lower threshold for better line detection
                              minLineLength=min(height, width) * 0.1,  # Scale with image size
                              maxLineGap=20)  # Increased gap tolerance
        lines = lines if lines is not None else []
        
        # Debug info
        print(f"Edge ratio: {edge_ratio:.4f}, Lines detected: {len(lines)}")
        
        # More conservative detection - require both conditions for diagram
        is_diagram = edge_ratio > edge_threshold and len(lines) > line_threshold
        return is_diagram
        
    except Exception as e:
        print(f"Diagram detection error: {str(e)}")
        return False

async def extract_diagram_text(image_path: str) -> str:
    """Extract text from diagrams using specialized OCR settings."""
    try:
        img = cv2.imread(image_path)
        config = '--psm 6 --oem 3 -c preserve_interword_spaces=1'
        text = pytesseract.image_to_string(img, config=config)
        return text.strip() or "No readable text found in diagram."
    except Exception as e:
        return f"Error extracting text from diagram: {str(e)}"