import streamlit as st
from core.db import db
from core.model_repo import get_process, get_process_master_model
from core.storage import save_generated_document
from core.agent_registry import render_deliverable_attribution
from core.ui import apply_inter_theme
from agents.flowchart_agent import generate_dot, generate_cytoscape_elements
from analytics.flowchart_viewer import render_interactive_cytoscape
from exports.bpmn import export_bpmn_xml
from exports.drawio import export_drawio_xml
from exports.pdf import export_process_summary_pdf
import json

st.set_page_config(page_title="Flowchart & Swimlanes · FieldAI", page_icon="🗺️", layout="wide")
apply_inter_theme()

if not st.session_state.get("user"):
    st.warning("Please sign in from the main page.")
    st.stop()

user = st.session_state.user
process_id = st.session_state.get("current_process_id", 1)
proc = get_process(process_id)
model = get_process_master_model(process_id)

st.title("🗺️ Process Flowchart & Swimlanes")
st.caption(f"Visual audit workflow for **{proc['name'] if proc else 'Process'}** ({proc['current_version'] if proc else 'v1.0'}) with risk & control badges")
render_deliverable_attribution("flowchart_agent", "Multi-Lane Swimlane Diagram & BPMN 2.0 Deliverables")

steps = model.get("steps", [])
risks = model.get("risks", [])
controls = model.get("controls", [])

if not steps:
    st.info("No steps available to generate flowchart. Capture a walkthrough meeting or upload documents first.")
    st.stop()

# Controls & Configuration Bar
st.markdown("##### ⚙️ Flowchart Layout & Engineering Settings")
col_c1, col_c2, col_c3, col_c4, col_c5 = st.columns(5)

with col_c1:
    lane_mode = st.selectbox("Swimlane Grouping", options=["Role (responsible_role)", "Department (department)", "System (system)"], index=0)
    lane_key = "role" if "Role" in lane_mode else ("department" if "Department" in lane_mode else "system")

with col_c2:
    orientation = st.selectbox("Flow Orientation", options=["Top-to-Bottom (TB)", "Left-to-Right (LR)"], index=0)
    orient_key = "TB" if "TB" in orientation else "LR"

with col_c3:
    detail_mode = st.selectbox("Node Detail Level", options=["Compact Summary (BPMN Style)", "Full Operational Narrative"], index=0)
    is_compact = "Compact" in detail_mode

with col_c4:
    spline_choice = st.selectbox("Graphviz Line Routing", options=["Smooth Splines (No Overlaps)", "Polyline Curves", "Orthogonal (Grid)"], index=0)
    spline_key = "spline" if "Smooth" in spline_choice else ("polyline" if "Polyline" in spline_choice else "ortho")

with col_c5:
    cy_curve = st.selectbox("Cytoscape Curve Style", options=["Smooth Bézier (bezier)", "Unbundled Bézier (unbundled-bezier)", "Taxi Curves (taxi)"], index=0)
    cy_curve_key = "bezier" if "Smooth" in cy_curve else ("unbundled-bezier" if "Unbundled" in cy_curve else "taxi")

diff_mode = st.checkbox("🔍 Version Diff Mode (Highlight Withdrawn Items)", value=False)

# Generate models for all engines
cy_elements = generate_cytoscape_elements(
    process_name=proc["name"] if proc else "Audit Process",
    version=proc["current_version"] if proc else "v1.0",
    steps=steps,
    risks=risks,
    controls=controls,
    lane_by=lane_key,
    compact=is_compact
)

dot_code = generate_dot(
    process_name=proc["name"] if proc else "Audit Process",
    version=proc["current_version"] if proc else "v1.0",
    steps=steps,
    risks=risks,
    controls=controls,
    lane_by=lane_key,
    orientation=orient_key,
    diff_mode=diff_mode,
    spline_type=spline_key,
    compact=is_compact
)

st.markdown("---")

tab_cytoscape, tab_graphviz = st.tabs([
    "⚡ Cytoscape Interactive Canvas (Curved Béziers & Draggable)",
    "📐 Blueprint View (Refined Graphviz)"
])

