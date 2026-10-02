import streamlit as st
from core.db import db
from core.model_repo import get_process, get_process_master_model
from core.storage import save_generated_document
from core.agent_registry import render_deliverable_attribution
from agents.flowchart_agent import generate_dot
from exports.bpmn import export_bpmn_xml
from exports.drawio import export_drawio_xml
from exports.pdf import export_process_summary_pdf

st.set_page_config(page_title="Flowchart & Swimlanes · FieldAI", page_icon="🗺️", layout="wide")

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
col_c1, col_c2, col_c3 = st.columns([1, 1, 1])

with col_c1:
    lane_mode = st.selectbox("Swimlane Layout", options=["Role (responsible_role)", "Department (department)", "System (system)"], index=0)
    lane_key = "role" if "Role" in lane_mode else ("department" if "Department" in lane_mode else "system")

with col_c2:
    orientation = st.selectbox("Flow Orientation", options=["Top-to-Bottom (TB)", "Left-to-Right (LR)"], index=0)
    orient_key = "TB" if "TB" in orientation else "LR"

with col_c3:
    diff_mode = st.checkbox("🔍 Version Diff Mode (Show Withdrawn Items)", value=False)

# Generate DOT diagram
dot_code = generate_dot(
    process_name=proc["name"] if proc else "Audit Process",
    version=proc["current_version"] if proc else "v1.0",
    steps=steps,
    risks=risks,
    controls=controls,
    lane_by=lane_key,
    orientation=orient_key,
    diff_mode=diff_mode
)

# Render Graphviz Flowchart in browser
st.markdown("### 📊 Interactive Flow Diagram")
st.graphviz_chart(dot_code, use_container_width=True)

st.divider()

# Diagram Exports
st.subheader("📥 Export Deliverables")
st.caption("Download flowcharts in standard editable engineering and diagramming formats:")

exp1, exp2, exp3, exp4 = st.columns(4)

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
        "Graphviz DOT (.dot)",
        data=dot_code,
        file_name=f"{proc.get('code_prefix', 'PROC')}_flow.dot",
        mime="text/vnd.graphviz",
        use_container_width=True
    )
