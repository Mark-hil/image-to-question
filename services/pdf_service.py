import fitz  # PyMuPDF
from pdf2image import convert_from_path
import os
import re
from typing import List, Tuple, Optional
from pathlib import Path

def parse_page_range(page_range_str: str, total_pages: int) -> Tuple[int, int]:
    """
    Parses page range strings like '8-20', '5', '10-', '-15' into 0-indexed start and end indices.
    Returns (start_idx, end_idx) where end_idx is exclusive for slicing.
    """
    if not page_range_str or not str(page_range_str).strip():
        return 0, total_pages
    
    clean_str = str(page_range_str).strip().replace(' ', '')
    try:
        if '-' in clean_str:
            parts = clean_str.split('-')
            start = int(parts[0]) - 1 if parts[0] else 0
            end = int(parts[1]) if parts[1] else total_pages
        else:
            p = int(clean_str)
            start = p - 1
            end = p
        
        start_idx = max(0, min(start, total_pages - 1))
        end_idx = max(start_idx + 1, min(end, total_pages))
        return start_idx, end_idx
    except Exception:
        return 0, total_pages

def extract_pdf_toc(pdf_path: str) -> dict:
    """
    Extract Table of Contents (chapters and page ranges) from a PDF document.
    Uses PDF metadata TOC bookmarks, with an intelligent text-heading regex scanner fallback.
    """
    try:
        with fitz.open(pdf_path) as doc:
            total_pages = len(doc)
            raw_toc = doc.get_toc()
        
            chapters = []
            if raw_toc:
                for i, item in enumerate(raw_toc):
                    level, title, page = item[0], item[1], item[2]
                    start_p = max(1, min(page, total_pages))
                    
                    # Determine end page based on next chapter start or total pages
                    if i < len(raw_toc) - 1:
                        next_page = raw_toc[i+1][2]
                        end_p = max(start_p, min(next_page - 1, total_pages))
                    else:
                        end_p = total_pages
                    
                    chapters.append({
                        "title": title.strip(),
                        "level": level,
                        "start_page": start_p,
                        "end_page": end_p,
                        "range": f"{start_p}-{end_p}" if start_p != end_p else f"{start_p}"
                    })

            # Fallback: Intelligent text-heading regex scanner if PDF metadata TOC is empty
            if not chapters and total_pages > 0:
                detected_headings = []
                seen_titles = set()
                for p in range(total_pages):
                    text = doc[p].get_text("text")
                    lines = [line.strip() for line in text.split("\n") if line.strip()][:6]
                    for line in lines:
                        # Match headings like 'Chapter 1', 'Unit 2', 'Section 3', 'Lesson 4', 'Part 5', 'Module 6'
                        match = re.search(r'(?i)^(chapter|unit|section|lesson|part|module)\s+(\d+|[ivx]+)[:\.\s]\s*(.*)', line)
                        if match:
                            title_clean = line.strip()
                            title_key = title_clean.upper()
                            if title_key not in seen_titles:
                                seen_titles.add(title_key)
                                detected_headings.append({
                                    "title": title_clean,
                                    "start_page": p + 1
                                })
                            break

                for i, item in enumerate(detected_headings):
                    start_p = item["start_page"]
                    if i < len(detected_headings) - 1:
                        next_start = detected_headings[i+1]["start_page"]
                        end_p = max(start_p, min(next_start - 1, total_pages))
                    else:
                        end_p = total_pages

                    chapters.append({
                        "title": item["title"],
                        "level": 1,
                        "start_page": start_p,
                        "end_page": end_p,
                        "range": f"{start_p}-{end_p}" if start_p != end_p else f"{start_p}"
                    })
        
        return {
            "total_pages": total_pages,
            "chapters": chapters
        }
    except Exception as e:
        return {
            "total_pages": 0,
            "chapters": [],
            "error": str(e)
        }

class PDFService:
    @staticmethod
    async def pdf_to_images(pdf_path: str, output_dir: str = "temp_images", page_range: Optional[str] = None) -> List[str]:
        """Convert PDF pages to images within range and return list of image paths"""
        os.makedirs(output_dir, exist_ok=True)
        
        with fitz.open(pdf_path) as doc:
            total_pages = len(doc)
        
        start_idx, end_idx = parse_page_range(page_range or "", total_pages)
        # convert_from_path uses 1-based indexing for first_page and last_page
        images = convert_from_path(pdf_path, first_page=start_idx+1, last_page=end_idx)
        image_paths = []
        
        for i, image in enumerate(images):
            page_num = start_idx + i + 1
            image_path = os.path.join(output_dir, f"page_{page_num}.jpg")
            image.save(image_path, "JPEG")
            image_paths.append(image_path)
            
        return image_paths

    @staticmethod
    def extract_text_from_pdf(pdf_path: str, page_range: Optional[str] = None) -> str:
        """Extract text directly from PDF within optional page range"""
        text = ""
        with fitz.open(pdf_path) as doc:
            total_pages = len(doc)
            start_idx, end_idx = parse_page_range(page_range or "", total_pages)
            for page_num in range(start_idx, end_idx):
                text += doc[page_num].get_text() + "\n\n"
        return text