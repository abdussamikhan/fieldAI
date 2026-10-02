import io
from typing import List, Dict, Any
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

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

    # Title
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontSize=18,
        leading=22,
        textColor=colors.HexColor('#0f172a'),
        spaceAfter=12
    )
    story.append(Paragraph(f"FieldAI Process Fieldwork Deliverable: {process_name} ({version})", title_style))
    story.append(Spacer(1, 10))

    # Section 1: Process Steps
    h2_style = ParagraphStyle('H2', parent=styles['Heading2'], fontSize=13, textColor=colors.HexColor('#0284c7'))
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
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
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
