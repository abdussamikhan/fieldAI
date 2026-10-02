import streamlit as st
import pandas as pd
from core.db import db
from core.model_repo import get_process
from core.audit_log import log_audit
from exports.word import export_findings_word
from graphs.orchestrator import run_task

st.set_page_config(page_title="Findings & QA Review · FieldAI", page_icon="📝", layout="wide")

if not st.session_state.get("user"):
    st.warning("Please sign in from the main page.")
    st.stop()

user = st.session_state.user
process_id = st.session_state.get("current_process_id", 1)
proc = get_process(process_id)

st.title("📝 Audit Findings (5 Cs) & QA Review")
st.caption(f"Formal fieldwork findings and methodology quality assurance for **{proc['name'] if proc else 'Process'}**")

tab1, tab2 = st.tabs(["📑 Draft Findings (5 Cs)", "✅ Methodology & IIA QA Review"])

with tab1:
    col_f1, col_f2 = st.columns([1, 1.5])
    with col_f1:
        if st.button("⚡ Draft Findings from Fieldwork Exceptions", type="primary"):
            with st.spinner("Compiling test exceptions and drafting 5 Cs findings..."):
                f_res = run_task("draft_findings", {
                    "process_id": process_id,
                    "user_id": user["id"]
                })
                st.success("Draft findings generated successfully!")
                st.rerun()

    findings = db.fetch_all("SELECT * FROM findings WHERE process_id = %s ORDER BY id DESC;", (process_id,))

    if findings:
        with col_f2:
            word_findings = export_findings_word(findings)
            st.download_button(
                "📥 Export Findings to Word (.docx)",
                data=word_findings,
                file_name=f"{proc.get('code_prefix', 'PROC')}_Findings.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )

        st.divider()

        for idx, f in enumerate(findings, 1):
            rating = f.get("rating", "Medium")
            r_color = "#ef4444" if rating == "High" else ("#f59e0b" if rating == "Medium" else "#0284c7")
            status = f.get("status", "draft")

            with st.expander(f"Finding {idx} [{rating.upper()}]: {f.get('title', '')} ({status.upper()})", expanded=(idx == 1)):
                st.markdown(f"**Condition (What was found):**\n{f.get('condition_text', '')}")
                st.markdown(f"**Criteria (Policy / Standard):**\n{f.get('criteria_text', '')}")
                st.markdown(f"**Cause (Root cause):**\n{f.get('cause_text', '')}")
                st.markdown(f"**Effect (Risk / Impact):**\n{f.get('effect_text', '')}")
                st.markdown(f"**Recommendation:**\n{f.get('recommendation_text', '')}")
                st.caption(f"Linked Controls: `{f.get('linked_controls')}` | Linked Tests: `{f.get('linked_tests')}`")

                if user["role"] in ("Manager", "Admin") and status == "draft":
                    if st.button(f"Approve Finding {idx}", key=f"appr_{f['id']}"):
                        db.execute("UPDATE findings SET status = 'approved', approved_by = %s, approved_at = CURRENT_TIMESTAMP WHERE id = %s;", (user["id"], f["id"]))
                        log_audit(user["id"], "approve_finding", "finding", f["id"])
                        st.success("Finding approved!")
                        st.rerun()
    else:
        st.info("No findings logged yet. Click the button above to draft findings from identified exceptions.")

with tab2:
    st.subheader("✅ Quality Assurance (IIA Standards 2024 Checklist)")
    st.markdown("Automated quality review verifying file completeness against internal audit documentation standards.")

    if st.button("Run QA Review Check"):
        with st.spinner("Checking risk-control links, test coverage, and sign-offs..."):
            qa_res = run_task("qa_review", {
                "process_id": process_id,
                "user_id": user["id"]
            })
            st.session_state.qa_data = qa_res.get("qa_review", {})
            st.success("QA Inspection complete!")

    qa_data = st.session_state.get("qa_data")
    if qa_data:
        st.metric("Documentation Compliance Score", f"{qa_data.get('compliance_score', 90)}%")
        st.info(qa_data.get("summary", "Complete"))

        st.markdown("#### Review Notes:")
        notes = qa_data.get("review_notes", [])
        for n in notes:
            st.warning(f"📌 **{n.get('checklist_item')} ({n.get('target_code')}):** {n.get('note')}")
