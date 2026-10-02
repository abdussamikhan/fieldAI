import io
from typing import List, Dict, Any
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH

def export_transcript_word(
    title: str,
    summary_data: Dict[str, Any],
    segments: List[Dict[str, Any]]
) -> bytes:
    doc = Document()
    
    # Title
    p_title = doc.add_paragraph()
    run_title = p_title.add_run(f"FieldAI Walkthrough Record: {title}")
    run_title.font.name = "Calibri"
    run_title.font.size = Pt(20)
    run_title.font.bold = True
    run_title.font.color.rgb = RGBColor(15, 23, 42)

    # Executive Summary Heading
    doc.add_heading("1. Executive Summary", level=1)
    doc.add_paragraph(summary_data.get("summary", "No summary recorded."))

    # Key Points
    if summary_data.get("key_points"):
        doc.add_heading("2. Key Discussion Points", level=2)
        for pt in summary_data["key_points"]:
            doc.add_paragraph(pt, style='List Bullet')

    # Open Questions
    if summary_data.get("open_questions"):
        doc.add_heading("3. Open Questions / Follow-ups", level=2)
        for q in summary_data["open_questions"]:
            doc.add_paragraph(q, style='List Bullet')

    # PBC Requests
    if summary_data.get("pbc_requests"):
        doc.add_heading("4. Provided By Client (PBC) Requests", level=2)
        pbc_table = doc.add_table(rows=1, cols=3)
        pbc_table.style = 'Light Shading Accent 1'
        hdr_cells = pbc_table.rows[0].cells
        hdr_cells[0].text = "Requested Item"
        hdr_cells[1].text = "Owner"
        hdr_cells[2].text = "Due Date Hint"
        
        for pbc in summary_data["pbc_requests"]:
            row_cells = pbc_table.add_row().cells
            row_cells[0].text = pbc.get("item", "")
            row_cells[1].text = pbc.get("owner", "")
            row_cells[2].text = pbc.get("due_hint", "")

    # Detailed Transcript
    doc.add_page_break()
    doc.add_heading("5. Detailed Meeting Transcript", level=1)

    for seg in segments:
        speaker = seg.get("speaker_name") or seg.get("speaker_label", "Speaker")
        start_min = int(seg.get("start_s", 0) // 60)
        start_sec = int(seg.get("start_s", 0) % 60)
        time_str = f"[{start_min:02d}:{start_sec:02d}]"

        p = doc.add_paragraph()
        run_speaker = p.add_run(f"{speaker} {time_str}: ")
        run_speaker.bold = True
        run_speaker.font.color.rgb = RGBColor(2, 132, 199)
        p.add_run(seg.get("text", ""))

    out = io.BytesIO()
    doc.save(out)
    return out.getvalue()

def export_findings_word(findings: List[Dict[str, Any]]) -> bytes:
    doc = Document()
    
    p_title = doc.add_paragraph()
    run_title = p_title.add_run("Internal Audit Fieldwork Findings (5 Cs)")
    run_title.font.name = "Calibri"
    run_title.font.size = Pt(20)
    run_title.font.bold = True

    for idx, f in enumerate(findings, 1):
        doc.add_heading(f"Finding {idx}: {f.get('finding_code', '')} – {f.get('title', '')}", level=1)
        
        p_rating = doc.add_paragraph()
        run_r = p_rating.add_run(f"Severity Rating: {f.get('rating', 'Medium')}")
        run_r.bold = True
        
        # 5 Cs
        doc.add_heading("Condition (What was found):", level=3)
        doc.add_paragraph(f.get("condition_text") or f.get("condition", ""))

        doc.add_heading("Criteria (What should be):", level=3)
        doc.add_paragraph(f.get("criteria_text") or f.get("criteria", ""))

        doc.add_heading("Cause (Why did it happen):", level=3)
        doc.add_paragraph(f.get("cause_text") or f.get("cause", ""))

        doc.add_heading("Effect (Risk or business impact):", level=3)
        doc.add_paragraph(f.get("effect_text") or f.get("effect", ""))

        doc.add_heading("Recommendation (Remediation action):", level=3)
        doc.add_paragraph(f.get("recommendation_text") or f.get("recommendation", ""))

        doc.add_paragraph(f"Linked Controls/Tests: {f.get('linked_controls', '')} / {f.get('linked_tests', '')}")
        doc.add_paragraph("-" * 40)

    out = io.BytesIO()
    doc.save(out)
    return out.getvalue()
