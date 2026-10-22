import os
import re
import logging
from typing import Optional, Dict, Any, List
from docx import Document
from services.pdf_service import parse_page_range

logger = logging.getLogger(__name__)

WORDS_PER_PAGE_ESTIMATE = 300

def _extract_plain_text(file_path: str) -> str:
    """Read a plain text or fallback document with encoding detection."""
    encodings = ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252']
    for enc in encodings:
        try:
            with open(file_path, 'r', encoding=enc) as f:
                return f.read()
        except UnicodeDecodeError:
            continue
    # Fallback with error replacement
    with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
        return f.read()

def _extract_legacy_doc_strings(file_path: str) -> str:
    """Extract readable text strings from legacy binary .doc files."""
    try:
        # First attempt: maybe it's a docx with .doc extension
        doc = Document(file_path)
        return _extract_from_docx_object(doc)["text"]
    except Exception:
        pass

    try:
        with open(file_path, 'rb') as f:
            content = f.read()
        # Find printable ASCII and unicode strings >= 4 chars
        words = re.findall(b'[\x20-\x7E\t\r\n]{4,}', content)
        decoded = [w.decode('latin-1', errors='ignore').strip() for w in words]
        return "\n".join([line for line in decoded if line and len(line) > 3])
    except Exception as e:
        logger.warning(f"Failed to extract strings from legacy .doc file {file_path}: {e}")
        return ""

def _extract_from_docx_object(doc: Document) -> Dict[str, Any]:
    """Extract paragraphs and tables from a python-docx Document instance."""
    blocks: List[str] = []
    headings: List[Dict[str, Any]] = []
    
    # Process paragraphs
    for p in doc.paragraphs:
        text = p.text.strip()
        if not text:
            continue
        
        style_name = (p.style.name if p.style else "").lower()
        if "heading" in style_name or "title" in style_name:
            level = 1
            match = re.search(r'\d+', style_name)
            if match:
                level = min(int(match.group()), 3)
            headings.append({
                "title": text,
                "level": level
            })
            blocks.append(f"\n## {text}\n")
        else:
            blocks.append(text)

    # Process tables
    for table_idx, table in enumerate(doc.tables):
        table_lines = []
        for row in table.rows:
            cells = [cell.text.strip().replace("\n", " ") for cell in row.cells]
            # Deduplicate contiguous duplicate cells (often from merged cells)
            dedup_cells = []
            for c in cells:
                if not dedup_cells or dedup_cells[-1] != c:
                    dedup_cells.append(c)
            if any(dedup_cells):
                table_lines.append(" | ".join(dedup_cells))
        if table_lines:
            blocks.append(f"\n[Table {table_idx + 1}]\n" + "\n".join(table_lines) + "\n")

    full_text = "\n\n".join(blocks).strip()
    return {
        "text": full_text,
        "headings": headings
    }

def extract_docx_content(file_path: str, page_range: Optional[str] = None) -> Dict[str, Any]:
    """
    Extract text content from Microsoft Word (.docx, .doc) or text (.txt) files.
    Supports logical page filtering based on estimated page length (300 words/page).
    """
    ext = os.path.splitext(file_path)[1].lower()

    if ext == '.txt':
        raw_text = _extract_plain_text(file_path).strip()
        headings = []
    elif ext == '.doc':
        raw_text = _extract_legacy_doc_strings(file_path).strip()
        headings = []
    else:
        try:
            doc = Document(file_path)
            extracted = _extract_from_docx_object(doc)
            raw_text = extracted["text"]
            headings = extracted["headings"]
        except Exception as e:
            logger.warning(f"python-docx parsing error on {file_path}, falling back to text read: {e}")
            raw_text = _extract_plain_text(file_path).strip()
            headings = []

    words = raw_text.split()
    total_words = len(words)
    total_estimated_pages = max(1, (total_words + WORDS_PER_PAGE_ESTIMATE - 1) // WORDS_PER_PAGE_ESTIMATE)

    # Apply page range filtering if provided
    if page_range and total_estimated_pages > 1:
        start_idx, end_idx = parse_page_range(page_range, total_estimated_pages)
        start_word = start_idx * WORDS_PER_PAGE_ESTIMATE
        end_word = min(end_idx * WORDS_PER_PAGE_ESTIMATE, total_words)
        filtered_words = words[start_word:end_word]
        selected_text = " ".join(filtered_words)
        processed_pages = end_idx - start_idx
        used_range = f"{start_idx + 1}-{end_idx}"
    else:
        selected_text = raw_text
        processed_pages = total_estimated_pages
        used_range = f"1-{total_estimated_pages}"

    return {
        "text": selected_text,
        "total_pages": total_estimated_pages,
        "processed_pages": processed_pages,
        "headings": headings,
        "page_range_used": used_range
    }

def inspect_docx_content(file_path: str) -> Dict[str, Any]:
    """
    Inspect a Word or text file and return total estimated page count and chapter/heading pills.
    Matches the schema expected by the frontend document TOC inspector.
    """
    try:
        extracted = extract_docx_content(file_path)
        total_pages = extracted.get("total_pages", 1)
        headings = extracted.get("headings", [])

        chapters = []
        if headings:
            # Distribute headings across estimated pages
            headings_count = len(headings)
            for idx, h in enumerate(headings):
                # Approximate start page for this heading
                approx_page = max(1, min(total_pages, int((idx / headings_count) * total_pages) + 1))
                chapters.append({
                    "title": h["title"][:50] + ("..." if len(h["title"]) > 50 else ""),
                    "level": h.get("level", 1),
                    "start_page": approx_page,
                    "end_page": approx_page,
                    "range": str(approx_page)
                })
        else:
            # If no formal headings, generate logical sections if document is multi-page
            if total_pages <= 3:
                for p in range(1, total_pages + 1):
                    chapters.append({
                        "title": f"Section {p}",
                        "level": 1,
                        "start_page": p,
                        "end_page": p,
                        "range": str(p)
                    })
            else:
                chunk_size = max(2, total_pages // 4)
                for start_p in range(1, total_pages + 1, chunk_size):
                    end_p = min(start_p + chunk_size - 1, total_pages)
                    chapters.append({
                        "title": f"Section (Pages {start_p}-{end_p})",
                        "level": 1,
                        "start_page": start_p,
                        "end_page": end_p,
                        "range": f"{start_p}-{end_p}"
                    })

        return {
            "total_pages": total_pages,
            "chapters": chapters
        }
    except Exception as e:
        logger.error(f"Error inspecting docx content for {file_path}: {e}")
        return {
            "total_pages": 1,
            "chapters": [],
            "error": str(e)
        }
