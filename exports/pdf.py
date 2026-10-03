import io
import os
from pathlib import Path
from typing import List, Dict, Any
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# Register Inter font if TTF asset exists
FONT_NAME = "Helvetica"
font_path = Path(__file__).resolve().parent.parent / "assets" / "fonts" / "Inter-Regular.ttf"
if font_path.exists():
    try:
        pdfmetrics.registerFont(TTFont("Inter", str(font_path)))
        FONT_NAME = "Inter"
    except Exception as e:
        print(f"[PDF] Could not register Inter font: {e}")

def export_process_summary_pdf(
    process_name: str,
    version: str,
    steps: List[Dict[str, Any]],
    risks: List[Dict[str, Any]],
    controls: List[Dict[str, Any]]
) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    story = []
    styles = getSampleStyleSheet()

    # Title with Inter font, non-bold
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName=FONT_NAME,
        fontSize=16,
        leading=20,
        textColor=colors.HexColor('#0f172a'),
        spaceAfter=12
    )
    story.append(Paragraph(f"FieldAI Process Fieldwork Deliverable: {process_name} ({version})", title_style))
    story.append(Spacer(1, 10))

    # Section 1: Process Steps
    h2_style = ParagraphStyle(
        'H2',
        parent=styles['Heading2'],
        fontName=FONT_NAME,
        fontSize=12,
        leading=16,
        textColor=colors.HexColor('#0284c7')
    )
    story.append(Paragraph("1. Process Steps & Responsibility Flow", h2_style))
    story.append(Spacer(1, 6))

    step_data = [["Code", "Step Description", "Role", "System"]]
    for s in steps:
        step_data.append([
            s.get("step_code", ""),
            s.get("description", "")[:65] + ("..." if len(s.get("description", "")) > 65 else ""),
            s.get("responsible_role", "")[:20],
            s.get("system", "")[:15]
        ])

    table_style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e293b')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, -1), FONT_NAME),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ])
    t_steps = Table(step_data, colWidths=[60, 260, 110, 110])
    t_steps.setStyle(table_style)
    story.append(t_steps)
    story.append(Spacer(1, 16))

    # Section 2: Risks & Controls
    story.append(Paragraph("2. Identified Inherent Risks and Key Controls", h2_style))
    story.append(Spacer(1, 6))

    rc_data = [["Risk", "Risk Description", "Control", "Control Description", "Design Rating"]]
    ctrl_dict = {c.get("control_code"): c for c in controls}
    
    for r in risks:
        c_code = r.get("control_codes", [""])[0] if r.get("control_codes") else ""
        ctrl = ctrl_dict.get(c_code, {})
        rc_data.append([
            r.get("risk_code", ""),
            r.get("description", "")[:45] + "...",
            c_code,
            ctrl.get("description", "Unmitigated / Gap")[:45] + "...",
            ctrl.get("design_rating", "Inadequate" if not c_code else "Adequate")
        ])

    t_rc = Table(rc_data, colWidths=[45, 170, 45, 200, 80])
    t_rc.setStyle(table_style)
    story.append(t_rc)

    doc.build(story)
    return buffer.getvalue()

def export_findings_pdf(findings: List[Dict[str, Any]], process_name: str = "") -> bytes:
    """Exports structured 5 Cs audit findings to a styled ReportLab PDF."""
    import html
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    story = []
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'FindingsTitle',
        parent=styles['Heading1'],
        fontName=FONT_NAME,
        fontSize=16,
        leading=20,
        textColor=colors.HexColor('#0f172a'),
        spaceAfter=4
    )
    subtitle_style = ParagraphStyle(
        'FindingsSubTitle',
        parent=styles['Normal'],
        fontName=FONT_NAME,
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#64748b'),
        spaceAfter=14
    )
    field_label_style = ParagraphStyle(
        'FieldLabel',
        parent=styles['Heading3'],
        fontName=FONT_NAME,
        fontSize=10,
        leading=13,
        textColor=colors.HexColor('#0284c7'),
        spaceBefore=6,
        spaceAfter=2
    )
    body_style = ParagraphStyle(
        'BodyDark',
        parent=styles['Normal'],
        fontName=FONT_NAME,
        fontSize=9,
        leading=13,
        textColor=colors.HexColor('#1e293b'),
        spaceAfter=4
    )

    story.append(Paragraph("FieldAI Internal Audit Fieldwork Findings (5 Cs)", title_style))
    proc_str = f"Process: {html.escape(process_name)} &bull; " if process_name else ""
    story.append(Paragraph(f"{proc_str}Total Findings: {len(findings)}", subtitle_style))
    story.append(Spacer(1, 8))

    for idx, f in enumerate(findings, 1):
        f_code = html.escape(str(f.get("finding_code") or f"FIND-{idx:02d}"))
        f_title = html.escape(str(f.get("title") or "Untitled Finding"))
        rating = str(f.get("rating") or "Medium").capitalize()
        status = str(f.get("status") or "draft").upper()

        badge_color = colors.HexColor('#ef4444') if rating.lower() == "high" else (
            colors.HexColor('#f59e0b') if rating.lower() == "medium" else colors.HexColor('#0284c7')
        )
        
        head_table_data = [[
            Paragraph(f"<b>Finding {idx}: {f_code} &ndash; {f_title}</b>", ParagraphStyle('HeadWhite', fontName=FONT_NAME, fontSize=11, leading=14, textColor=colors.white)),
            Paragraph(f"<b>{rating.upper()}</b> | {status}", ParagraphStyle('RatingWhite', fontName=FONT_NAME, fontSize=9, leading=12, alignment=2, textColor=colors.white))
        ]]
        t_head = Table(head_table_data, colWidths=[410, 130])
        t_head.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#1e293b')),
            ('LINELEFT', (0, 0), (0, 0), 4, badge_color),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ]))
        story.append(t_head)
        story.append(Spacer(1, 6))

        for heading_label, text_key in [
            ("Condition (What was found):", "condition_text"),
            ("Criteria (What should be / Policy):", "criteria_text"),
            ("Cause (Root Cause):", "cause_text"),
            ("Effect (Risk or Business Impact):", "effect_text"),
            ("Recommendation (Remediation Action):", "recommendation_text")
        ]:
            val = f.get(text_key) or f.get(text_key.replace("_text", ""), "")
            if val:
                clean_val = html.escape(str(val)).replace("\n", "<br/>")
                story.append(Paragraph(heading_label, field_label_style))
                story.append(Paragraph(clean_val, body_style))

        linked_ctrl = f.get("linked_controls") or "-"
        linked_tst = f.get("linked_tests") or "-"
        story.append(Paragraph(
            f"<font color='#64748b'>Linked Controls: {html.escape(str(linked_ctrl))} | Linked Tests: {html.escape(str(linked_tst))}</font>",
            ParagraphStyle('SubMuted', fontName=FONT_NAME, fontSize=8, leading=10, textColor=colors.HexColor('#64748b'), spaceBefore=4, spaceAfter=10)
        ))
        story.append(Spacer(1, 10))

    doc.build(story)
    return buffer.getvalue()

