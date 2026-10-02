import streamlit as st
from core.db import db
from core.model_repo import get_process
from graphs.orchestrator import run_task

st.set_page_config(page_title="Meeting Preparation · FieldAI", page_icon="📋", layout="wide")

if not st.session_state.get("user"):
    st.warning("Please sign in from the main page.")
    st.stop()

user = st.session_state.user
process_id = st.session_state.get("current_process_id", 1)
proc = get_process(process_id)

st.title("📋 Walkthrough Preparation & Scoping")
st.caption(f"Pre-meeting question pack and risk-based scoping for **{proc['name'] if proc else 'Process'}** ({proc['current_version'] if proc else 'v1.0'})")

col_btn1, col_btn2 = st.columns([1, 1.5])
with col_btn1:
    if st.button("⚡ Generate Bilingual Walkthrough Question Pack", type="primary", use_container_width=True):
        with st.spinner("Analyzing open items, risk library, and building question pack..."):
            prep_res = run_task("prep_meeting", {
                "process_id": process_id,
                "user_id": user["id"]
            })
            st.session_state.prep_res = prep_res.get("prep_package", {})
            st.success("Question pack generated successfully!")

prep_data = st.session_state.get("prep_res")

if prep_data:
    st.divider()
    scoping = prep_data.get("scoping", {})
    s1, s2, s3 = st.columns(3)
    with s1:
        st.metric("Inherent Process Risk", scoping.get("inherent_risk_score", "High"))
    with s2:
        st.metric("Indicative Fieldwork Hours", f"{scoping.get('indicative_hours', 80)} hrs")
    with s3:
        st.metric("Focus Areas Count", len(scoping.get("recommended_scope_areas", [])))

    st.markdown("#### 🎯 Recommended Audit Focus Areas:")
    for a in scoping.get("recommended_scope_areas", []):
        st.markdown(f"- **{a}**")

    st.divider()
    st.subheader("🌐 Bilingual Walkthrough Question Pack (Arabic & English)")
    
    questions = prep_data.get("question_pack", [])
    for idx, q in enumerate(questions, 1):
        with st.expander(f"Question {idx}: {q.get('phase', 'General')} – {q.get('question_en', '')}"):
            col_en, col_ar = st.columns(2)
            with col_en:
                st.markdown(f"**English:** {q.get('question_en', '')}")
                st.caption(f"**Audit Objective:** {q.get('objective', '')}")
            with col_ar:
                st.markdown(f"<div style='text-align: right; direction: rtl;'><b>العربية:</b> {q.get('question_ar', '')}</div>", unsafe_allow_html=True)
                st.caption(f"**Expected Evidence / PBC:** {q.get('expected_evidence', '')}")
else:
    st.info("Click the button above to generate a tailored walkthrough question pack based on process risks and open items.")
