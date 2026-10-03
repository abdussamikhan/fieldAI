"""
FieldAI Comprehensive BRD + PRD PDF Generator
Generates a complete, publication-grade dual Business Requirements Document (BRD)
and Product Requirements Document (PRD) detailing the business objectives, functional
specifications, 15 application modules, and the configuration and flow of the
21-agent multi-agent architecture (LangGraph StateGraph).
"""

import os
import sys
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# Font configuration
FONT_NAME = "Helvetica"
font_path = Path(__file__).resolve().parent.parent / "assets" / "fonts" / "Inter-Regular.ttf"
if font_path.exists():
    try:
        pdfmetrics.registerFont(TTFont("Inter", str(font_path)))
        FONT_NAME = "Inter"
    except Exception as e:
        print(f"[PDF] Font registration error: {e}")

class NumberedCanvas(canvas.Canvas):
    """
    Two-pass canvas to compute total page count and draw running header and footer.
    """
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
            self.draw_header_footer(num_pages)
            super().showPage()
        super().save()

    def draw_header_footer(self, page_count):
        if self._pageNumber > 1:
            self.saveState()
            self.setFont(FONT_NAME, 7.5)
            self.setFillColor(colors.HexColor("#64748b"))
            
            # Running Header
            self.drawString(36, 756, "FieldAI - Combined BRD & PRD | Enterprise Multi-Agent Audit Fieldwork & Process Intelligence")
            self.setStrokeColor(colors.HexColor("#e2e8f0"))
            self.setLineWidth(0.5)
            self.line(36, 750, 576, 750)
            
            # Running Footer
            self.line(36, 42, 576, 42)
            self.drawString(36, 32, "Confidential | Internal Audit Technology | ACCELERAT | Production Architecture Baseline v1.0")
            page_text = f"Page {self._pageNumber} of {page_count}"
            self.drawRightString(576, 32, page_text)
            self.restoreState()