def export_executive_audit_report_pdf(title: str, report_text: str, test_id: str = "") -> bytes:
    """Exports AI Executive Audit Findings Memo to a styled ReportLab PDF."""
    import html
    import re
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    story = []
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'ExecTitle',
        parent=styles['Heading1'],
        fontName=FONT_NAME,
        fontSize=16,
        leading=20,
        textColor=colors.HexColor('#0f172a'),
        spaceAfter=4
    )
    subtitle_style = ParagraphStyle(
        'ExecSubTitle',
        parent=styles['Normal'],
        fontName=FONT_NAME,
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#64748b'),
        spaceAfter=14
    )
    h1_style = ParagraphStyle(
        'ReportH1',
        parent=styles['Heading2'],
        fontName=FONT_NAME,
        fontSize=12,
        leading=16,
        textColor=colors.HexColor('#0284c7'),
        spaceBefore=10,
        spaceAfter=4
    )
    h2_style = ParagraphStyle(
        'ReportH2',
        parent=styles['Heading3'],
        fontName=FONT_NAME,
        fontSize=11,
        leading=15,
        textColor=colors.HexColor('#0f172a'),
        spaceBefore=8,
        spaceAfter=3
    )
    body_style = ParagraphStyle(
        'ReportBody',
        parent=styles['Normal'],
        fontName=FONT_NAME,
        fontSize=9.5,
        leading=14,
        textColor=colors.HexColor('#1e293b'),
        spaceAfter=5
    )
    bullet_style = ParagraphStyle(
        'ReportBullet',
        parent=styles['Normal'],
        fontName=FONT_NAME,
        fontSize=9.5,
        leading=14,
        textColor=colors.HexColor('#1e293b'),
        leftIndent=15,
        spaceAfter=3
    )

    doc_title = title if title else "FieldAI Executive Audit Report"
    story.append(Paragraph(html.escape(doc_title), title_style))
    id_str = f"Test ID: {html.escape(test_id)} &bull; " if test_id else ""
    story.append(Paragraph(f"{id_str}Generated by FieldAI Multi-Agent Analytics", subtitle_style))
    story.append(Spacer(1, 8))

    for line in report_text.splitlines():
        line_s = line.strip()
        if not line_s:
            story.append(Spacer(1, 4))
            continue
        
        if line_s.startswith("### "):
            header_text = html.escape(line_s[4:])
            story.append(Paragraph(header_text, h2_style))
        elif line_s.startswith("## "):
            header_text = html.escape(line_s[3:])
            story.append(Paragraph(header_text, h1_style))
        elif line_s.startswith("# "):
            header_text = html.escape(line_s[2:])
            story.append(Paragraph(header_text, h1_style))
        elif line_s.startswith("- ") or line_s.startswith("* "):
            bullet_text = html.escape(line_s[2:])
            bullet_text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', bullet_text)
            story.append(Paragraph(f"&bull; {bullet_text}", bullet_style))
        elif re.match(r'^\d+\.\s+', line_s):
            num_text = html.escape(line_s)
            num_text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', num_text)
            story.append(Paragraph(num_text, bullet_style))
        else:
            p_text = html.escape(line_s)
            p_text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', p_text)
            story.append(Paragraph(p_text, body_style))

    doc.build(story)
    return buffer.getvalue()