with tab_cytoscape:
    st.markdown("#### ⚡ Cytoscape.js Process Flow Canvas (Dagre + Bézier Curves)")
    st.caption("Draggable nodes, obstacle-aware smooth curved lines, small Inter font styling, and click-to-inspect audit drawer.")
    render_interactive_cytoscape(cy_elements, orientation=orient_key, curve_style=cy_curve_key, height=650)

with tab_graphviz:
    st.markdown("#### 📐 High-Fidelity Graphviz Architecture Blueprint")
    st.caption("Rendered via Graphviz with smooth spline routing, left-aligned swimlane headers, word-wrapped nodes, and proportional decision diamonds.")
    st.graphviz_chart(dot_code, use_container_width=True)

st.divider()

# Diagram Exports
st.subheader("📥 Export Deliverables")
st.caption("Download flowcharts in standard editable engineering and diagramming formats:")

exp1, exp2, exp3, exp4, exp5, exp6 = st.columns(6)

with exp1:
    bpmn_xml = export_bpmn_xml(
        process_name=proc["name"] if proc else "Process",
        steps=steps,
        lane_attribute="responsible_role" if lane_key == "role" else ("department" if lane_key == "department" else "system")
    )
    save_generated_document(
        filename=f"{proc.get('code_prefix', 'PROC')}_flow.bpmn",
        mime_type="application/xml",
        data=bpmn_xml.encode("utf-8"),
        process_id=process_id,
        created_by=user["id"]
    )
    st.download_button(
        "BPMN 2.0 XML (.bpmn)",
        data=bpmn_xml,
        file_name=f"{proc.get('code_prefix', 'PROC')}_flow.bpmn",
        mime="application/xml",
        use_container_width=True
    )

with exp2:
    drawio_xml = export_drawio_xml(
        process_name=proc["name"] if proc else "Process",
        steps=steps,
        lane_attribute="responsible_role" if lane_key == "role" else ("department" if lane_key == "department" else "system")
    )
    save_generated_document(
        filename=f"{proc.get('code_prefix', 'PROC')}_flow.drawio",
        mime_type="application/xml",
        data=drawio_xml.encode("utf-8"),
        process_id=process_id,
        created_by=user["id"]
    )
    st.download_button(
        "draw.io / Diagrams (.drawio)",
        data=drawio_xml,
        file_name=f"{proc.get('code_prefix', 'PROC')}_flow.drawio",
        mime="application/xml",
        use_container_width=True,
        help="Open in draw.io or convert to Visio .vsdx via draw.io (File → Export as → VSDX)"
    )

with exp3:
    pdf_bytes = export_process_summary_pdf(
        process_name=proc["name"] if proc else "Process",
        version=proc["current_version"] if proc else "v1.0",
        steps=steps,
        risks=risks,
        controls=controls
    )
    save_generated_document(
        filename=f"{proc.get('code_prefix', 'PROC')}_Summary.pdf",
        mime_type="application/pdf",
        data=pdf_bytes,
        process_id=process_id,
        created_by=user["id"]
    )
    st.download_button(
        "Audit Summary PDF (.pdf)",
        data=pdf_bytes,
        file_name=f"{proc.get('code_prefix', 'PROC')}_Summary.pdf",
        mime="application/pdf",
        use_container_width=True
    )

with exp4:
    st.download_button(
        "Mermaid (.mmd)",
        data=mermaid_code,
        file_name=f"{proc.get('code_prefix', 'PROC')}_flow.mmd",
        mime="text/plain",
        use_container_width=True
    )

with exp5:
    st.download_button(
        "Graphviz DOT (.dot)",
        data=dot_code,
        file_name=f"{proc.get('code_prefix', 'PROC')}_flow.dot",
        mime="text/vnd.graphviz",
        use_container_width=True
    )

with exp6:
    st.download_button(
        "Cytoscape (.json)",
        data=json.dumps(cy_elements, indent=2),
        file_name=f"{proc.get('code_prefix', 'PROC')}_flow.json",
        mime="application/json",
        use_container_width=True
    )
