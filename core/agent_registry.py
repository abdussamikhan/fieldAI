import streamlit as st
from typing import Dict, Any, List, Union

AGENTS_REGISTRY: Dict[str, Dict[str, Any]] = {
    "transcription_agent": {
        "name": "transcription_agent",
        "title": "Transcription & Diarization Agent",
        "code": "FR-1.x / Agent 01",
        "icon": "🎙️",
        "role": "Audio Ingestion & Speaker Diarization",
        "framework": "Faster-Whisper / STT Engine",
        "color": "#38bdf8",
        "deliverables": ["Verbatim Timestamped Transcripts", "Speaker Turn Diarization"]
    },
    "summary_agent": {
        "name": "summary_agent",
        "title": "Walkthrough Synthesis Agent",
        "code": "FR-2.x / Agent 02",
        "icon": "📝",
        "role": "Discussion Summarization & Action Item Capture",
        "framework": "DeepSeek / Audit Synthesis",
        "color": "#60a5fa",
        "deliverables": ["Executive Walkthrough Summary", "Key Decisions & Action Items", "Identified Open Questions", "Initial PBC List"]
    },
    "process_extraction_agent": {
        "name": "process_extraction_agent",
        "title": "Process Extraction Agent",
        "code": "FR-3.x / Agent 03",
        "icon": "⚙️",
        "role": "Sequential Process Step & Gateway Extraction",
        "framework": "DeepSeek / Structural Grammar",
        "color": "#34d399",
        "deliverables": ["Process Step Registry", "Decision Gateways", "Role & System Allocations"]
    },
    "risk_control_agent": {
        "name": "risk_control_agent",
        "title": "Risk & Control Mapping Agent",
        "code": "FR-4.x / Agent 04",
        "icon": "🛡️",
        "role": "Inherent Risk Identification & Control Activity Mapping",
        "framework": "COSO 2013 / NCA ECC / ISO 27001",
        "color": "#f59e0b",
        "deliverables": ["Inherent Risk Catalog", "Mitigating Control Activities", "COSO/NCA Standards Mapping"]
    },
    "change_set_agent": {
        "name": "change_set_agent",
        "title": "Entity Resolution & Change Set Agent",
        "code": "FR-5.x / Agent 05",
        "icon": "⚖️",
        "role": "Model Reconciliation & Version Diff Generation",
        "framework": "Deterministic Diff Engine",
        "color": "#a78bfa",
        "deliverables": ["Formal Change Set (Added/Changed/Confirmed/Removed)", "Contradiction Alerts", "Audit Version Diff"]
    },
    "flowchart_agent": {
        "name": "flowchart_agent",
        "title": "Flowchart & Swimlane Generation Agent",
        "code": "FR-6.1 / Agent 06",
        "icon": "🗺️",
        "role": "Multi-Lane Swimlane Diagram Synthesis",
        "framework": "Graphviz DOT & BPMN 2.0 Engine",
        "color": "#06b6d4",
        "deliverables": ["Interactive Graphviz Swimlanes", "BPMN 2.0 XML Schema", "draw.io / Visio XML Deliverable"]
    },
    "rcm_agent": {
        "name": "rcm_agent",
        "title": "RCM Compilation Agent",
        "code": "FR-6.2 / Agent 07",
        "icon": "📊",
        "role": "Risk-Control Matrix & Design Adequacy Evaluation",
        "framework": "IIA / COSO Frameworks",
        "color": "#f97316",
        "deliverables": ["RCM Matrix (Excel/Table)", "Control Design Adequacy Ratings", "Unmitigated Risk Gap Highlights"]
    },
    "audit_program_agent": {
        "name": "audit_program_agent",
        "title": "Audit Program & Testing Agent",
        "code": "FR-6.3 / Agent 08",
        "icon": "📜",
        "role": "Fieldwork Test Step & Deterministic Sample Size Formulation",
        "framework": "Deterministic Sampling Engine",
        "color": "#10b981",
        "deliverables": ["Fieldwork Audit Program (ToD & ToE)", "Sampling Table Allocations", "PBC Evidence Requirements"]
    },
    "knowledge_agent": {
        "name": "knowledge_agent",
        "title": "Audit Knowledge & Standards Agent",
        "code": "FR-6.5 / Agent 09",
        "icon": "📚",
        "role": "Internal Audit Guidance & Benchmark RAG Retrieval",
        "framework": "IIA GIAS / COSO / SAMA CSF",
        "color": "#6366f1",
        "deliverables": ["Regulatory Framework Citations", "Industry Control Benchmarks"]
    },
    "document_agent": {
        "name": "document_agent",
        "title": "Document Parsing & Ingestion Agent",
        "code": "FR-7.1 / Agent 10",
        "icon": "📄",
        "role": "Auditee Document Extraction & Text Chunking",
        "framework": "Document Chunking & Control Parser",
        "color": "#8b5cf6",
        "deliverables": ["Parsed Document Chunks", "Document Register Metadata", "Documented Control Catalog"]
    },
    "reconciliation_agent": {
        "name": "reconciliation_agent",
        "title": "Said vs Documented Reconciliation Agent",
        "code": "FR-7.2 / Agent 11",
        "icon": "⚖️",
        "role": "5-Category Interview vs Document Reconciliation",
        "framework": "Reconciliation Heuristics Engine",
        "color": "#ec4899",
        "deliverables": ["5-Category Reconciliation Matrix", "SOP Divergence Flags", "Unwritten Practice Warnings"]
    },
    "doc_qa_agent": {
        "name": "doc_qa_agent",
        "title": "In-Document Grounded Q&A Agent",
        "code": "FR-7.8 / Agent 12",
        "icon": "🔍",
        "role": "Grounded Inquiry Answering with Verified Source Citations",
        "framework": "Grounded Citation Engine",
        "color": "#14b8a6",
        "deliverables": ["Grounded Audit Answers", "Exact Page & Section Citations", "Verifiable Policy Excerpts"]
    },
    "prep_agent": {
        "name": "prep_agent",
        "title": "Walkthrough Preparation & Scoping Agent",
        "code": "FR-6.7 / Agent 13",
        "icon": "📋",
        "role": "Pre-Meeting Scoping & Bilingual Question Pack Generation",
        "framework": "DeepSeek Bilingual Audit Model",
        "color": "#f59e0b",
        "deliverables": ["Bilingual Interview Question Pack (EN & AR)", "Inherent Risk Scoping Metric", "Audit Focus Areas"]
    },
    "copilot_agent": {
        "name": "copilot_agent",
        "title": "Live Interview Co-Pilot Agent",
        "code": "FR-6.6 / Agent 14",
        "icon": "⚡",
        "role": "Near-Live Interview Audio Chunk Co-Pilot Prompts",
        "framework": "Real-Time Prompting Engine",
        "color": "#eab308",
        "deliverables": ["Live Follow-Up Interview Prompts", "Missing Control Checklists", "Instant Evidence Requests"]
    },
    "analytics_agent": {
        "name": "analytics_agent",
        "title": "Audit Analytics & Logic Agent",
        "code": "FR-8.1 / Agent 15",
        "icon": "📈",
        "role": "Deterministic Full-Population Data Analytics Tests",
        "framework": "Pandas & Python Audit Logic",
        "color": "#0284c7",
        "deliverables": ["Duplicate Payment Analysis", "Split Purchase Order Detection", "Weekend/After-Hours Invoicing", "Benford's Law Digital Analysis"]
    },
    "sod_agent": {
        "name": "sod_agent",
        "title": "Segregation of Duties (SoD) Agent",
        "code": "FR-8.2 / Agent 16",
        "icon": "🔀",
        "role": "Matrix Rule Evaluation for Incompatible ERP Permissions",
        "framework": "SoD Conflict Matrix Engine",
        "color": "#ef4444",
        "deliverables": ["SoD Toxic Pair Violation Catalog", "User Conflict Risk Scores"]
    },
    "process_mining_agent": {
        "name": "process_mining_agent",
        "title": "Process Mining & Conformance Agent",
        "code": "FR-8.3 / Agent 17",
        "icon": "🌀",
        "role": "ERP Event Log Path Variance & Bottleneck Mining",
        "framework": "Event Conformance Engine",
        "color": "#d946ef",
        "deliverables": ["Process Variant Analysis", "Happy Path Deviation Ratios", "Cycle Time Bottleneck Analytics"]
    },
    "evidence_agent": {
        "name": "evidence_agent",
        "title": "Evidence Verification & Reading Agent",
        "code": "FR-8.4 / Agent 18",
        "icon": "🔎",
        "role": "Sample Voucher & Document Attribute Matching",
        "framework": "Voucher OCR & Attribute Matcher",
        "color": "#0ea5e9",
        "deliverables": ["Sample Voucher Attribute Verification", "Sign-Off Signature Validation"]
    },
    "findings_agent": {
        "name": "findings_agent",
        "title": "Findings & Observations Formulation Agent",
        "code": "FR-9.1 / Agent 19",
        "icon": "⚠️",
        "role": "Standard 5 Cs (Criteria, Condition, Cause, Consequence, Corrective Action) Formulation",
        "framework": "IIA 5 Cs Audit Standards",
        "color": "#dc2626",
        "deliverables": ["Structured 5 Cs Audit Findings", "Residual Severity Ratings", "Practical Remediation Recommendations"]
    },
    "qa_review_agent": {
        "name": "qa_review_agent",
        "title": "Independent QA & Methodology Review Agent",
        "code": "FR-9.2 / Agent 20",
        "icon": "🎯",
        "role": "Quality Assurance Checklist & Constructive Critique",
        "framework": "IIA Quality Assessment Framework",
        "color": "#84cc16",
        "deliverables": ["Audit Working Paper Review Notes", "Methodology Compliance Checklists"]
    },
    "monitoring_agent": {
        "name": "monitoring_agent",
        "title": "CAE Continuous Monitoring Agent",
        "code": "FR-10.x / Agent 21",
        "icon": "📊",
        "role": "Executive Audit Metrics & Real-Time Telemetry Synthesis",
        "framework": "Executive Analytics Engine",
        "color": "#06b6d4",
        "deliverables": ["CAE Executive Heat Maps", "Continuous Exception Feeds", "Audit Plan Progress Telemetry"]
    }
}

