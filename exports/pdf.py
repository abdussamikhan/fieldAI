import io
import os
import html
import re
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

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

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor('#94a3b8'))
        # Footer
        self.drawString(36, 24, "FieldAI | Continuous Audit Analytics & Fieldwork Assistant")
        page_text = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(letter[0] - 36, 24, page_text)
        # Thin footer line
        self.setStrokeColor(colors.HexColor('#e2e8f0'))
        self.setLineWidth(0.5)
        self.line(36, 34, letter[0] - 36, 34)
        self.restoreState()

def _format_inline_markdown(text: str) -> str:
    text = html.escape(text.strip())
    text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
    text = re.sub(r'__(.*?)__', r'<b>\1</b>', text)
    text = re.sub(r'(?<!\w)\*(.*?)\*(?!\w)', r'<i>\1</i>', text)
    text = re.sub(r'`(.*?)`', r'<font name="Courier" color="#0284c7"><b>\1</b></font>', text)
    return text

def _parse_markdown_table(lines: list, font_name: str):
    raw_rows = []
    for line in lines:
        line_s = line.strip()
        if not line_s or not line_s.startswith("|"):
            continue
        cells = [c.strip() for c in line_s[1:-1].split("|")]
        if all(re.match(r'^:?-+:?$', c) for c in cells if c):
            continue
        raw_rows.append(cells)

    if not raw_rows:
        return None

    num_cols = max(len(r) for r in raw_rows)
    for r in raw_rows:
        while len(r) < num_cols:
            r.append("")

    total_width = 540
    if num_cols == 2:
        col_widths = [190, 350]
    elif num_cols == 3:
        col_widths = [140, 180, 220]
    elif num_cols == 4:
        col_widths = [110, 140, 140, 150]
    else:
        col_widths = [total_width / num_cols] * num_cols

    hdr_style = ParagraphStyle(
        'TblHdr',
        fontName=font_name,
        fontSize=8.5,
        leading=11,
        textColor=colors.white
    )
    cell_style = ParagraphStyle(
        'TblCell',
        fontName=font_name,
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor('#1e293b')
    )

    table_data = []
    for row_idx, r in enumerate(raw_rows):
        row_cells = []
        for c in r:
            formatted_text = _format_inline_markdown(c)
            if row_idx == 0:
                p = Paragraph(f"<b>{formatted_text}</b>", hdr_style)
            else:
                p = Paragraph(formatted_text, cell_style)
            row_cells.append(p)
        table_data.append(row_cells)

    t = Table(table_data, colWidths=col_widths)
    t_style = [
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e293b')),
        ('TOPPADDING', (0, 0), (-1, -1), 4.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4.5),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]
    for r_idx in range(1, len(table_data)):
        bg = colors.HexColor('#f8fafc') if r_idx % 2 == 1 else colors.white
        t_style.append(('BACKGROUND', (0, r_idx), (-1, r_idx), bg))

    t.setStyle(TableStyle(t_style))
    return t

