import os
import pytest
from docx import Document
from services.docx_service import extract_docx_content, inspect_docx_content
from utils.file import allowed_file, is_docx, ALLOWED_EXTENSIONS

def test_file_extensions():
    assert allowed_file("document.docx")
    assert allowed_file("syllabus.doc")
    assert allowed_file("notes.txt")
    assert is_docx("document.docx")
    assert is_docx("test.DOCX")
    assert not is_docx("diagram.png")
    assert not is_docx("slides.pptx")

def test_extract_and_inspect_docx(tmp_path):
    doc_path = str(tmp_path / "sample.docx")
    doc = Document()
    doc.add_heading("Quantum Mechanics Overview", level=1)
    doc.add_paragraph("The wave function represents the quantum state of a system.")
    doc.add_heading("Schrodinger Equation", level=2)
    doc.add_paragraph("The time-dependent Schrodinger equation describes how quantum state changes over time.")

    # Add table
    table = doc.add_table(rows=1, cols=2)
    hdr = table.rows[0].cells
    hdr[0].text = "Variable"
    hdr[1].text = "Description"
    row = table.add_row().cells
    row[0].text = "Psi"
    row[1].text = "Wave function"

    doc.save(doc_path)

    # 1. Extraction test
    content = extract_docx_content(doc_path)
    assert "Quantum Mechanics Overview" in content["text"]
    assert "Schrodinger Equation" in content["text"]
    assert "Wave function" in content["text"]
    assert content["total_pages"] >= 1
    assert len(content["headings"]) == 2

    # 2. Inspection test
    inspection = inspect_docx_content(doc_path)
    assert inspection["total_pages"] >= 1
    assert len(inspection["chapters"]) == 2
    assert inspection["chapters"][0]["title"] == "Quantum Mechanics Overview"
    assert inspection["chapters"][1]["title"] == "Schrodinger Equation"

def test_extract_plain_text(tmp_path):
    txt_path = str(tmp_path / "notes.txt")
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write("Line 1: Photosynthesis notes.\nLine 2: Chloroplast structure.")

    content = extract_docx_content(txt_path)
    assert "Photosynthesis notes" in content["text"]
    assert content["total_pages"] == 1

    inspection = inspect_docx_content(txt_path)
    assert inspection["total_pages"] == 1
    assert len(inspection["chapters"]) >= 1