def get_agent_info(agent_name: str) -> Dict[str, Any]:
    """Retrieves agent metadata, falling back to a clean default if not found."""
    return AGENTS_REGISTRY.get(agent_name, {
        "name": agent_name,
        "title": agent_name.replace("_", " ").title(),
        "code": "FieldAI Agent",
        "icon": "🤖",
        "role": "Audit Task Execution",
        "framework": "FieldAI Multi-Agent Core",
        "color": "#38bdf8",
        "deliverables": ["Audit Deliverable"]
    })

def render_active_agent_pill(agent_name: str, activity_text: str = ""):
    """Renders a sleek live pulse banner indicating the agent actively executing the screen task."""
    info = get_agent_info(agent_name)
    color = info.get("color", "#38bdf8")
    activity = activity_text or f"Executing {info['role']}..."
    st.markdown(
        f"""
        <div style="background: rgba(15, 23, 42, 0.7); border: 1px solid {color}55; border-left: 4px solid {color}; border-radius: 8px; padding: 10px 16px; margin-bottom: 16px; display: flex; align-items: center; justify-content: space-between;">
            <div style="display: flex; align-items: center; gap: 10px;">
                <span style="font-size: 1.3rem;">{info['icon']}</span>
                <div>
                    <span style="color: #94a3b8; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.05em; font-weight: 600;">Active Agent</span>
                    <div style="color: #f8fafc; font-weight: 700; font-size: 0.95rem;">
                        {info['title']} <span style="font-size: 0.8rem; color: {color}; font-weight: normal;">({info['code']})</span>
                    </div>
                </div>
            </div>
            <div style="text-align: right;">
                <span style="color: #cbd5e1; font-size: 0.85rem; font-style: italic;">{activity}</span>
                <span style="display: inline-block; width: 8px; height: 8px; background-color: {color}; border-radius: 50%; margin-left: 8px; animation: pulse 1.5s infinite;"></span>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

def render_deliverable_attribution(
    agent_names: Union[str, List[str]],
    deliverable_title: str = "Deliverable",
    version: str = "",
    note: str = ""
):
    """
    Renders an attribution badge identifying the specific agent(s) who delivered the artifact shown on screen.
    """
    if isinstance(agent_names, str):
        agent_names = [agent_names]

    badges = []
    for a in agent_names:
        info = get_agent_info(a)
        color = info.get("color", "#38bdf8")
        badges.append(
            f"""<span style="background-color: {color}22; border: 1px solid {color}66; color: {color}; padding: 3px 8px; border-radius: 4px; font-size: 0.8rem; font-weight: 600; display: inline-flex; align-items: center; gap: 4px;">
                {info['icon']} {info['title']}
            </span>"""
        )

    badges_html = " ".join(badges)
    ver_html = f"<span style='color: #64748b; font-size: 0.8rem; margin-left: 6px;'>• {version}</span>" if version else ""
    note_html = f"<div style='color: #94a3b8; font-size: 0.78rem; margin-top: 4px;'>{note}</div>" if note else ""

    st.markdown(
        f"""
        <div style="background: rgba(30, 41, 59, 0.4); border: 1px dashed rgba(148, 163, 184, 0.25); border-radius: 6px; padding: 8px 14px; margin-top: 8px; margin-bottom: 14px;">
            <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 8px;">
                <div style="display: flex; align-items: center; gap: 8px;">
                    <span style="color: #94a3b8; font-size: 0.8rem; font-weight: 600;">🤖 Delivered by:</span>
                    {badges_html}
                    {ver_html}
                </div>
                <div style="color: #10b981; font-size: 0.75rem; font-weight: 600; display: flex; align-items: center; gap: 4px;">
                    <span>✓</span> Grounded & Validated
                </div>
            </div>
            {note_html}
        </div>
        """,
        unsafe_allow_html=True
    )