def export_executive_audit_report_pdf(title: str, report_text: str, test_id: str = "") -> bytes:
    """Exports AI Executive Audit Findings Memo to a professionally styled ReportLab PDF."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=42)
    story = []

    doc_title = title.strip() if title and title.strip() else "Internal Audit Findings & Exception Report"
    
    # Title Banner with Accent
    title_table = Table([[
        Paragraph(f"<b>{html.escape(doc_title)}</b>", ParagraphStyle(
            'DocTitle',
            fontName=FONT_NAME,
            fontSize=15,
            leading=18,
            textColor=colors.HexColor('#0f172a')
        )),
        Paragraph(f"<font color='#0284c7'><b>FieldAI Analytics</b></font><br/><font color='#64748b' size='7.5'>{html.escape(test_id) if test_id else 'Continuous Assurance'}</font>", ParagraphStyle(
            'RightBadge',
            fontName=FONT_NAME,
            fontSize=9,
            leading=12,
            alignment=2
        ))
    ]], colWidths=[400, 140])
    title_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(title_table)
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#0284c7'), spaceBefore=2, spaceAfter=8))

    lines = report_text.splitlines() if report_text else []
    i = 0
    in_meta = True
    meta_rows = []

    h1_style = ParagraphStyle(
        'H1Sec',
        fontName=FONT_NAME,
        fontSize=12,
        leading=16,
        textColor=colors.HexColor('#0284c7'),
        spaceBefore=12,
        spaceAfter=5
    )
    h2_style = ParagraphStyle(
        'H2Sub',
        fontName=FONT_NAME,
        fontSize=10,
        leading=13.5,
        textColor=colors.HexColor('#0f172a'),
        spaceBefore=8,
        spaceAfter=4,
        keepWithNext=True
    )
    body_style = ParagraphStyle(
        'BodyTxt',
        fontName=FONT_NAME,
        fontSize=9,
        leading=13.5,
        textColor=colors.HexColor('#1e293b'),
        spaceAfter=5
    )
    bullet_style = ParagraphStyle(
        'BulletTxt',
        fontName=FONT_NAME,
        fontSize=9,
        leading=13.5,
        textColor=colors.HexColor('#1e293b'),
        leftIndent=14,
        spaceAfter=3.5
    )
    meta_key_style = ParagraphStyle(
        'MetaKey',
        fontName=FONT_NAME,
        fontSize=8.5,
        leading=11.5,
        textColor=colors.HexColor('#475569')
    )
    meta_val_style = ParagraphStyle(
        'MetaVal',
        fontName=FONT_NAME,
        fontSize=8.5,
        leading=11.5,
        textColor=colors.HexColor('#0f172a')
    )

    def flush_meta():
        nonlocal meta_rows, in_meta
        if meta_rows:
            t_meta = Table(meta_rows, colWidths=[160, 380])
            t_meta.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8fafc')),
                ('LINELEFT', (0, 0), (0, -1), 3.5, colors.HexColor('#38bdf8')),
                ('TOPPADDING', (0, 0), (-1, -1), 3),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
                ('LEFTPADDING', (0, 0), (-1, -1), 8),
                ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ]))
            story.append(t_meta)
            story.append(Spacer(1, 8))
            meta_rows = []
        in_meta = False

    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue

        # Skip duplicate doc title if repeated in the text
        if line.lower() in ("internal audit findings & exception report", "# internal audit findings & exception report", doc_title.lower()):
            i += 1
            continue

        # Collect metadata block before first table/section
        if in_meta and ":" in line and not line.startswith("|") and not line.startswith(("-", "*", "#")) and not re.match(r'^\d+\.', line):
            parts = line.split(":", 1)
            k = parts[0].strip()
            v = parts[1].strip()
            if "[insert date]" in v.lower():
                v = datetime.now().strftime("%B %d, %Y")
            
            if "risk rating" in k.lower():
                rating_color = "#ef4444" if "high" in v.lower() else ("#f59e0b" if "med" in v.lower() else "#0284c7")
                val_p = Paragraph(f"<font color='{rating_color}'><b>{html.escape(v.upper())}</b></font>", meta_val_style)
            else:
                val_p = Paragraph(_format_inline_markdown(v), meta_val_style)
            key_p = Paragraph(f"<b>{html.escape(k)}:</b>", meta_key_style)
            meta_rows.append([key_p, val_p])
            i += 1
            continue

        # Flush metadata card when leaving metadata section
        if in_meta and (line.startswith("|") or line.startswith("#") or line.startswith("---") or re.match(r'^\d+\.', line)):
            flush_meta()

        # Table block detection
        if line.startswith("|"):
            tbl_lines = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                tbl_lines.append(lines[i].strip())
                i += 1
            tbl = _parse_markdown_table(tbl_lines, FONT_NAME)
            if tbl:
                story.append(tbl)
                story.append(Spacer(1, 7))
            continue

        # Divider detection
        if re.match(r'^(---|\*\*\*|___)$', line):
            story.append(HRFlowable(width="100%", thickness=0.8, color=colors.HexColor('#cbd5e1'), spaceBefore=6, spaceAfter=6))
            i += 1
            continue

        # Section Headings (Numbered or markdown #/##/###)
        sec_num_match = re.match(r'^(\d+\.\s+.*)$', line)
        h_md_match = re.match(r'^(#{1,3})\s+(.*)$', line)

        if sec_num_match and ("Executive Summary" in line or "Root Cause" in line or "Business Risk" in line or "Recommendations" in line or len(line) < 60):
            heading_text = _format_inline_markdown(sec_num_match.group(1))
            t_sec = Table([[
                Paragraph(f"<b>{heading_text}</b>", ParagraphStyle('SecWhite', fontName=FONT_NAME, fontSize=10.5, leading=13, textColor=colors.white))
            ]], colWidths=[540])
            t_sec.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#1e293b')),
                ('LINELEFT', (0, 0), (0, 0), 4, colors.HexColor('#0284c7')),
                ('TOPPADDING', (0, 0), (-1, -1), 5),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
                ('LEFTPADDING', (0, 0), (-1, -1), 8),
                ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ]))
            story.append(Spacer(1, 6))
            story.append(t_sec)
            story.append(Spacer(1, 6))
            i += 1
            continue

        if h_md_match:
            level = len(h_md_match.group(1))
            heading_text = _format_inline_markdown(h_md_match.group(2))
            if level <= 2:
                story.append(Paragraph(f"<b>{heading_text}</b>", h1_style))
            else:
                story.append(Paragraph(f"<b>{heading_text}</b>", h2_style))
            i += 1
            continue

        # Subheading detection (e.g. "Root Cause Indicators", "Behavioral Pattern Analysis")
        if not line.startswith(("-", "*", "1.", "2.", "3.", "4.", "5.")) and len(line) < 45 and not line.endswith(".") and ":" not in line:
            story.append(Paragraph(f"<b>{_format_inline_markdown(line)}</b>", h2_style))
            i += 1
            continue

        # Bullets
        if line.startswith(("- ", "* ")):
            clean_b = _format_inline_markdown(line[2:])
            story.append(Paragraph(f"&bull; {clean_b}", bullet_style))
            i += 1
            continue

        # Numbered list items
        num_item_match = re.match(r'^(\d+\.)\s+(.*)$', line)
        if num_item_match:
            clean_n = _format_inline_markdown(num_item_match.group(2))
            story.append(Paragraph(f"<b>{num_item_match.group(1)}</b> {clean_n}", bullet_style))
            i += 1
            continue

        # Standard paragraph
        story.append(Paragraph(_format_inline_markdown(line), body_style))
        i += 1

    flush_meta()
    doc.build(story, canvasmaker=NumberedCanvas)
    return buffer.getvalue()
