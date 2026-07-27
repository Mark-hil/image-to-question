import io
import zipfile
import xml.etree.ElementTree as ET
from typing import List, Dict, Any

from docx import Document
from docx.shared import Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH

class ExportService:
    """Service to export Question Banks into Canvas QTI 2.1 XML packages, MS Word .docx, and printable formats."""

    @staticmethod
    def generate_qti_xml(quiz_title: str, questions: List[Dict[str, Any]]) -> str:
        """Generate Canvas QTI 2.1 XML representation of questions."""
        root = ET.Element("questestinterop", {
            "xmlns": "http://www.imsglobal.org/xsd/ims_qtiasasi_v1p2",
            "xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance"
        })

        assessment = ET.SubElement(root, "assessment", {"ident": "quiz_1001", "title": quiz_title})
        section = ET.SubElement(assessment, "section", {"ident": "root_section"})

        for idx, q in enumerate(questions, 1):
            q_id = f"item_{idx}"
            item = ET.SubElement(section, "item", {"ident": q_id, "title": f"Question {idx}"})

            q_text = q.get("question_text") or q.get("question") or f"Question {idx}"
            a_text = q.get("answer_text") or q.get("answer") or ""
            q_type = q.get("qtype") or q.get("type") or "mcq"

            # Item Metadata
            itemmetadata = ET.SubElement(item, "itemmetadata")
            qtimetadata = ET.SubElement(itemmetadata, "qtimetadata")

            def add_meta(field, val):
                field_node = ET.SubElement(qtimetadata, "qtimetadatafield")
                ET.SubElement(field_node, "fieldlabel").text = field
                ET.SubElement(field_node, "fieldentry").text = str(val)

            if q_type == "mcq":
                qtype_str = "multiple_choice_question"
            elif q_type == "true_false":
                qtype_str = "true_false_question"
            else:
                qtype_str = "short_answer_question"

            add_meta("question_type", qtype_str)
            add_meta("points_possible", "1.0")

            # Presentation / Question Stem
            presentation = ET.SubElement(item, "presentation")
            material = ET.SubElement(presentation, "material")
            mattext = ET.SubElement(material, "mattext", {"texttype": "text/html"})
            mattext.text = q_text

            # Choices / Response Lid
            choices = q.get("choices") or []
            if q_type == "true_false" and not choices:
                choices = ["True", "False"]

            if choices and q_type in ["mcq", "true_false"]:
                response_lid = ET.SubElement(presentation, "response_lid", {"ident": "response1", "rcardinality": "Single"})
                render_choice = ET.SubElement(response_lid, "render_choice")
                for c_idx, choice_text in enumerate(choices):
                    c_id = f"choice_{c_idx}"
                    response_label = ET.SubElement(render_choice, "response_label", {"ident": c_id})
                    mat_node = ET.SubElement(response_label, "material")
                    ET.SubElement(mat_node, "mattext", {"texttype": "text/plain"}).text = str(choice_text)

        xml_str = ET.tostring(root, encoding="utf-8").decode("utf-8")
        return f'<?xml version="1.0" encoding="UTF-8"?>\n{xml_str}'

    @classmethod
    def generate_canvas_qti_zip(cls, quiz_title: str, questions: List[Dict[str, Any]]) -> bytes:
        """Create a zip archive containing IMS manifest and QTI XML for Canvas LMS import."""
        qti_xml = cls.generate_qti_xml(quiz_title, questions)
        manifest_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<manifest identifier="qti_manifest_{quiz_title.replace(' ', '_')}" xmlns="http://www.imsglobal.org/xsd/imscp_v1p1p3">
  <resources>
    <resource identifier="resource_qti" type="imsqti_xmlv1p2">
      <file href="qti.xml"/>
    </resource>
  </resources>
