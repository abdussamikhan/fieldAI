import streamlit as st
import pandas as pd
from core.db import db
from core.model_repo import get_process
from core.audit_log import log_audit
from exports.excel import export_audit_program_excel

st.set_page_config(page_title="Audit Program · FieldAI", page_icon="📜", layout="wide")

if not st.session_state.get("user"):
    st.warning("Please sign in from the main page.")
    st.stop()

user = st.session_state.user
process_id = st.session_state.get("current_process_id", 1)
proc = get_process(process_id)

st.title("📜 Audit Program & Testing Procedures")
st.caption(f"Detailed fieldwork test procedures, sample sizes, and PBC evidence requirements for **{proc['name'] if proc else 'Process'}** ({proc['current_version'] if proc else 'v1.0'})")

tests = db.fetch_all("SELECT * FROM tests WHERE process_id = %s ORDER BY id ASC;", (process_id,))

if not tests:
    st.info("No audit tests generated yet. Rebuild deliverables from Process Table or RCM.")
    st.stop()

col_t1, col_t2 = st.columns([1, 1])
with col_t1:
    st.write(f"**Total Audit Test Steps:** {len(tests)}")
with col_t2:
    excel_tests = export_audit_program_excel(tests)
    st.download_button(
        "📥 Export Audit Program to Excel (.xlsx)",
        data=excel_tests,
        file_name=f"{proc.get('code_prefix', 'PROC')}_Audit_Program_{proc.get('current_version', 'v1.0')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

st.divider()

# Test steps editor / viewer
df_tests = pd.DataFrame(tests)
display_cols = ["test_code", "control_code", "objective", "test_type", "procedure", "sample_size", "evidence_pbc", "result", "status"]
df_edit = df_tests[[c for c in display_cols if c in df_tests.columns]].copy()

edited_tests = st.data_editor(
    df_edit,
    use_container_width=True,
    column_config={
        "test_code": st.column_config.TextColumn("Test ID", disabled=True),
        "control_code": st.column_config.TextColumn("Control ID", disabled=True),
        "objective": st.column_config.TextColumn("Objective", width="medium"),
        "test_type": st.column_config.SelectboxColumn("Type", options=["ToE", "ToD", "analytics"]),
        "procedure": st.column_config.TextColumn("Audit Procedure", width="large"),
        "sample_size": st.column_config.NumberColumn("Sample Size", min_value=1),
        "evidence_pbc": st.column_config.TextColumn("PBC Evidence", width="medium"),
        "result": st.column_config.SelectboxColumn("Result", options=["Untested", "Pass", "Exception", "Inconclusive"]),
        "status": st.column_config.SelectboxColumn("Status", options=["draft", "approved", "locked"])
    }
)

col_s1, col_s2 = st.columns([1, 1])
with col_s1:
    if st.button("💾 Save Test Results & Updates", type="primary"):
        for _, r in edited_tests.iterrows():
            db.execute(
                """
                UPDATE tests 
                SET objective = %s, test_type = %s, procedure = %s, sample_size = %s, 
                    evidence_pbc = %s, result = %s, status = %s
                WHERE process_id = %s AND test_code = %s;
                """,
                (
                    r.get("objective", ""), r.get("test_type", "ToE"), r.get("procedure", ""),
                    r.get("sample_size", 25), r.get("evidence_pbc", ""), r.get("result", "Untested"),
                    r.get("status", "draft"), process_id, r.get("test_code")
                )
            )
        st.success("Audit program updated successfully!")
        st.rerun()

with col_s2:
    if user["role"] in ("Manager", "Admin"):
        if st.button("🔒 Manager Approval & Lock Audit Program"):
            db.execute("UPDATE tests SET status = 'locked' WHERE process_id = %s;", (process_id,))
            log_audit(user["id"], "lock_audit_program", "process", process_id)
            st.success("Audit Program formally approved and locked by Audit Manager.")
            st.rerun()
