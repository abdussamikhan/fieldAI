import streamlit as st
from core.db import db
from core.model_repo import get_process, get_process_master_model
from core.ui import apply_inter_theme
from agents.flowchart_agent import generate_dot

st.set_page_config(page_title="Auditee Confirmation Portal · FieldAI", page_icon="🤝", layout="wide")
apply_inter_theme()

st.title("🤝 Auditee Process Confirmation Portal (Option 16)")
st.caption("Secure, read-only walkthrough confirmation interface for client process owners and auditees.")

process_id = st.session_state.get("current_process_id", 1)
proc = get_process(process_id)
model = get_process_master_model(process_id)

st.info(f"You are reviewing documented business process: **{proc['name'] if proc else 'Procure-to-Pay'}** (Baseline {proc['current_version'] if proc else 'v1.0'}). Please confirm accuracy or submit clarification notes.")

# Render read-only flowchart
steps = model.get("steps", [])
risks = model.get("risks", [])
controls = model.get("controls", [])

if steps:
    dot_code = generate_dot(
        process_name=proc["name"] if proc else "Audit Process",
        version=proc["current_version"] if proc else "v1.0",
        steps=steps,
        risks=risks,
        controls=controls,
        lane_by="role"
    )
    st.graphviz_chart(dot_code, use_container_width=True)

st.divider()

col_conf1, col_conf2 = st.columns([1.2, 1.8])

with col_conf1:
    st.subheader("Process Confirmation")
    auditee_name = st.text_input("Your Name & Role", value="Sarah Jenkins (Operations Head)")
    confirm_choice = st.radio("Confirmation Status", [
        "✅ I confirm this process flow and controls accurately reflect our operational practice.",
        "⚠️ I have corrections or clarification notes regarding specific steps."
    ])

with col_conf2:
    st.subheader("Clarification Notes")
    comments = st.text_area("Specific Feedback / Corrections", placeholder="e.g. In step 2, approval threshold was changed to $15k last month...")
    
    if st.button("Submit Confirmation / Feedback", type="primary"):
        db.execute_insert(
            """
            INSERT INTO review_notes (process_id, target_entity, note, status)
            VALUES (%s, 'auditee_confirmation', %s, 'open');
            """,
            (process_id, f"Auditee [{auditee_name}]: {confirm_choice} | Notes: {comments}")
        )
        st.success("Thank you! Your feedback has been officially logged in the audit workpapers.")