def generate_brd_prd_pdf(output_path: str):
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=46,
        bottomMargin=46
    )
    
    styles = getSampleStyleSheet()
    
    # Palette definition
    c_primary = colors.HexColor("#0f172a")     # Slate 900
    c_accent = colors.HexColor("#0284c7")      # Sky 600
    c_secondary = colors.HexColor("#334155")   # Slate 700
    c_muted = colors.HexColor("#64748b")       # Slate 500
    c_border = colors.HexColor("#cbd5e1")      # Slate 300
    c_table_bg = colors.HexColor("#f8fafc")    # Slate 50
    c_header_bg = colors.HexColor("#1e293b")   # Slate 800
    c_pill_bg = colors.HexColor("#e0f2fe")     # Sky 100
    
    style_cover_title = ParagraphStyle(
        'CoverTitle',
        parent=styles['Normal'],
        fontName=FONT_NAME,
        fontSize=18,
        leading=22,
        textColor=c_primary,
        spaceAfter=3
    )
    
    style_cover_sub = ParagraphStyle(
        'CoverSub',
        parent=styles['Normal'],
        fontName=FONT_NAME,
        fontSize=10,
        leading=14,
        textColor=c_accent,
        spaceAfter=8
    )
    
    style_h1 = ParagraphStyle(
        'Doc_H1',
        parent=styles['Normal'],
        fontName=FONT_NAME,
        fontSize=11.5,
        leading=15,
        textColor=c_primary,
        spaceBefore=8,
        spaceAfter=3,
        keepWithNext=True
    )
    
    style_h2 = ParagraphStyle(
        'Doc_H2',
        parent=styles['Normal'],
        fontName=FONT_NAME,
        fontSize=9,
        leading=12,
        textColor=c_accent,
        spaceBefore=6,
        spaceAfter=2,
        keepWithNext=True
    )
    
    style_body = ParagraphStyle(
        'Doc_Body',
        parent=styles['Normal'],
        fontName=FONT_NAME,
        fontSize=7,
        leading=10,
        textColor=c_secondary,
        spaceAfter=3
    )
    
    style_bullet = ParagraphStyle(
        'Doc_Bullet',
        parent=styles['Normal'],
        fontName=FONT_NAME,
        fontSize=7,
        leading=10,
        textColor=c_secondary,
        leftIndent=12,
        firstLineIndent=-8,
        spaceAfter=2
    )

    style_table_header = ParagraphStyle(
        'Doc_TH',
        parent=styles['Normal'],
        fontName=FONT_NAME,
        fontSize=6.5,
        leading=8.5,
        textColor=colors.white
    )
    
    style_table_cell = ParagraphStyle(
        'Doc_TD',
        parent=styles['Normal'],
        fontName=FONT_NAME,
        fontSize=6.5,
        leading=8.5,
        textColor=c_secondary
    )

    style_table_cell_code = ParagraphStyle(
        'Doc_TD_Code',
        parent=styles['Normal'],
        fontName=FONT_NAME,
        fontSize=6.5,
        leading=8.5,
        textColor=c_primary
    )

    style_flow_node = ParagraphStyle(
        'Doc_FlowNode',
        parent=styles['Normal'],
        fontName=FONT_NAME,
        fontSize=6.5,
        leading=8.5,
        textColor=c_primary
    )
    style_table_flow_node = style_flow_node
    
    story = []

    # =========================================================
    # PAGE 1: COVER, METADATA & PART I: BRD CORE
    # =========================================================
    story.append(Paragraph("FieldAI - Combined BRD & PRD Specification", style_cover_title))
    story.append(Paragraph("Business Requirements Document (BRD) & Product Requirements Document (PRD)", style_cover_sub))
    story.append(HRFlowable(width="100%", thickness=1.5, color=c_accent, spaceBefore=0, spaceAfter=6))

    meta_data = [
        [Paragraph("Document Type:", style_table_cell_code), Paragraph("Unified BRD & PRD Specification", style_table_cell),
         Paragraph("Product Stage:", style_table_cell_code), Paragraph("Production Baseline v1.0", style_table_cell)],
        [Paragraph("System Identifier:", style_table_cell_code), Paragraph("FieldAI Audit Assistant", style_table_cell),
         Paragraph("Target Environment:", style_table_cell_code), Paragraph("Render Cloud (Docker + PostgreSQL)", style_table_cell)],
        [Paragraph("Orchestration:", style_table_cell_code), Paragraph("LangGraph Multi-Agent StateGraph", style_table_cell),
         Paragraph("AI Engine:", style_table_cell_code), Paragraph("DeepSeek Flash & ElevenLabs Scribe", style_table_cell)],
        [Paragraph("Author / Practice:", style_table_cell_code), Paragraph("ACCELERAT Audit Technology", style_table_cell),
         Paragraph("Product Approver:", style_table_cell_code), Paragraph("Product Owner (Sami)", style_table_cell)],
    ]
    t_meta = Table(meta_data, colWidths=[95, 175, 105, 165])
    t_meta.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), c_table_bg),
        ('GRID', (0, 0), (-1, -1), 0.5, c_border),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 2.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2.5),
        ('FONTNAME', (0, 0), (-1, -1), FONT_NAME),
    ]))
    story.append(t_meta)
    story.append(Spacer(1, 4))

    # Executive Overview
    overview_text = (
        "<b>Executive Overview & Purpose:</b> This unified specification bridges business requirements (BRD) with technical and architectural execution (PRD) "
        "for <b>FieldAI</b>, the enterprise internal audit fieldwork platform. FieldAI transforms raw audit walkthrough recordings, multi-lingual interviews, "
        "and auditee procedural documentation (SOPs, manuals, policies) into a fully linked, verifiable, and standardized audit workpaper ecosystem. "
        "The system coordinates <b>21 specialized LangGraph agents</b> across <b>6 structured sub-graphs</b>, an interactive <b>15-page Streamlit portal</b>, "
        "an asynchronous <b>PostgreSQL job queue worker</b>, and deterministic audit analytics logic to cut audit cycle times by over 50% while guaranteeing "
        "100% bi-directional traceability back to source timestamps and document clauses."
    )
    story.append(Paragraph(overview_text, style_body))
    story.append(Spacer(1, 4))

    # PART I: BRD
    story.append(Paragraph("Part I: Business Requirements Document (BRD)", style_h1))
    
    story.append(Paragraph("1.1 Business Problems & Market Drivers", style_h2))
    story.append(Paragraph(
        "Internal audit departments face severe operational constraints during fieldwork and walkthrough phases: "
        "(1) <i>Manual Documentation Friction:</i> Auditors spend 40-60% of their fieldwork hours transcribing interviews, drafting step narratives, and manually drawing flowcharts. "
        "(2) <i>Information Asymmetry:</i> What auditees say in walkthroughs frequently diverges from what is written in approved SOPs, creating unobserved control gaps. "
        "(3) <i>Broken Traceability:</i> In standard workpapers, audit test steps rarely maintain direct evidence links to the exact interview timestamp or policy clause. "
        "(4) <i>Audit Standard Rigor:</i> The IIA Global Internal Audit Standards (2024 Edition) mandate thorough evidence grounding, supervisory review, and robust quality assurance.",
        style_body
    ))

    story.append(Paragraph("1.2 Strategic Business Objectives & Quantitative ROI", style_h2))
    brd_goals = [
        [Paragraph("Goal ID", style_table_header), Paragraph("Strategic Objective", style_table_header), Paragraph("Target Metric / Success Threshold", style_table_header), Paragraph("Business Impact", style_table_header)],
        [Paragraph("G-01", style_table_cell_code), Paragraph("Accelerate Walkthrough Lead Time", style_table_cell), Paragraph(">= 50% reduction in elapsed time from interview to approved RCM.", style_table_cell), Paragraph("Frees senior auditors from administrative drafting to focus on high-risk testing.", style_table_cell)],
        [Paragraph("G-02", style_table_cell_code), Paragraph("Single Source of Truth", style_table_cell), Paragraph("Zero manual re-keying across Process Table, Flowcharts, RCM, and Program.", style_table_cell), Paragraph("Eliminates version mismatch and inconsistent risk-control numbering.", style_table_cell)],
        [Paragraph("G-03", style_table_cell_code), Paragraph("Bi-Directional Source Traceability", style_table_cell), Paragraph("100% of steps, risks, controls, and tests cite exact timestamp or clause.", style_table_cell), Paragraph("Defensible audit trails during external quality assessment reviews (EQAR).", style_table_cell)],
        [Paragraph("G-04", style_table_cell_code), Paragraph("Objective Gap & Divergence Detection", style_table_cell), Paragraph("100% automated 5-category gap reconciliation between SOPs and interviews.", style_table_cell), Paragraph("Uncovers informal or undocumented operational workarounds immediately.", style_table_cell)],
        [Paragraph("G-05", style_table_cell_code), Paragraph("Full-Population Substantive Testing", style_table_cell), Paragraph("100% verification of duplicate payments, split POs, and SoD toxic roles.", style_table_cell), Paragraph("Transitions audits from small sample sizes (25 items) to full population analytics.", style_table_cell)],
    ]
    t_goals = Table(brd_goals, colWidths=[35, 135, 160, 210])
    t_goals.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), c_header_bg),
        ('GRID', (0, 0), (-1, -1), 0.5, c_border),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, c_table_bg]),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ('FONTNAME', (0, 0), (-1, -1), FONT_NAME),
    ]))
    story.append(t_goals)
    story.append(Spacer(1, 4))

    story.append(Paragraph("1.3 Stakeholder Personas & Permissions (RBAC)", style_h2))
    story.append(Paragraph(
        "• <b>Chief Audit Executive (CAE):</b> Reviews audit committee dashboards, process risk heatmaps, control gap densities, and continuous monitoring exceptions.<br/>"
        "• <b>Audit Manager:</b> Reviews change sets, resolves contradictory walkthrough testimonies, approves RCM design ratings, and formally locks audit test programs.<br/>"
        "• <b>Field Senior / Auditor:</b> Records/uploads walkthrough audio, inspects transcribed segments, edits process tables, reviews visual flowcharts, and runs substantive tests.<br/>"
        "• <b>Auditee / Business Process Owner:</b> Receives token-secured, read-only links via the confirmation portal to inspect visual swimlanes and confirm process accuracy.<br/>"
        "• <b>Audit System Administrator:</b> Manages user credentials, sampling parameter tables, risk/control libraries, regulatory framework mappings, and AI API keys.",
        style_body
    ))
    story.append(Spacer(1, 4))

    story.append(Paragraph("1.4 Regulatory & Framework Alignment", style_h2))
    story.append(Paragraph(
        "FieldAI maps all operational controls directly to international and regional governance frameworks: "
        "<b>IIA Global Internal Audit Standards (2024)</b>, <b>COSO Internal Control - Integrated Framework (2013)</b>, "
        "<b>COBIT 2019</b>, <b>ISO 27001:2022</b>, <b>Saudi National Cybersecurity Authority (NCA ECC)</b>, and <b>SAMA Cybersecurity Framework (CSF)</b>.",
        style_body
    ))

    # Page Break to Page 2
    story.append(PageBreak())

    # =========================================================
    # PAGE 2: PART II: PRD CLOUD ARCHITECTURE & VISUALIZATION ENGINE
    # =========================================================
    story.append(Paragraph("Part II: Product Requirements Document (PRD)", style_h1))
    story.append(Paragraph("2.1 System Architecture & Multi-Tier Cloud Topology", style_h2))
    story.append(Paragraph(
        "FieldAI operates as a modular, decoupled containerized platform on <b>Render Cloud</b>, specified via <code>render.yaml</code>:",
        style_body
    ))

    arch_rows = [
        [Paragraph("Service", style_table_header), Paragraph("Type", style_table_header), Paragraph("Technology", style_table_header), Paragraph("Architecture & Responsibility", style_table_header)],
        [Paragraph("fieldai-web", style_table_cell_code), Paragraph("Web Service", style_table_cell), Paragraph("Streamlit 1.35+, Docker", style_table_cell), Paragraph("Serves the 15-module auditor portal, st.data_editor, Cytoscape.js canvas, and st.audio_input.", style_table_cell)],
        [Paragraph("fieldai-worker", style_table_cell_code), Paragraph("Background Worker", style_table_cell), Paragraph("worker.py, Python 3.11", style_table_cell), Paragraph("Polls PostgreSQL jobs table via SELECT ... FOR UPDATE SKIP LOCKED. Executes transcription, OCR, and mining.", style_table_cell)],
        [Paragraph("fieldai-monitoring", style_table_cell_code), Paragraph("Cron Job", style_table_cell), Paragraph("run_monitoring.py, Cron", style_table_cell), Paragraph("Executes weekly scheduled continuous monitoring scripts against new client data extracts.", style_table_cell)],
        [Paragraph("fieldai-db", style_table_cell_code), Paragraph("Managed DB", style_table_cell), Paragraph("PostgreSQL 16, psycopg3", style_table_cell), Paragraph("Single store: Master models, version snapshots, immutable audit trail, files (BYTEA), and LangGraph checkpoints.", style_table_cell)],
        [Paragraph("External AI", style_table_cell_code), Paragraph("SaaS APIs", style_table_cell), Paragraph("ElevenLabs & DeepSeek", style_table_cell), Paragraph("ElevenLabs Scribe (word timestamps + diarization) and DeepSeek Flash for structured reasoning.", style_table_cell)],
    ]
    t_arch = Table(arch_rows, colWidths=[90, 75, 125, 250])
    t_arch.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), c_header_bg),
        ('GRID', (0, 0), (-1, -1), 0.5, c_border),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, c_table_bg]),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ('FONTNAME', (0, 0), (-1, -1), FONT_NAME),
    ]))
    story.append(t_arch)
    story.append(Spacer(1, 6))

    story.append(Paragraph("2.2 Visualization & Deliverables Engine", style_h2))
    story.append(Paragraph(
        "FieldAI provides a specialized dual-engine visualization architecture designed to handle complex audit flowcharts "
        "with non-bold Inter typography, curved connectors, swimlane segregation, and high-density information compacting:",
        style_body
    ))
    story.append(Paragraph(
        "• <b>Cytoscape.js Interactive Canvas (Dagre + Bezier Routing):</b> "
        "Employs the Dagre hierarchical layout algorithm with top-to-bottom orientation (rankDir: 'TB'), "
        "tight node/rank separation (nodeSep: 35, rankSep: 45), and automatic compound bounding for swimlanes. "
        "Features smooth curved Bezier routing, draggable nodes, click-to-inspect audit drawer, density presets (Micro, Compact, Full), and PNG/JSON export.<br/>"
        "• <b>High-Fidelity Graphviz Architecture Blueprint:</b> "
        "Rendered at authentic 1:1 pixel scale (use_container_width=False) to prevent magnification distortion. "
        "Features smooth spline routing, compact pill terminals, proportional decision diamonds, and left-aligned swimlane cluster labels.",
        style_body
    ))
    story.append(Spacer(1, 4))

    story.append(Paragraph("<b>Standard Deliverable Export Matrix:</b>", style_body))
    deliv_rows = [
        [Paragraph("Export Format", style_table_header), Paragraph("Extension", style_table_header), Paragraph("Underlying Generator", style_table_header), Paragraph("Target Application & Interoperability", style_table_header)],
        [Paragraph("BPMN 2.0 XML", style_table_cell_code), Paragraph(".bpmn", style_table_cell), Paragraph("exports/bpmn.py", style_table_cell), Paragraph("Standard OMG BPMN 2.0 XML with full swimlanes, gateway nodes, and sequence flows for Camunda and enterprise BPM suites.", style_table_cell)],
        [Paragraph("draw.io / Diagrams", style_table_cell_code), Paragraph(".drawio", style_table_cell), Paragraph("exports/drawio.py", style_table_cell), Paragraph("Native draw.io XML with swimlane containers and connected vertices. Can be directly converted to Microsoft Visio (.vsdx).", style_table_cell)],
        [Paragraph("Audit Summary PDF", style_table_cell_code), Paragraph(".pdf", style_table_cell), Paragraph("exports/pdf.py (ReportLab)", style_table_cell), Paragraph("Publication-quality formal deliverable with Inter typography, step tables, and risk/control listings.", style_table_cell)],
        [Paragraph("Graphviz DOT", style_table_cell_code), Paragraph(".dot", style_table_cell), Paragraph("agents/flowchart_agent.py", style_table_cell), Paragraph("Raw Graphviz source code formatted with cluster swimlanes for automated CI/CD documentation pipelines.", style_table_cell)],
        [Paragraph("Cytoscape JSON", style_table_cell_code), Paragraph(".json", style_table_cell), Paragraph("analytics/flowchart_viewer.py", style_table_cell), Paragraph("Complete node/edge element graph and layout metadata for web-based graph visualization engines.", style_table_cell)],
    ]
    t_deliv = Table(deliv_rows, colWidths=[100, 50, 110, 280])
    t_deliv.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), c_header_bg),
        ('GRID', (0, 0), (-1, -1), 0.5, c_border),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, c_table_bg]),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ('FONTNAME', (0, 0), (-1, -1), FONT_NAME),
    ]))
    story.append(t_deliv)

    # Page Break to Page 3
    story.append(PageBreak())

    # =========================================================
    # PAGE 3: PRD APPLICATION MODULE CATALOGUE (15 MODULES)
    # =========================================================
    story.append(Paragraph("2.3 Comprehensive Application Screen Catalogue (15 Modules)", style_h1))
    story.append(Paragraph(
        "The web user interface is partitioned into 15 purpose-built Streamlit modules under pages/, "
        "designed specifically for audit teams to progress systematically from engagement setup to fieldwork delivery:",
        style_body
    ))
    story.append(Spacer(1, 2))

    modules_data = [
        [Paragraph("File & Module", style_table_header), Paragraph("Key Functional Capabilities & Auditor Workflows", style_table_header)],
        [Paragraph("app.py / Portal", style_table_cell_code), Paragraph("Bcrypt login authentication, role-based navigation bar, active engagement context switcher, and global Ask FieldAI semantic copilot.", style_table_cell)],
        [Paragraph("1_Engagements.py", style_table_cell_code), Paragraph("Create/manage audit engagements, define process entities, assign stable code prefixes (e.g. P2P, O2C, HTR), and monitor fieldwork progress.", style_table_cell)],
        [Paragraph("2_Capture.py", style_table_cell_code), Paragraph("Direct browser audio recording via st.audio_input, multi-format upload (MP3, WAV, M4A, MP4, OGG), mandatory consent logging, diarization, speaker role mapping, segment redaction, and near-live interview copilot.", style_table_cell)],
        [Paragraph("3_Review_Changes.py", style_table_cell_code), Paragraph("Multi-meeting diff analysis; tracked changes review (Added, Changed, Confirmed, Contradicted, Removed); side-by-side conflict resolution; mandatory resolution notes; and version bumping (v1.0 -> v1.1).", style_table_cell)],
        [Paragraph("4_Process_Table.py", style_table_cell_code), Paragraph("Interactive master model table with in-place st.data_editor; columns for Step Code, Order, Description, Role, Department, System, Decision Gates, and source timestamps with confidence ratings.", style_table_cell)],
        [Paragraph("5_Flowchart.py", style_table_cell_code), Paragraph("Dual-engine visualization: Cytoscape.js interactive canvas (Dagre layout, Bezier curved connectors, draggable nodes, density modes: Micro/Compact/Full, click-to-inspect audit drawer) and Graphviz Blueprint (1:1 scale). 5 export formats.", style_table_cell)],
        [Paragraph("6_RCM.py", style_table_cell_code), Paragraph("Risk-Control Matrix with inherent risk ratings, control design adequacy evaluations, AI-suggested controls for unmitigated gaps, framework mapping (COSO, COBIT, ISO, NCA, SAMA), and Excel import/export.", style_table_cell)],
        [Paragraph("7_Audit_Program.py", style_table_cell_code), Paragraph("Test of Design (ToD) and Operating Effectiveness (ToE) procedures; deterministic sample size calculation from sampling table; PBC request lists; criteria references; manager approval and workpaper lock.", style_table_cell)],
        [Paragraph("8_Documents.py", style_table_cell_code), Paragraph("Document metadata register; multi-format upload (PDF OCR, DOCX, XLSX, PPTX); 5-category reconciliation against walkthrough interviews (Matches, Documented-not-described, Described-not-documented, Conflicting, Outdated); document citation Q&A.", style_table_cell)],
        [Paragraph("9_Prep.py", style_table_cell_code), Paragraph("Walkthrough preparation engine generating bilingual (Arabic and English) interview question packs grouped by step, follow-up interview agendas, and risk-based scoping matrices.", style_table_cell)],
        [Paragraph("10_Testing.py", style_table_cell_code), Paragraph("5 substantive testing engines: Automated Analytics (duplicate payments, split POs, Benford's Law), Segregation of Duties (SoD) toxic role matrices, Process Mining conformance, Evidence OCR attribute verification, and Recurring Tests.", style_table_cell)],
        [Paragraph("11_Findings.py", style_table_cell_code), Paragraph("Drafts formal audit observations in the 5 Cs format (Condition, Criteria, Cause, Effect, Recommendation); assigns risk ratings; and evaluates workpapers against IIA Global Standards 2024 quality checklist.", style_table_cell)],
        [Paragraph("12_Dashboard.py", style_table_cell_code), Paragraph("Executive CAE metrics, process risk heatmaps, control gap density distributions, fieldwork completion rates, and real-time exception alert feeds.", style_table_cell)],
        [Paragraph("13_Confirm.py", style_table_cell_code), Paragraph("Token-secured external portal enabling auditees to view approved process flows, inspect visual swimlanes, and submit validation comments or corrections.", style_table_cell)],
        [Paragraph("14_Admin.py", style_table_cell_code), Paragraph("User management & RBAC, sampling parameter tables, risk & control reference libraries, AI model credentials, and immutable audit trail viewer.", style_table_cell)],
        [Paragraph("15_Centralized_Storage.py", style_table_cell_code), Paragraph("Centralized enterprise evidence repository: folder tree hierarchy, multi-tag filtering, metadata indexing, document preview, secure downloads, and storage governance.", style_table_cell)],
    ]
    t_mod = Table(modules_data, colWidths=[120, 420])
    t_mod.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), c_header_bg),
        ('GRID', (0, 0), (-1, -1), 0.5, c_border),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, c_table_bg]),
        ('TOPPADDING', (0, 0), (-1, -1), 1.8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 1.8),
        ('FONTNAME', (0, 0), (-1, -1), FONT_NAME),
    ]))
    story.append(t_mod)

    # Page Break to Page 4
    story.append(PageBreak())

    # =========================================================
    # PAGE 4: PART III: MULTI-AGENT SPECIFICATION MATRIX (ALL 21 AGENTS)
    # =========================================================
    story.append(Paragraph("Part III: Multi-Agent Architecture, Configuration & Flow", style_h1))
    story.append(Paragraph(
        "FieldAI executes intelligence through 21 autonomous, single-responsibility agents in <code>agents/</code>, orchestrated via <b>LangGraph StateGraph</b>. "
        "State transitions, conditional branches, and human-in-the-loop review interrupts are typed under <code>FieldAIState</code> (graphs/state.py).",
        style_body
    ))
    story.append(Spacer(1, 2))

    story.append(Paragraph("3.1 Agent Configuration Matrix (All 21 Agents)", style_h2))
    agent_matrix = [
        [Paragraph("Agent Name", style_table_header), Paragraph("Engine / Model", style_table_header), Paragraph("Core Mission & Logic", style_table_header), Paragraph("Input -> Output Contract", style_table_header)],
        [Paragraph("transcription_agent", style_table_cell_code), Paragraph("ElevenLabs Scribe", style_table_cell), Paragraph("Speech-to-text with word timestamps, speaker diarization, language auto-detection (AR/EN), and redaction.", style_table_cell), Paragraph("audio file -> transcript_segments", style_table_cell)],
        [Paragraph("summary_agent", style_table_cell_code), Paragraph("DeepSeek Flash", style_table_cell), Paragraph("Synthesizes walkthrough narrative into executive summary, action items, open questions, and initial PBC requests.", style_table_cell), Paragraph("transcript -> summary, open_items, pbc", style_table_cell)],
        [Paragraph("process_extraction_agent", style_table_cell_code), Paragraph("DeepSeek Flash", style_table_cell), Paragraph("Extracts ordered steps, responsible roles, departments, systems, inputs/outputs, and decision diamonds.", style_table_cell), Paragraph("transcript -> extracted_steps", style_table_cell)],
        [Paragraph("risk_control_agent", style_table_cell_code), Paragraph("DeepSeek Flash", style_table_cell), Paragraph("Identifies stated and library-suggested risks and controls, categorizes nature/frequency/owner, and flags initial SoD gaps.", style_table_cell), Paragraph("steps -> extracted_risks, extracted_controls", style_table_cell)],
        [Paragraph("change_set_agent", style_table_cell_code), Paragraph("DeepSeek Flash", style_table_cell), Paragraph("Diffs new extraction against master model. Resolves entities, detects contradictions, and pauses for human review.", style_table_cell), Paragraph("new vs master -> change_set (Interrupt)", style_table_cell)],
        [Paragraph("flowchart_agent", style_table_cell_code), Paragraph("Deterministic", style_table_cell), Paragraph("Constructs Graphviz DOT and Cytoscape JSON graphs with swimlane clustering, risk/control badges, and compact styling.", style_table_cell), Paragraph("master model -> dot_code, cy_elements", style_table_cell)],
        [Paragraph("rcm_agent", style_table_cell_code), Paragraph("DeepSeek Flash", style_table_cell), Paragraph("Builds RCM rows, rates control design adequacy (Adequate/Partially/Inadequate), and maps regulatory frameworks.", style_table_cell), Paragraph("model -> rcm_rows, design_ratings", style_table_cell)],
        [Paragraph("audit_program_agent", style_table_cell_code), Paragraph("DeepSeek + Rules", style_table_cell), Paragraph("Formulates ToD and ToE steps, calculates deterministic sample sizes from sampling table, and sets PBC evidence lists.", style_table_cell), Paragraph("rcm -> test_steps, sample_sizes", style_table_cell)],
        [Paragraph("document_agent", style_table_cell_code), Paragraph("DeepSeek + OCR", style_table_cell), Paragraph("Parses auditee SOPs, policies, manuals (PDF/DOCX/XLSX), extracts metadata, and chunks text with section citations.", style_table_cell), Paragraph("document file -> doc_chunks, doc_metadata", style_table_cell)],
        [Paragraph("reconciliation_agent", style_table_cell_code), Paragraph("DeepSeek Flash", style_table_cell), Paragraph("Performs 5-category gap analysis comparing documented procedures with walkthrough interview statements.", style_table_cell), Paragraph("doc vs interview -> recon_items", style_table_cell)],
        [Paragraph("prep_agent", style_table_cell_code), Paragraph("DeepSeek Flash", style_table_cell), Paragraph("Generates bilingual walkthrough interview question packs, follow-up agendas, and risk-based scoping matrices.", style_table_cell), Paragraph("prior model -> bilingual question pack", style_table_cell)],
        [Paragraph("copilot_agent", style_table_cell_code), Paragraph("Scribe + DeepSeek", style_table_cell), Paragraph("Near-live walkthrough assistant analyzing audio chunks to propose real-time probing questions and instant PBC items.", style_table_cell), Paragraph("audio chunk -> live_prompts, instant_pbc", style_table_cell)],
        [Paragraph("analytics_agent", style_table_cell_code), Paragraph("Pandas + Rules", style_table_cell), Paragraph("Maps uploaded data schemas and runs fixed analytics: duplicate payments, split POs, weekend postings, Benford's Law.", style_table_cell), Paragraph("client data extract -> test_exceptions", style_table_cell)],
        [Paragraph("sod_agent", style_table_cell_code), Paragraph("Rules + DeepSeek", style_table_cell), Paragraph("Evaluates user-access matrices against toxic role combination rules, mapping conflicts to swimlane handoffs.", style_table_cell), Paragraph("user permissions -> sod_conflicts", style_table_cell)],
        [Paragraph("process_mining_agent", style_table_cell_code), Paragraph("Pandas + DeepSeek", style_table_cell), Paragraph("Analyzes event logs to identify process path variants, cycle time bottlenecks, and control bypasses.", style_table_cell), Paragraph("event log -> variants, bypass_alerts", style_table_cell)],
        [Paragraph("evidence_agent", style_table_cell_code), Paragraph("OCR + DeepSeek", style_table_cell), Paragraph("Inspects sample vouchers (PO, invoice, approval email) and verifies compliance with audit test attributes.", style_table_cell), Paragraph("voucher files -> attribute_results", style_table_cell)],
        [Paragraph("monitoring_agent", style_table_cell_code), Paragraph("Deterministic", style_table_cell), Paragraph("Schedules recurring automated tests, logs periodic cron runs, and raises exception alerts on new data.", style_table_cell), Paragraph("cron trigger -> updated_exceptions", style_table_cell)],
        [Paragraph("findings_agent", style_table_cell_code), Paragraph("DeepSeek Flash", style_table_cell), Paragraph("Drafts formal audit observations in the 5 Cs format (Condition, Criteria, Cause, Effect, Recommendation).", style_table_cell), Paragraph("exceptions -> structured 5 Cs findings", style_table_cell)],
        [Paragraph("qa_review_agent", style_table_cell_code), Paragraph("DeepSeek Flash", style_table_cell), Paragraph("Reviews working papers against IIA Global Standards 2024 checklist and methodology rules, creating review notes.", style_table_cell), Paragraph("workpapers -> qa_checklist, notes", style_table_cell)],
        [Paragraph("knowledge_agent", style_table_cell_code), Paragraph("DeepSeek Flash", style_table_cell), Paragraph("Enables cross-engagement intelligence reuse, baseline process templates, and year-on-year change detection.", style_table_cell), Paragraph("prior engagements -> baseline_model", style_table_cell)],
        [Paragraph("doc_qa_agent", style_table_cell_code), Paragraph("DeepSeek Flash", style_table_cell), Paragraph("Performs semantic search across transcripts and documents, answering auditor queries with exact citations.", style_table_cell), Paragraph("user question -> grounded cited answers", style_table_cell)],
    ]
    t_amatrix = Table(agent_matrix, colWidths=[95, 80, 215, 150])
    t_amatrix.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), c_header_bg),
        ('GRID', (0, 0), (-1, -1), 0.5, c_border),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, c_table_bg]),
        ('TOPPADDING', (0, 0), (-1, -1), 1.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 1.5),
        ('FONTNAME', (0, 0), (-1, -1), FONT_NAME),
    ]))
    story.append(t_amatrix)

    # Page Break to Page 5
    story.append(PageBreak())

    # =========================================================
    # PAGE 5: AGENTIC WORKFLOWS 1 & 2 (MEETING & DOCUMENT GRAPHS)
    # =========================================================
    story.append(Paragraph("3.2 Detailed Agentic Workflows & State Transitions", style_h1))
    story.append(Paragraph(
        "FieldAI executes intelligence through 6 distinct StateGraph pipelines. "
        "Each graph coordinates node executions, passes typed state (FieldAIState), and handles human review checkpoints.",
        style_body
    ))
    story.append(Spacer(1, 2))

    # Workflow 1 Table
    story.append(Paragraph("<b>Workflow 1: Core Walkthrough Meeting Graph (graphs/meeting_graph.py)</b>", style_h2))
    w1_steps = [
        [Paragraph("Seq", style_table_header), Paragraph("State Node / Agent", style_table_header), Paragraph("Input Context", style_table_header), Paragraph("Processing Logic & Verification Guardrail", style_table_header), Paragraph("State Output Artifact", style_table_header)],
        [Paragraph("1", style_table_cell_code), Paragraph("transcription\n(transcription_agent)", style_table_flow_node), Paragraph("Audio file (files table)", style_table_cell), Paragraph("Checks consent_recorded. Calls ElevenLabs Scribe (fallback OpenAI). Segments speech by speaker turn with second-level timestamps.", style_table_cell), Paragraph("transcript_segments", style_table_cell)],
        [Paragraph("2", style_table_cell_code), Paragraph("summary\n(summary_agent)", style_table_flow_node), Paragraph("transcript_segments", style_table_cell), Paragraph("DeepSeek Flash synthesizes <=200 word summary, key decisions, opens items, and PBC requests.", style_table_cell), Paragraph("summary, open_items, pbc_requests", style_table_cell)],
        [Paragraph("3", style_table_cell_code), Paragraph("process_extraction\n(process_extraction_agent)", style_table_flow_node), Paragraph("transcript_segments", style_table_cell), Paragraph("Extracts ordered steps, owners, systems, decision gates, inputs/outputs. Assigns stable step codes (e.g. P2P-01).", style_table_cell), Paragraph("extracted_steps (ProcessStep[])", style_table_cell)],
        [Paragraph("4", style_table_cell_code), Paragraph("risk_control\n(risk_control_agent)", style_table_flow_node), Paragraph("extracted_steps", style_table_cell), Paragraph("Identifies stated auditee risks and controls. Proposes library controls for unmitigated gap risks. Flags SoD conflicts on handoffs.", style_table_cell), Paragraph("extracted_risks, extracted_controls", style_table_cell)],
        [Paragraph("5", style_table_cell_code), Paragraph("change_set\n(change_set_agent)", style_table_flow_node), Paragraph("extractions vs master model", style_table_cell), Paragraph("Diffs extraction against current master model. Classifies items: Added, Changed, Confirmed, Contradicted, Removed.", style_table_cell), Paragraph("change_set, conflict_list", style_table_cell)],
        [Paragraph("6", style_table_cell_code), Paragraph("HUMAN REVIEW INTERRUPT\n(LangGraph interrupt())", style_table_flow_node), Paragraph("change_set", style_table_cell), Paragraph("Execution halts; PostgresSaver checkpointer stores thread state. Auditor reviews tracked changes and resolves conflicts on Review Changes page.", style_table_cell), Paragraph("review_decisions (resume)", style_table_cell)],
        [Paragraph("7", style_table_cell_code), Paragraph("apply_changes\n(core/model_repo.py)", style_table_flow_node), Paragraph("review_decisions", style_table_cell), Paragraph("Applies approved deltas to master model tables (steps, risks, controls). Bumps version snapshot (v1.0 -> v1.1) in versions table.", style_table_cell), Paragraph("updated master model", style_table_cell)],
        [Paragraph("8", style_table_cell_code), Paragraph("flowchart\n(flowchart_agent)", style_table_flow_node), Paragraph("master model", style_table_cell), Paragraph("Deterministic generator outputs Graphviz DOT and Cytoscape JSON with lane clustering and density modes (Micro, Compact, Full).", style_table_cell), Paragraph("dot_code, cy_elements", style_table_cell)],
        [Paragraph("9", style_table_cell_code), Paragraph("rcm\n(rcm_agent)", style_table_flow_node), Paragraph("master model", style_table_cell), Paragraph("Builds formal RCM, rates control design adequacy, and maps regulatory standards (COSO, COBIT, ISO, NCA, SAMA).", style_table_cell), Paragraph("rcm_rows, design_ratings", style_table_cell)],
        [Paragraph("10", style_table_cell_code), Paragraph("audit_program\n(audit_program_agent)", style_table_flow_node), Paragraph("rcm_rows", style_table_cell), Paragraph("Drafts ToD and ToE test procedures, calculates deterministic sample sizes from sampling table, and sets PBC evidence lists.", style_table_cell), Paragraph("test_steps, sample_sizes", style_table_cell)],
    ]
    t_w1 = Table(w1_steps, colWidths=[20, 110, 95, 215, 100])
    t_w1.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), c_header_bg),
        ('GRID', (0, 0), (-1, -1), 0.5, c_border),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, c_table_bg]),
        ('BACKGROUND', (0, 6), (-1, 6), c_pill_bg),
        ('TOPPADDING', (0, 0), (-1, -1), 1.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 1.5),
        ('FONTNAME', (0, 0), (-1, -1), FONT_NAME),
    ]))
    story.append(t_w1)
    story.append(Spacer(1, 4))

    # Workflow 2 Table
    story.append(Paragraph("<b>Workflow 2: Document Ingestion & Reconciliation Graph (graphs/document_graph.py)</b>", style_h2))
    w2_steps = [
        [Paragraph("Seq", style_table_header), Paragraph("State Node / Agent", style_table_header), Paragraph("Input Context", style_table_header), Paragraph("Processing Logic & Verification Guardrail", style_table_header), Paragraph("State Output Artifact", style_table_header)],
        [Paragraph("1", style_table_cell_code), Paragraph("document\n(document_agent)", style_table_flow_node), Paragraph("Policy / SOP file (PDF OCR, DOCX, XLSX)", style_table_cell), Paragraph("Extracts document register metadata (owner, version, effective date, approval status). Chunks document into section/page segments with citations.", style_table_cell), Paragraph("doc_chunks, doc_metadata", style_table_cell)],
        [Paragraph("2", style_table_cell_code), Paragraph("reconciliation\n(reconciliation_agent)", style_table_flow_node), Paragraph("doc_chunks vs interview master model", style_table_cell), Paragraph("Executes 5-Category Gap Analysis comparing written procedures vs interview testimony: (1) Matches, (2) Documented-not-described, (3) Described-not-documented, (4) Conflicting detail, (5) Outdated document.", style_table_cell), Paragraph("recon_items, gap_notes", style_table_cell)],
        [Paragraph("3", style_table_cell_code), Paragraph("HUMAN REVIEW INTERRUPT\n(Documents Page)", style_table_flow_node), Paragraph("recon_items", style_table_cell), Paragraph("Auditor inspects reconciliation findings side-by-side with SOP text, confirms criteria references, and selects items to merge into master model.", style_table_cell), Paragraph("accepted_recon_items", style_table_cell)],
        [Paragraph("4", style_table_cell_code), Paragraph("rebuild_deliverables\n(flowchart -> rcm -> audit_program)", style_table_flow_node), Paragraph("accepted_recon_items", style_table_cell), Paragraph("Re-runs deliverables graph to attach verified SOP clause citations to control criteria columns and refresh flowcharts.", style_table_cell), Paragraph("updated deliverables", style_table_cell)],
    ]
    t_w2 = Table(w2_steps, colWidths=[20, 110, 95, 215, 100])
    t_w2.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), c_header_bg),
        ('GRID', (0, 0), (-1, -1), 0.5, c_border),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, c_table_bg]),
        ('BACKGROUND', (0, 3), (-1, 3), c_pill_bg),
        ('TOPPADDING', (0, 0), (-1, -1), 1.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 1.5),
        ('FONTNAME', (0, 0), (-1, -1), FONT_NAME),
    ]))
    story.append(t_w2)

    # Page Break to Page 6
    story.append(PageBreak())

    # =========================================================
    # PAGE 6: AGENTIC WORKFLOWS 3, 4, 5, 6 (TESTING, REPORTING, PREP, ORCHESTRATOR)
    # =========================================================
    story.append(Paragraph("<b>Workflow 3: Substantive Field Testing Graph (graphs/testing_graph.py)</b>", style_h2))
    w3_steps = [
        [Paragraph("Branch / Node", style_table_header), Paragraph("Executing Agent", style_table_header), Paragraph("Data Input Source", style_table_header), Paragraph("Deterministic Testing Logic & Exceptions Detected", style_table_header), Paragraph("Deliverable Artifact", style_table_header)],
        [Paragraph("Router", style_table_cell_code), Paragraph("test_router (conditional edge)", style_table_cell), Paragraph("test_request.test_type", style_table_cell), Paragraph("Evaluates requested test category and dynamically routes execution state to analytics, sod, process_mining, or evidence.", style_table_cell), Paragraph("Branch routing dispatch", style_table_cell)],
        [Paragraph("Branch A: Analytics", style_table_cell_code), Paragraph("analytics_agent\n(Pandas library)", style_table_flow_node), Paragraph("Client financial extract (CSV / Excel)", style_table_cell), Paragraph("Full-population queries: duplicate payments, split POs below approval limits, weekend postings, round amounts, Benford's Law digit tests, 3-way match exceptions.", style_table_cell), Paragraph("test_results, exception_rows", style_table_cell)],
        [Paragraph("Branch B: SoD", style_table_cell_code), Paragraph("sod_agent\n(Matrix engine)", style_table_flow_node), Paragraph("ERP user-role-permission dump", style_table_cell), Paragraph("Evaluates permission matrix against toxic role pairs (e.g. create vendor + post payment, record invoice + approve payment). Maps conflicts to swimlane handoffs.", style_table_cell), Paragraph("sod_conflicts, violation_matrix", style_table_cell)],
        [Paragraph("Branch C: Mining", style_table_cell_code), Paragraph("process_mining_agent\n(Event log engine)", style_table_flow_node), Paragraph("Audit trail event log (case_id, activity, time, user)", style_table_cell), Paragraph("Computes process variant frequencies, throughput cycle times, happy path deviation ratios, and flags transactions that bypassed key controls.", style_table_cell), Paragraph("variants, bypass_alerts", style_table_cell)],
        [Paragraph("Branch D: Evidence", style_table_cell_code), Paragraph("evidence_agent\n(OCR attribute matcher)", style_table_flow_node), Paragraph("Sample voucher files (PO, invoice, approval email)", style_table_cell), Paragraph("OCR-inspects voucher files, verifies audit test attributes (authorized signature, amount matching PO, valid tax invoice), and quotes verified text.", style_table_cell), Paragraph("attribute_results, quotes", style_table_cell)],
        [Paragraph("Recurring Check", style_table_cell_code), Paragraph("check_recurring\n-> monitoring_agent", style_table_flow_node), Paragraph("make_recurring flag == True", style_table_cell), Paragraph("If enabled, registers test in test_runs table as recurring. Weekly Render Cron job (run_monitoring.py) re-executes tests on new data extracts.", style_table_cell), Paragraph("active_recurring_tests", style_table_cell)],
    ]
    t_w3 = Table(w3_steps, colWidths=[80, 105, 95, 170, 90])
    t_w3.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), c_header_bg),
        ('GRID', (0, 0), (-1, -1), 0.5, c_border),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, c_table_bg]),
        ('TOPPADDING', (0, 0), (-1, -1), 1.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 1.5),
        ('FONTNAME', (0, 0), (-1, -1), FONT_NAME),
    ]))
    story.append(t_w3)
    story.append(Spacer(1, 4))

    # Workflows 4, 5, 6 Summary
    story.append(Paragraph("<b>Workflows 4, 5 & 6: Reporting, Preparation, and Global Orchestrator</b>", style_h2))
    other_flows = [
        [Paragraph("Workflow Pipeline", style_table_header), Paragraph("Trigger & Agents", style_table_header), Paragraph("State Progression & Operational Behavior", style_table_header)],
        [Paragraph("Reporting & QA\n(graphs/reporting_graph.py)", style_table_cell_code), Paragraph("findings_agent\n-> qa_review_agent", style_table_cell), Paragraph("Triggered from Findings Page. findings_agent synthesizes test exceptions and reconciliation gaps into formal 5 Cs audit observations (Condition, Criteria, Cause, Effect, Recommendation). qa_review_agent evaluates the complete audit file against IIA Global Standards 2024 checklist.", style_table_cell)],
        [Paragraph("Meeting Prep & Copilot\n(graphs/prep_graph.py)", style_table_cell_code), Paragraph("prep_agent\n-> copilot_agent", style_table_cell), Paragraph("Triggered from Prep and Capture Pages. prep_agent analyzes prior year RCMs and uploaded SOPs to generate bilingual (Arabic and English) interview question packs. copilot_agent analyzes near-live 2-5 minute audio chunks, outputting real-time probing questions.", style_table_cell)],
        [Paragraph("Global Orchestrator\n(graphs/orchestrator.py)", style_table_cell_code), Paragraph("Supervisor Router\n+ doc_qa_agent", style_table_cell), Paragraph("Central dispatcher: Routes UI actions deterministically to sub-graphs without LLM cost. Free-text queries from 'Ask FieldAI' box are classified into target workflows or answered with exact citations via doc_qa_agent across transcripts and documents.", style_table_cell)],
    ]
    t_other = Table(other_flows, colWidths=[110, 100, 330])
    t_other.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), c_header_bg),
        ('GRID', (0, 0), (-1, -1), 0.5, c_border),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, c_table_bg]),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ('FONTNAME', (0, 0), (-1, -1), FONT_NAME),
    ]))
    story.append(t_other)

    # Page Break to Page 7
    story.append(PageBreak())

    # =========================================================
    # PAGE 7: PART IV: DATA ARCHITECTURE, SECURITY & STAKEHOLDER SIGN-OFF
    # =========================================================
    story.append(Paragraph("Part IV: Data Architecture, Security & Governance", style_h1))
    story.append(Paragraph("4.1 Relational Data Model (PostgreSQL 16)", style_h2))
    
    schema_rows = [
        [Paragraph("Table Name", style_table_header), Paragraph("Primary / Foreign Keys", style_table_header), Paragraph("Key Data Attributes & Schemas", style_table_header), Paragraph("Storage Purpose & Audit Role", style_table_header)],
        [Paragraph("users", style_table_cell_code), Paragraph("id (PK)", style_table_cell), Paragraph("username, password_hash, role, active, created_at", style_table_cell), Paragraph("User credentials with bcrypt cryptographic hashing and RBAC.", style_table_cell)],
        [Paragraph("engagements", style_table_cell_code), Paragraph("id (PK)", style_table_cell), Paragraph("name, entity, period, status, created_at", style_table_cell), Paragraph("Top-level audit containers (e.g. FY26 IT Audit).", style_table_cell)],
        [Paragraph("processes", style_table_cell_code), Paragraph("id (PK), engagement_id (FK)", style_table_cell), Paragraph("name, code_prefix, current_version, status", style_table_cell), Paragraph("Process definitions with stable code prefixes (P2P, O2C).", style_table_cell)],
        [Paragraph("sources", style_table_cell_code), Paragraph("id (PK), process_id (FK)", style_table_cell), Paragraph("kind, title, storage_path, language, consent_recorded", style_table_cell), Paragraph("Evidence registry; transcription blocked without consent.", style_table_cell)],
        [Paragraph("transcript_segments", style_table_cell_code), Paragraph("id (PK), source_id (FK)", style_table_cell), Paragraph("speaker_label, speaker_name, start_s, end_s, text, redacted", style_table_cell), Paragraph("Diarized utterances with exact second timestamps.", style_table_cell)],
        [Paragraph("steps", style_table_cell_code), Paragraph("id (PK), process_id (FK)", style_table_cell), Paragraph("step_code, order_num, description, role, system, is_decision", style_table_cell), Paragraph("Master flow steps. Never renumbered; status='withdrawn'.", style_table_cell)],
        [Paragraph("risks", style_table_cell_code), Paragraph("id (PK), process_id (FK)", style_table_cell), Paragraph("risk_code, description, inherent_rating, ai_suggested", style_table_cell), Paragraph("Identified inherent risk catalogue with severity scoring.", style_table_cell)],
        [Paragraph("controls", style_table_cell_code), Paragraph("id (PK), process_id (FK)", style_table_cell), Paragraph("control_code, description, type, nature, freq, key_control", style_table_cell), Paragraph("Internal controls with design adequacy ratings & framework refs.", style_table_cell)],
        [Paragraph("versions", style_table_cell_code), Paragraph("id (PK), process_id (FK)", style_table_cell), Paragraph("version_label, snapshot_json, change_log, approved_by", style_table_cell), Paragraph("Immutable version snapshots (v1.0, v1.1) approved by managers.", style_table_cell)],
        [Paragraph("change_sets", style_table_cell_code), Paragraph("id (PK), process_id (FK)", style_table_cell), Paragraph("source_id, status (proposed/applied), changes_json", style_table_cell), Paragraph("Multi-meeting delta proposals awaiting human auditor review.", style_table_cell)],
        [Paragraph("documents", style_table_cell_code), Paragraph("id (PK), source_id (FK)", style_table_cell), Paragraph("doc_type, owner, version, effective_date, approval_status", style_table_cell), Paragraph("Auditee document metadata register with freshness tracking.", style_table_cell)],
        [Paragraph("recon_items", style_table_cell_code), Paragraph("id (PK), process_id (FK)", style_table_cell), Paragraph("category, item_code, doc_ref, meeting_ref, note, status", style_table_cell), Paragraph("5-category reconciliation items between SOPs and interviews.", style_table_cell)],
        [Paragraph("tests", style_table_cell_code), Paragraph("id (PK), control_id (FK)", style_table_cell), Paragraph("test_code, objective, test_type, procedure, sample_size", style_table_cell), Paragraph("Audit program test steps linked to deterministic sampling rules.", style_table_cell)],
        [Paragraph("test_runs", style_table_cell_code), Paragraph("id (PK), test_id (FK)", style_table_cell), Paragraph("run_type, parameters_json, result_summary, exceptions_json", style_table_cell), Paragraph("Substantive test executions and continuous monitoring log.", style_table_cell)],
        [Paragraph("findings", style_table_cell_code), Paragraph("id (PK), process_id (FK)", style_table_cell), Paragraph("finding_code, condition, criteria, cause, effect, recommendation", style_table_cell), Paragraph("5 Cs formal audit observations linked to controls and tests.", style_table_cell)],
        [Paragraph("files", style_table_cell_code), Paragraph("id (PK)", style_table_cell), Paragraph("filename, mime_type, size_bytes, data (BYTEA), sha256", style_table_cell), Paragraph("Centralized binary storage accessible to web and worker.", style_table_cell)],
        [Paragraph("jobs", style_table_cell_code), Paragraph("id (PK)", style_table_cell), Paragraph("job_type, payload_json, status, progress, message, thread_id", style_table_cell), Paragraph("Asynchronous worker task queue (SELECT ... FOR UPDATE SKIP LOCKED).", style_table_cell)],
        [Paragraph("audit_log", style_table_cell_code), Paragraph("id (PK)", style_table_cell), Paragraph("user_id, action, entity, entity_id, details_json, created_at", style_table_cell), Paragraph("Append-only immutable audit trail recording all user actions.", style_table_cell)],
    ]
    t_schema = Table(schema_rows, colWidths=[90, 105, 160, 185])
    t_schema.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), c_header_bg),
        ('GRID', (0, 0), (-1, -1), 0.5, c_border),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, c_table_bg]),
        ('TOPPADDING', (0, 0), (-1, -1), 1.2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 1.2),
        ('FONTNAME', (0, 0), (-1, -1), FONT_NAME),
    ]))
    story.append(t_schema)
    story.append(Spacer(1, 4))

    story.append(Paragraph("4.2 Non-Functional Requirements & Security Governance", style_h2))
    nfrs = [
        "<b>Zero Arbitrary AI Code Execution:</b> To guarantee audit integrity, no LLM-generated code is ever executed against client financial data. All substantive testing relies on verified, deterministically coded Python/Pandas functions in analytics/library.py.",
        "<b>Auditor-in-the-Loop Safeguards:</b> All AI extractions are treated as draft recommendations. Human auditors retain full override authority. Changes to key controls require explicit managerial re-approval before updating master baselines.",
        "<b>Bi-Directional Source Traceability:</b> 100% of steps, risks, controls, tests, and findings maintain clickable links to raw audio timestamps (e.g. 00:14:22) or document section citations (e.g. SOP v2.1 Section 4.2).",
        "<b>Privacy & Redaction:</b> Mandatory consent logging blocks transcription until consent is verified. Auditors can redact sensitive PII or off-the-record statements prior to extraction.",
        "<b>Immutable Audit Trail:</b> Every login, model edit, change-set approval, and export action is permanently recorded in the append-only audit_log table with SHA-256 hash verification.",
    ]
    for nfr in nfrs:
        story.append(Paragraph(f"- {nfr}", style_bullet))
    story.append(Spacer(1, 6))

    # Formal Approval Block
    story.append(Paragraph("4.3 Acceptance Verification & Stakeholder Sign-Off", style_h2))
    sign_table_data = [
        [Paragraph("Prepared by: Lead Audit Solutions Architect", style_table_cell_code), Paragraph("Approved by: Product Owner & Practice Lead (Sami)", style_table_cell_code)],
        [Paragraph("Signature: ___________________________________", style_table_cell), Paragraph("Signature: ___________________________________", style_table_cell)],
        [Paragraph("Date: October 2026", style_table_cell), Paragraph("Status: Approved Production Specification v1.0", style_table_cell)],
    ]
    t_sign = Table(sign_table_data, colWidths=[270, 270])
    t_sign.setStyle(TableStyle([
        ('LINEABOVE', (0, 0), (-1, 0), 1, c_accent),
        ('TOPPADDING', (0, 0), (-1, -1), 2.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2.5),
        ('FONTNAME', (0, 0), (-1, -1), FONT_NAME),
    ]))
    story.append(KeepTogether(t_sign))

    # Build PDF
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"[PDF] Combined BRD/PRD successfully built at: {output_path}")

if __name__ == "__main__":
    out_dir = Path(__file__).resolve().parent.parent
    pdf_filename = "FieldAI_Comprehensive_BRD_PRD.pdf"
    target_path = str(out_dir / pdf_filename)
    generate_brd_prd_pdf(target_path)