</manifest>
"""
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("qti.xml", qti_xml.encode("utf-8"))
            zf.writestr("imsmanifest.xml", manifest_xml.encode("utf-8"))

        buffer.seek(0)
        return buffer.getvalue()

    @staticmethod
    def generate_printable_text(quiz_title: str, questions: List[Dict[str, Any]]) -> str:
        """Format quiz questions cleanly as plain text for printing."""
        output = [f"=========================================="]
        output.append(f"  {quiz_title.upper()}")
        output.append(f"==========================================\n")

        for idx, q in enumerate(questions, 1):
            q_text = q.get("question_text") or q.get("question") or f"Question {idx}"
            output.append(f"{idx}. {q_text}")
            choices = q.get("choices")
            q_type = q.get("qtype") or q.get("type") or "mcq"
            if q_type == "true_false" and not choices:
                choices = ["True", "False"]

            if choices:
                letters = ["A", "B", "C", "D", "E"]
                for c_idx, c in enumerate(choices):
                    label = letters[c_idx] if c_idx < len(letters) else f"({c_idx+1})"
                    output.append(f"   [{label}] {c}")
            output.append("")

        output.append("\n------------------------------------------")
        output.append("             ANSWER KEY                   ")
        output.append("------------------------------------------\n")
        for idx, q in enumerate(questions, 1):
            a_text = q.get("answer_text") or q.get("answer") or ""
            rationale = q.get("rationale") or ""
            output.append(f"{idx}. Answer: {a_text}")
            if rationale:
                output.append(f"   Explanation: {rationale}")
            output.append("")

        return "\n".join(output)

    @staticmethod
    def generate_docx(quiz_title: str, questions: List[Dict[str, Any]]) -> bytes:
        """Generate Microsoft Word document (.docx) with question bank and answer key."""
        doc = Document()

        # Quiz Title
        title_p = doc.add_paragraph()
        title_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = title_p.add_run(quiz_title.upper())
        run.bold = True
        run.font.size = Pt(18)
        run.font.color.rgb = RGBColor(79, 70, 229)  # Indigo

        doc.add_paragraph()  # Spacing

        # Questions Section
        for idx, q in enumerate(questions, 1):
            q_text = q.get("question_text") or q.get("question") or f"Question {idx}"
            p = doc.add_paragraph()
            q_run = p.add_run(f"{idx}. {q_text}")
            q_run.bold = True
            q_run.font.size = Pt(12)

            choices = q.get("choices") or []
            q_type = q.get("qtype") or q.get("type") or "mcq"
            if q_type == "true_false" and not choices:
                choices = ["True", "False"]

            if choices:
                letters = ["A", "B", "C", "D", "E"]
                for c_idx, c in enumerate(choices):
                    label = letters[c_idx] if c_idx < len(letters) else f"({c_idx+1})"
                    cp = doc.add_paragraph()
                    cp.paragraph_format.left_indent = Pt(18)
                    c_run = cp.add_run(f"[{label}] {c}")
                    c_run.font.size = Pt(11)

            doc.add_paragraph()  # Spacing

        # Answer Key Page Break
        doc.add_page_break()
        ak_title = doc.add_paragraph()
        ak_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
        ak_run = ak_title.add_run("ANSWER KEY & EXPLANATIONS")
        ak_run.bold = True
        ak_run.font.size = Pt(16)
        ak_run.font.color.rgb = RGBColor(16, 185, 129)  # Emerald

        doc.add_paragraph()

        for idx, q in enumerate(questions, 1):
            a_text = q.get("answer_text") or q.get("answer") or ""
            rationale = q.get("rationale") or ""

            ap = doc.add_paragraph()
            arun = ap.add_run(f"{idx}. Correct Answer: {a_text}")
            arun.bold = True
            arun.font.size = Pt(11)

            if rationale:
                rp = doc.add_paragraph()
                rp.paragraph_format.left_indent = Pt(18)
                rrun = rp.add_run(f"Explanation: {rationale}")
                rrun.italic = True
                rrun.font.size = Pt(10)
                rrun.font.color.rgb = RGBColor(100, 116, 139)

            doc.add_paragraph()

        buffer = io.BytesIO()
        doc.save(buffer)
        buffer.seek(0)
        return buffer.getvalue()
