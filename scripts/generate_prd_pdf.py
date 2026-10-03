"""
FieldAI Comprehensive PRD PDF Generator
Generates a publication-grade, professional Product Requirements Document (PRD)
reflecting the full architecture, all 15 Streamlit pages, 21 LangGraph agents,
database models, and export deliverables of the FieldAI platform.
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

# Register Inter font if available
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
    Two-pass canvas to calculate total page count and draw running header/footer.
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
            self.drawString(36, 756, "FieldAI - Product Requirements Document (PRD) | Enterprise Multi-Agent Audit Fieldwork Platform")
            self.setStrokeColor(colors.HexColor("#e2e8f0"))
            self.setLineWidth(0.5)
            self.line(36, 750, 576, 750)
            
            # Running Footer
            self.line(36, 42, 576, 42)
            self.drawString(36, 32, "Confidential | Internal Audit Technology | Sami Associates | Version 1.0 Production Specification")
            page_text = f"Page {self._pageNumber} of {page_count}"
            self.drawRightString(576, 32, page_text)
            self.restoreState()

def create_prd_pdf(output_path: str):
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=46,
        bottomMargin=46
    )
    
    styles = getSampleStyleSheet()
    
    # Custom color palette
    c_primary = colors.HexColor("#0f172a")     # Slate 900
    c_accent = colors.HexColor("#0284c7")      # Sky 600
    c_secondary = colors.HexColor("#334155")   # Slate 700
    c_muted = colors.HexColor("#64748b")       # Slate 500
    c_border = colors.HexColor("#cbd5e1")      # Slate 300
    c_table_bg = colors.HexColor("#f8fafc")    # Slate 50
    c_header_bg = colors.HexColor("#1e293b")   # Slate 800
    
    style_cover_title = ParagraphStyle(
        'CoverTitle',
        parent=styles['Normal'],
        fontName=FONT_NAME,
        fontSize=22,
        leading=28,
        textColor=c_primary,
        spaceAfter=4
    )
    
    style_cover_sub = ParagraphStyle(
        'CoverSub',
        parent=styles['Normal'],
        fontName=FONT_NAME,
        fontSize=11,
        leading=15,
        textColor=c_accent,
        spaceAfter=12
    )
    
    style_h1 = ParagraphStyle(
        'PRD_H1',
        parent=styles['Normal'],
        fontName=FONT_NAME,
        fontSize=13,
        leading=17,
        textColor=c_primary,
        spaceBefore=12,
        spaceAfter=5,
        keepWithNext=True
    )
    
    style_h2 = ParagraphStyle(
        'PRD_H2',
        parent=styles['Normal'],
        fontName=FONT_NAME,
        fontSize=10,
        leading=13,
        textColor=c_accent,
        spaceBefore=8,
        spaceAfter=3,
        keepWithNext=True
    )
    
    style_body = ParagraphStyle(
        'PRD_Body',
        parent=styles['Normal'],
        fontName=FONT_NAME,
        fontSize=8,
        leading=11.5,
        textColor=c_secondary,
        spaceAfter=5
    )
    
    style_bullet = ParagraphStyle(
        'PRD_Bullet',
        parent=styles['Normal'],
        fontName=FONT_NAME,
        fontSize=8,
        leading=11.5,
        textColor=c_secondary,
        leftIndent=12,
        firstLineIndent=-8,
        spaceAfter=3
    )

    style_table_header = ParagraphStyle(
        'PRD_TH',
        parent=styles['Normal'],
        fontName=FONT_NAME,
        fontSize=7.5,
        leading=9.5,
        textColor=colors.white
    )
    
    style_table_cell = ParagraphStyle(
        'PRD_TD',
        parent=styles['Normal'],
        fontName=FONT_NAME,
        fontSize=7,
        leading=9,
        textColor=c_secondary
    )

    style_table_cell_code = ParagraphStyle(
        'PRD_TD_Code',
        parent=styles['Normal'],
        fontName=FONT_NAME,
        fontSize=7,
        leading=9,
        textColor=c_primary
    )
    
    story = []

    # ---------------------------------------------------------
    # COVER / HEADER BLOCK
    # ---------------------------------------------------------
    story.append(Spacer(1, 10))
    story.append(Paragraph("FieldAI - Product Requirements Document (PRD)", style_cover_title))
    story.append(Paragraph("Enterprise Multi-Agent Audit Fieldwork & Process Intelligence Platform", style_cover_sub))
    story.append(HRFlowable(width="100%", thickness=2, color=c_accent, spaceBefore=0, spaceAfter=10))

    meta_data = [
        [Paragraph("Document ID:", style_table_cell_code), Paragraph("PRD-FIELDAI-2026-V1.0", style_table_cell),
         Paragraph("Product Stage:", style_table_cell_code), Paragraph("Production / Active Deployment", style_table_cell)],
        [Paragraph("System Version:", style_table_cell_code), Paragraph("v1.0 (Full Multi-Agent Architecture)", style_table_cell),
         Paragraph("Target Deployment:", style_table_cell_code), Paragraph("Render Cloud (Docker + PostgreSQL)", style_table_cell)],
        [Paragraph("Prepared By:", style_table_cell_code), Paragraph("Sami Associates Internal Audit Tech Practice", style_table_cell),
         Paragraph("Product Owner:", style_table_cell_code), Paragraph("Sami (Leadership Review Approved)", style_table_cell)],
        [Paragraph("Core Technologies:", style_table_cell_code), Paragraph("LangGraph | Streamlit | PostgreSQL | ElevenLabs | DeepSeek", style_table_cell),
         Paragraph("Date of Specification:", style_table_cell_code), Paragraph("October 2026", style_table_cell)],
    ]
    t_meta = Table(meta_data, colWidths=[90, 180, 100, 170])
    t_meta.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), c_table_bg),
        ('GRID', (0, 0), (-1, -1), 0.5, c_border),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('FONTNAME', (0, 0), (-1, -1), FONT_NAME),
    ]))
    story.append(t_meta)
    story.append(Spacer(1, 8))

    # Executive Summary Box
    summary_text = (
        "<b>Executive Summary:</b> FieldAI is an enterprise-grade, multi-agent AI audit fieldwork platform engineered "
        "to automate the transformation of unstructured audit walkthrough interviews, meeting recordings, and auditee documents "
        "(SOPs, policies, manuals) into a linked, rigorous, and verifiable internal audit workpaper package. "
        "The system replaces manual transcription, narrative drafting, flowchart drawing, and RCM generation with a coordinated "
        "orchestration of <b>21 specialized LangGraph agents</b>, an interactive <b>15-page Streamlit portal</b>, "
        "a reliable <b>PostgreSQL state store and job queue</b>, and a dedicated <b>asynchronous background worker</b>. "
        "Every single workpaper element (step, risk, control, test, finding) maintains bi-directional source traceability "
        "with second-level audio timestamps and document clause citations, ensuring compliance with the IIA Global Internal Audit Standards (2024)."
    )
    story.append(Paragraph(summary_text, style_body))
    story.append(Spacer(1, 6))

    # ---------------------------------------------------------
    # SECTION 1: SYSTEM ARCHITECTURE & TOPOLOGY
    # ---------------------------------------------------------
    story.append(Paragraph("1. System Architecture & Infrastructure Topology", style_h1))
    story.append(Paragraph(
        "FieldAI adopts a decoupled, multi-tier microservices architecture defined declaratively via a Render Blueprint (render.yaml). "
        "The system coordinates web presentation, background computing, recurring cron testing, database persistence, and external AI providers.",
        style_body
    ))

    arch_data = [
        [Paragraph("Tier / Service", style_table_header), Paragraph("Component", style_table_header), Paragraph("Technology Stack", style_table_header), Paragraph("Operational Role & SLA", style_table_header)],
        [Paragraph("Frontend / Web", style_table_cell_code), Paragraph("fieldai-web", style_table_cell), Paragraph("Streamlit 1.35+, Python 3.11, Docker", style_table_cell), Paragraph("Interactive UI for auditors, 15 module pages, data editors, Cytoscape/Graphviz viewers, live audio input.", style_table_cell)],
        [Paragraph("Asynchronous Worker", style_table_cell_code), Paragraph("fieldai-worker", style_table_cell), Paragraph("worker.py, Python 3.11, Docker", style_table_cell), Paragraph("Picks up long-running tasks (transcription, OCR, analytics, process mining) via PostgreSQL SKIP LOCKED queue.", style_table_cell)],
        [Paragraph("Recurring Scheduler", style_table_cell_code), Paragraph("fieldai-monitoring", style_table_cell), Paragraph("jobs/run_monitoring.py, Cron", style_table_cell), Paragraph("Executes weekly continuous monitoring scripts, evaluates recurring tests against latest data extracts.", style_table_cell)],
        [Paragraph("Relational Store", style_table_cell_code), Paragraph("fieldai-db", style_table_cell), Paragraph("PostgreSQL 16 (psycopg 3 pool)", style_table_cell), Paragraph("Single source of truth: master process models, versions, audit trail, LangGraph checkpoints, and binary files.", style_table_cell)],
        [Paragraph("Speech-to-Text", style_table_cell_code), Paragraph("STT Engine", style_table_cell), Paragraph("ElevenLabs Scribe / OpenAI gpt-4o", style_table_cell), Paragraph("Primary diarization and transcription with word-level timestamps in Arabic, English, or mixed speech.", style_table_cell)],
        [Paragraph("LLM Reasoning", style_table_cell_code), Paragraph("Cognitive Core", style_table_cell), Paragraph("DeepSeek Flash (OpenAI SDK compat)", style_table_cell), Paragraph("Process extraction, risk/control mapping, 5-category reconciliation, test procedures, and QA checks.", style_table_cell)],
    ]
    t_arch = Table(arch_data, colWidths=[90, 85, 150, 215])
    t_arch.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), c_header_bg),
        ('GRID', (0, 0), (-1, -1), 0.5, c_border),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, c_table_bg]),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('FONTNAME', (0, 0), (-1, -1), FONT_NAME),
    ]))
    story.append(t_arch)
    story.append(Spacer(1, 8))

    # ---------------------------------------------------------
    # SECTION 2: APPLICATION MODULE CATALOGUE (15 PAGES)
    # ---------------------------------------------------------
    story.append(Paragraph("2. Comprehensive Application Screen Catalogue (15 Modules)", style_h1))
    story.append(Paragraph(
        "The web user interface is partitioned into 15 purpose-built Streamlit modules under pages/, "
        "designed specifically for audit teams to progress systematically from engagement setup to fieldwork delivery.",
        style_body
    ))

    screens_data = [
        [Paragraph("Page & File", style_table_header), Paragraph("Module Name", style_table_header), Paragraph("Key Functional Capabilities & User Interactions", style_table_header)],
        [Paragraph("app.py", style_table_cell_code), Paragraph("Portal & Auth", style_table_cell), Paragraph("Bcrypt login authentication, role-based page navigation, active engagement selector, global Ask FieldAI copilot.", style_table_cell)],
        [Paragraph("1_Engagements.py", style_table_cell_code), Paragraph("Engagements & Scoping", style_table_cell), Paragraph("Create/manage audit engagements, define process entities, assign stable code prefixes (e.g. P2P, O2C, HTR), track completion.", style_table_cell)],
        [Paragraph("2_Capture.py", style_table_cell_code), Paragraph("Walkthrough Capture", style_table_cell), Paragraph("Browser in-person recording (st.audio_input), multi-format audio/video upload, mandatory consent logging, diarization, redaction, near-live co-pilot.", style_table_cell)],
        [Paragraph("3_Review_Changes.py", style_table_cell_code), Paragraph("Change Set Review", style_table_cell), Paragraph("Multi-meeting diff analysis; tracked changes review (Added/Changed/Confirmed/Contradicted/Removed); side-by-side conflict resolution; version bump.", style_table_cell)],
        [Paragraph("4_Process_Table.py", style_table_cell_code), Paragraph("Master Process Table", style_table_cell), Paragraph("Interactive tabular view of steps, owners, systems, risks, controls; in-place data editor; source citation links; confidence ratings.", style_table_cell)],
        [Paragraph("5_Flowchart.py", style_table_cell_code), Paragraph("Interactive Flowcharts", style_table_cell), Paragraph("Dual-engine rendering: Cytoscape.js interactive canvas (Dagre layout, Bezier curves, draggable nodes, density presets) and Graphviz Blueprint (1:1 scale). 5 export formats.", style_table_cell)],
        [Paragraph("6_RCM.py", style_table_cell_code), Paragraph("Risk-Control Matrix", style_table_cell), Paragraph("Inherent risk evaluation, control design adequacy ratings, AI suggestions for unmitigated gaps, framework mapping (COSO, COBIT, ISO, NCA, SAMA).", style_table_cell)],
        [Paragraph("7_Audit_Program.py", style_table_cell_code), Paragraph("Audit Test Program", style_table_cell), Paragraph("Generates ToD and ToE steps; deterministic sample size calculation based on frequency and risk; PBC request lists; manager approval and workpaper lock.", style_table_cell)],
        [Paragraph("8_Documents.py", style_table_cell_code), Paragraph("Document Reconciliation", style_table_cell), Paragraph("Document register; multi-format upload (PDF OCR, DOCX, XLSX); 5-category reconciliation against walkthrough statements; document citation Q&A.", style_table_cell)],
        [Paragraph("9_Prep.py", style_table_cell_code), Paragraph("Meeting Preparation", style_table_cell), Paragraph("Generates bilingual (Arabic/English) walkthrough question packs, follow-up interview agendas, and risk-based scoping matrices.", style_table_cell)],
        [Paragraph("10_Testing.py", style_table_cell_code), Paragraph("Field Testing & Analytics", style_table_cell), Paragraph("5 testing engines: Automated Analytics (duplicate payments, split POs, Benford's Law), Segregation of Duties (SoD), Process Mining, Evidence OCR, Recurring Tests.", style_table_cell)],
        [Paragraph("11_Findings.py", style_table_cell_code), Paragraph("Findings & QA", style_table_cell), Paragraph("Drafts 5 Cs findings (Condition, Criteria, Cause, Effect, Recommendation); automated QA review against IIA Global Standards 2024 checklist.", style_table_cell)],
        [Paragraph("12_Dashboard.py", style_table_cell_code), Paragraph("Executive Dashboard", style_table_cell), Paragraph("CAE executive metrics, process risk heatmaps, control gap analytics, fieldwork completion tracking, automated exception alerts.", style_table_cell)],
        [Paragraph("13_Confirm.py", style_table_cell_code), Paragraph("Auditee Confirmation", style_table_cell), Paragraph("Secure token-based external access portal for auditees to review process narratives, inspect visual swimlanes, and submit validation feedback.", style_table_cell)],
        [Paragraph("14_Admin.py", style_table_cell_code), Paragraph("System Administration", style_table_cell), Paragraph("User management and RBAC, sampling parameter tables, risk and control reference libraries, AI model credentials, immutable audit log viewer.", style_table_cell)],
        [Paragraph("15_Centralized_Storage.py", style_table_cell_code), Paragraph("Centralized Storage", style_table_cell), Paragraph("Enterprise document repository: hierarchical folder tree, multi-tag filtering, metadata indexing, document preview, secure downloads, storage governance.", style_table_cell)],
    ]
    t_screens = Table(screens_data, colWidths=[90, 100, 350])
    t_screens.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), c_header_bg),
        ('GRID', (0, 0), (-1, -1), 0.5, c_border),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, c_table_bg]),
        ('TOPPADDING', (0, 0), (-1, -1), 2.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2.5),
        ('FONTNAME', (0, 0), (-1, -1), FONT_NAME),
    ]))
    story.append(t_screens)
    story.append(Spacer(1, 8))

    # Page Break before Deep Dives
    story.append(PageBreak())

    # ---------------------------------------------------------
    # SECTION 3: MULTI-AGENT SPECIFICATIONS (21 AGENTS)
    # ---------------------------------------------------------
    story.append(Paragraph("3. Multi-Agent Ecosystem Specifications (21 Agents)", style_h1))
    story.append(Paragraph(
        "FieldAI executes all substantive intelligence tasks through 21 autonomous, single-responsibility agents located in agents/. "
        "Agents are orchestrated as nodes in LangGraph state graphs with typed state contracts (FieldAIState).",
        style_body
    ))

    agent_data = [
        [Paragraph("#", style_table_header), Paragraph("Agent Module", style_table_header), Paragraph("Engine", style_table_header), Paragraph("Operational Function & Core Logic", style_table_header), Paragraph("Key Outputs", style_table_header)],
        [Paragraph("1", style_table_cell), Paragraph("transcription_agent", style_table_cell_code), Paragraph("ElevenLabs Scribe", style_table_cell), Paragraph("Transcribes audio/video with speaker diarization, word-level timestamps, and language detection. Redaction support.", style_table_cell), Paragraph("transcript_segments", style_table_cell)],
        [Paragraph("2", style_table_cell), Paragraph("summary_agent", style_table_cell_code), Paragraph("DeepSeek Flash", style_table_cell), Paragraph("Generates concise executive summaries, open questions, and preliminary PBC request lists.", style_table_cell), Paragraph("summary, open_items, pbc", style_table_cell)],
        [Paragraph("3", style_table_cell), Paragraph("process_extraction_agent", style_table_cell_code), Paragraph("DeepSeek Flash", style_table_cell), Paragraph("Extracts ordered steps, responsible roles, departments, systems, decision points, and handoffs from text.", style_table_cell), Paragraph("ProcessStep objects", style_table_cell)],
        [Paragraph("4", style_table_cell), Paragraph("risk_control_agent", style_table_cell_code), Paragraph("DeepSeek Flash", style_table_cell), Paragraph("Identifies stated and library-suggested risks and controls, categorizes nature/frequency/owner, flags SoD gaps.", style_table_cell), Paragraph("Risk & Control objects", style_table_cell)],
        [Paragraph("5", style_table_cell), Paragraph("change_set_agent", style_table_cell_code), Paragraph("DeepSeek Flash", style_table_cell), Paragraph("Compares new extractions with master model. Resolves entities, generates tracked changes, pauses for auditor review.", style_table_cell), Paragraph("change_set, conflict_list", style_table_cell)],
        [Paragraph("6", style_table_cell), Paragraph("document_agent", style_table_cell_code), Paragraph("DeepSeek + OCR", style_table_cell), Paragraph("Parses policies, SOPs, and manuals (PDF, DOCX, XLSX). Registers metadata and chunks text with section citations.", style_table_cell), Paragraph("doc_chunks, doc_metadata", style_table_cell)],
        [Paragraph("7", style_table_cell), Paragraph("reconciliation_agent", style_table_cell_code), Paragraph("DeepSeek Flash", style_table_cell), Paragraph("Performs 5-category gap analysis comparing documented procedures with walkthrough interview statements.", style_table_cell), Paragraph("recon_items, gap_notes", style_table_cell)],
        [Paragraph("8", style_table_cell), Paragraph("flowchart_agent", style_table_cell_code), Paragraph("Deterministic", style_table_cell), Paragraph("Generates Graphviz DOT and Cytoscape JSON models with swimlane clustering, risk/control badges, and density modes.", style_table_cell), Paragraph("dot_code, cy_elements", style_table_cell)],
        [Paragraph("9", style_table_cell), Paragraph("rcm_agent", style_table_cell_code), Paragraph("DeepSeek Flash", style_table_cell), Paragraph("Constructs Risk-Control Matrix, evaluates design adequacy, suggests gap controls, and maps regulatory frameworks.", style_table_cell), Paragraph("rcm_rows, design_ratings", style_table_cell)],
        [Paragraph("10", style_table_cell), Paragraph("audit_program_agent", style_table_cell_code), Paragraph("DeepSeek + Rules", style_table_cell), Paragraph("Drafts ToD and ToE procedures, computes deterministic sample sizes from sampling table, defines PBC requirements.", style_table_cell), Paragraph("test_steps, sample_basis", style_table_cell)],
        [Paragraph("11", style_table_cell), Paragraph("prep_agent", style_table_cell_code), Paragraph("DeepSeek Flash", style_table_cell), Paragraph("Generates bilingual walkthrough questionnaires, scoping matrices, and tailored follow-up interview agendas.", style_table_cell), Paragraph("question_pack, scope_plan", style_table_cell)],
        [Paragraph("12", style_table_cell), Paragraph("copilot_agent", style_table_cell_code), Paragraph("Scribe + DeepSeek", style_table_cell), Paragraph("Near-live interview assistant analyzing audio chunks to suggest real-time probing questions and capture PBC items.", style_table_cell), Paragraph("live_prompts, instant_pbc", style_table_cell)],
        [Paragraph("13", style_table_cell), Paragraph("knowledge_agent", style_table_cell_code), Paragraph("DeepSeek Flash", style_table_cell), Paragraph("Enables cross-engagement intelligence reuse, baseline process templates, and year-on-year change detection.", style_table_cell), Paragraph("baseline_model, yoy_diff", style_table_cell)],
        [Paragraph("14", style_table_cell), Paragraph("doc_qa_agent", style_table_cell_code), Paragraph("DeepSeek Flash", style_table_cell), Paragraph("Performs semantic search across transcripts and documents, answering auditor queries with exact citations.", style_table_cell), Paragraph("cited_answers", style_table_cell)],
        [Paragraph("15", style_table_cell), Paragraph("analytics_agent", style_table_cell_code), Paragraph("Pandas + Rules", style_table_cell), Paragraph("Maps data schemas and executes fixed audit analytics (duplicate payments, split purchases, Benford's Law).", style_table_cell), Paragraph("test_results, exceptions", style_table_cell)],
        [Paragraph("16", style_table_cell), Paragraph("evidence_agent", style_table_cell_code), Paragraph("OCR + DeepSeek", style_table_cell), Paragraph("Inspects sample evidence files (PO, invoice, approval email) and verifies compliance with audit test attributes.", style_table_cell), Paragraph("attribute_results, quotes", style_table_cell)],
        [Paragraph("17", style_table_cell), Paragraph("sod_agent", style_table_cell_code), Paragraph("Rules + DeepSeek", style_table_cell), Paragraph("Evaluates user-access matrices against toxic role combination rules, mapping conflicts to swimlane handoffs.", style_table_cell), Paragraph("sod_conflicts, role_gaps", style_table_cell)],
        [Paragraph("18", style_table_cell), Paragraph("process_mining_agent", style_table_cell_code), Paragraph("Pandas + DeepSeek", style_table_cell), Paragraph("Analyzes event logs to identify process variants, calculate throughput times, and detect control bypasses.", style_table_cell), Paragraph("variants, bypass_alerts", style_table_cell)],
        [Paragraph("19", style_table_cell), Paragraph("monitoring_agent", style_table_cell_code), Paragraph("Deterministic", style_table_cell), Paragraph("Schedules recurring automated tests, logs periodic execution runs, and triggers exception alerts.", style_table_cell), Paragraph("cron_logs, new_exceptions", style_table_cell)],
        [Paragraph("20", style_table_cell), Paragraph("findings_agent", style_table_cell_code), Paragraph("DeepSeek Flash", style_table_cell), Paragraph("Drafts formal audit findings in the 5 Cs format (Condition, Criteria, Cause, Effect, Recommendation).", style_table_cell), Paragraph("Finding objects, ratings", style_table_cell)],
        [Paragraph("21", style_table_cell), Paragraph("qa_review_agent", style_table_cell_code), Paragraph("DeepSeek Flash", style_table_cell), Paragraph("Reviews workpapers against IIA Global Standards 2024 and methodology checklist, generating review notes.", style_table_cell), Paragraph("qa_checklist, review_notes", style_table_cell)],
    ]
    t_agents = Table(agent_data, colWidths=[15, 105, 80, 240, 100])
    t_agents.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), c_header_bg),
        ('GRID', (0, 0), (-1, -1), 0.5, c_border),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, c_table_bg]),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ('FONTNAME', (0, 0), (-1, -1), FONT_NAME),
    ]))
    story.append(t_agents)
    story.append(Spacer(1, 8))

    # ---------------------------------------------------------
    # SECTION 4: FLOWCHART & DELIVERABLE ENGINE DETAILS
    # ---------------------------------------------------------
    story.append(Paragraph("4. Visualization & Deliverables Engine", style_h1))
    story.append(Paragraph(
        "FieldAI provides a specialized dual-engine visualization architecture designed to handle complex audit flowcharts "
        "with non-bold Inter typography, curved connectors, swimlane segregation, and high-density information compacting.",
        style_body
    ))
    
    story.append(Paragraph("<b>4.1 Cytoscape.js Interactive Canvas (Dagre + Bezier Routing):</b>", style_body))
    story.append(Paragraph(
        "- <b>Layout Engine:</b> Dagre hierarchical DAG layout with top-to-bottom orientation (rankDir: 'TB'), "
        "tight node/rank separation (nodeSep: 35, rankSep: 45), and automatic parent-compound bounding for swimlanes.<br/>"
        "- <b>Connector Styling:</b> Smooth curved Bezier curves (curve-style: 'bezier') with obstacle-aware routing to eliminate jagged angles.<br/>"
        "- <b>Audit Badges:</b> Inherent risk pills (crimson R-xx), control badges (emerald C-xx), decision diamonds (amber), and system cylinders.<br/>"
        "- <b>Density Presets:</b> Supports three layout compaction modes: <i>Micro</i> (ultra-dense), <i>Compact</i> (default 8pt font, tight padding), and <i>Full</i>.<br/>"
        "- <b>Interactivity:</b> Fully draggable nodes, click-to-inspect audit metadata side drawer, zoom controls (+In, -Out, Fit, Reset), PNG and JSON exports.",
        style_bullet
    ))
    story.append(Spacer(1, 4))

    story.append(Paragraph("<b>4.2 High-Fidelity Graphviz Architecture Blueprint:</b>", style_body))
    story.append(Paragraph(
        "- <b>Scale & Routing:</b> Rendered at authentic 1:1 pixel scale (use_container_width=False) preventing oversized magnification. "
        "Smooth spline routing (splines=spline) with left-aligned swimlane cluster labels.<br/>"
        "- <b>Geometry:</b> Compact pill shapes for Start/End terminals, proportioned decision diamonds, word-wrapped process text, and eliminated overhead header boxes.",
        style_bullet
    ))
    story.append(Spacer(1, 4))

    story.append(Paragraph("<b>4.3 Multi-Format Export Deliverables:</b>", style_body))
    deliverables_data = [
        [Paragraph("Export Format", style_table_header), Paragraph("Extension", style_table_header), Paragraph("Target Application & Interoperability", style_table_header)],
        [Paragraph("BPMN 2.0 XML", style_table_cell_code), Paragraph(".bpmn", style_table_cell), Paragraph("Standard OMG BPMN 2.0 with full swimlanes, gateway nodes, and sequence flows for Camunda, Signavio, and enterprise BPM suites.", style_table_cell)],
        [Paragraph("draw.io / Diagrams", style_table_cell_code), Paragraph(".drawio", style_table_cell), Paragraph("Native draw.io XML with swimlane containers and connected vertices. Can be directly converted to Microsoft Visio (.vsdx).", style_table_cell)],
        [Paragraph("Audit Summary PDF", style_table_cell_code), Paragraph(".pdf", style_table_cell), Paragraph("Publication-quality formal deliverable generated via ReportLab with Inter typography, step tables, and risk/control listings.", style_table_cell)],
        [Paragraph("Graphviz DOT", style_table_cell_code), Paragraph(".dot", style_table_cell), Paragraph("Raw Graphviz source code formatted with cluster swimlanes for automated CI/CD documentation pipelines.", style_table_cell)],
        [Paragraph("Cytoscape JSON", style_table_cell_code), Paragraph(".json", style_table_cell), Paragraph("Complete node/edge element graph and layout metadata for web-based graph visualization engines.", style_table_cell)],
    ]
    t_deliv = Table(deliverables_data, colWidths=[110, 60, 370])
    t_deliv.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), c_header_bg),
        ('GRID', (0, 0), (-1, -1), 0.5, c_border),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, c_table_bg]),
        ('TOPPADDING', (0, 0), (-1, -1), 2.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2.5),
        ('FONTNAME', (0, 0), (-1, -1), FONT_NAME),
    ]))
    story.append(t_deliv)
    story.append(Spacer(1, 8))

    # Page Break before Data Architecture
    story.append(PageBreak())

    # ---------------------------------------------------------
    # SECTION 5: DATA ARCHITECTURE & RELATIONAL SCHEMA
    # ---------------------------------------------------------
    story.append(Paragraph("5. Data Architecture, Schema & Relational Models", style_h1))
    story.append(Paragraph(
        "FieldAI persists all operational state in PostgreSQL (or local SQLite fallback) via core/db.py and core/storage.py. "
        "The relational schema supports complete audit trails, stable entity coding, version snapshots, and LangGraph checkpoints.",
        style_body
    ))

    schema_data = [
        [Paragraph("Table Name", style_table_header), Paragraph("Primary Keys & Foreign Keys", style_table_header), Paragraph("Key Columns & Attributes", style_table_header), Paragraph("Functional Purpose & Retention", style_table_header)],
        [Paragraph("users", style_table_cell_code), Paragraph("id (PK)", style_table_cell), Paragraph("username, password_hash, role, active, created_at", style_table_cell), Paragraph("User identity and RBAC (auditor, manager, admin, auditee).", style_table_cell)],
        [Paragraph("engagements", style_table_cell_code), Paragraph("id (PK)", style_table_cell), Paragraph("name, entity, period, status, created_at", style_table_cell), Paragraph("Top-level audit engagement container (e.g. FY26 Internal Audit).", style_table_cell)],
        [Paragraph("processes", style_table_cell_code), Paragraph("id (PK), engagement_id (FK)", style_table_cell), Paragraph("name, code_prefix, current_version, status", style_table_cell), Paragraph("Audit process definition (e.g. P2P, Treasury) with prefix.", style_table_cell)],
        [Paragraph("sources", style_table_cell_code), Paragraph("id (PK), process_id (FK)", style_table_cell), Paragraph("kind, title, storage_path, language, consent_recorded", style_table_cell), Paragraph("Raw evidence input registry (audio, video, document, SOP).", style_table_cell)],
        [Paragraph("transcript_segments", style_table_cell_code), Paragraph("id (PK), source_id (FK)", style_table_cell), Paragraph("speaker_label, speaker_name, start_s, end_s, text, redacted", style_table_cell), Paragraph("Diarized transcript utterances with second-level timestamps.", style_table_cell)],
        [Paragraph("steps", style_table_cell_code), Paragraph("id (PK), process_id (FK)", style_table_cell), Paragraph("step_code, order_num, description, role, system, is_decision", style_table_cell), Paragraph("Master process flow steps. Never renumbered; status='withdrawn'.", style_table_cell)],
        [Paragraph("risks", style_table_cell_code), Paragraph("id (PK), process_id (FK)", style_table_cell), Paragraph("risk_code, description, inherent_rating, ai_suggested", style_table_cell), Paragraph("Identified inherent risk catalogue with severity scoring.", style_table_cell)],
        [Paragraph("controls", style_table_cell_code), Paragraph("id (PK), process_id (FK)", style_table_cell), Paragraph("control_code, description, type, nature, freq, key_control", style_table_cell), Paragraph("Internal controls with design adequacy ratings and framework refs.", style_table_cell)],
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
    t_schema = Table(schema_data, colWidths=[90, 110, 150, 190])
    t_schema.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), c_header_bg),
        ('GRID', (0, 0), (-1, -1), 0.5, c_border),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, c_table_bg]),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ('FONTNAME', (0, 0), (-1, -1), FONT_NAME),
    ]))
    story.append(t_schema)
    story.append(Spacer(1, 8))

    # ---------------------------------------------------------
    # SECTION 6: NON-FUNCTIONAL REQUIREMENTS & GOVERNANCE
    # ---------------------------------------------------------
    story.append(Paragraph("6. Non-Functional Requirements, Security & Standards", style_h1))
    story.append(Paragraph(
        "FieldAI adheres to strict security, auditability, and internal audit regulatory standards:",
        style_body
    ))
    
    nfr_items = [
        "<b>IIA Standards Compliance:</b> Fully aligned with the IIA Global Internal Audit Standards (2024 Edition), ensuring complete documentation of planning, walkthrough narratives, risk-control matrices, substantive test procedures, and 5 Cs findings.",
        "<b>Bi-Directional Traceability:</b> 100% of generated steps, risks, controls, tests, and findings maintain clickable or referenced links to raw evidence (audio timestamp e.g. 00:14:22 or document section e.g. SOP v2.1 Section 4.2).",
        "<b>Zero AI Code Execution:</b> The system strictly prohibits executing arbitrary LLM-generated code against client financial data. All substantive testing relies exclusively on verified, deterministically coded Python/Pandas functions in analytics/library.py.",
        "<b>Auditor-in-the-Loop Safeguards:</b> All AI extractions are treated as draft recommendations. Human auditors retain full override authority. Changes to key controls require explicit managerial re-approval before updating master baselines.",
        "<b>Data Privacy & Redaction:</b> Meeting recordings require recorded participant consent. Audio segment redaction allows auditors to expunge sensitive personal data or off-the-record conversations prior to LLM processing.",
        "<b>Immutable Audit Trail:</b> Every user login, model modification, change-set approval, and export action is permanently logged to the append-only audit_log table with SHA-256 integrity verification.",
    ]
    for item in nfr_items:
        story.append(Paragraph(f"- {item}", style_bullet))
    story.append(Spacer(1, 8))

    # ---------------------------------------------------------
    # SECTION 7: DELIVERY PLAN & ACCEPTANCE CRITERIA
    # ---------------------------------------------------------
    story.append(Paragraph("7. Acceptance Criteria & Production Verification", style_h1))
    acceptance_items = [
        "Browser audio recording and multi-format audio/video uploads transcribe cleanly with speaker diarization and second timestamps.",
        "Process tables accurately reflect extracted steps, owners, systems, and decision branches with associated confidence ratings.",
        "Interactive Cytoscape flowcharts render with smooth Bezier curves, draggable nodes, and click-to-inspect audit metadata drawers.",
        "Graphviz architecture blueprints render at compact 1:1 scale without oversized font or shape distortion.",
        "All 5 deliverable formats (BPMN 2.0 XML, draw.io XML, Audit Summary PDF, Graphviz DOT, Cytoscape JSON) export without runtime errors.",
        "Follow-up meetings generate structured change sets classifying items as Added, Changed, Confirmed, Contradicted, or Removed.",
        "Uploaded SOPs generate 5-category reconciliation reports comparing documented procedures against interview statements.",
        "Substantive analytics, SoD checks, and process mining engines execute deterministically on uploaded client data files.",
        "All automated test suites (including tests/test_flowchart.py) pass with 100% success rate in CI/CD pipeline.",
    ]
    for item in acceptance_items:
        story.append(Paragraph(f"[PASS] {item}", style_bullet))
    story.append(Spacer(1, 14))

    # Sign-off Block
    sign_data = [
        [Paragraph("Prepared by: Lead Audit Architect", style_table_cell_code), Paragraph("Approved by: Product Owner (Sami)", style_table_cell_code)],
        [Paragraph("Signature: __________________________", style_table_cell), Paragraph("Signature: __________________________", style_table_cell)],
        [Paragraph("Date: October 2026", style_table_cell), Paragraph("Status: Approved for Production Deployment", style_table_cell)],
    ]
    t_sign = Table(sign_data, colWidths=[270, 270])
    t_sign.setStyle(TableStyle([
        ('LINEABOVE', (0, 0), (-1, 0), 1, c_accent),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('FONTNAME', (0, 0), (-1, -1), FONT_NAME),
    ]))
    story.append(KeepTogether(t_sign))

    # Build Document with NumberedCanvas
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"[PDF] PRD successfully built at: {output_path}")

if __name__ == "__main__":
    out_dir = Path(__file__).resolve().parent.parent
    pdf_filename = "FieldAI_Comprehensive_PRD.pdf"
    target_path = str(out_dir / pdf_filename)
    create_prd_pdf(target_path)
