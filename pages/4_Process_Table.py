import streamlit as st
import pandas as pd
from core.db import db
from core.model_repo import get_process, get_active_steps
from core.agent_registry import render_deliverable_attribution
from exports.excel import export_process_table_excel
from graphs.orchestrator import run_task

st.set_page_config(page_title="Process Table · FieldAI", page_icon="📋", layout="wide")

if not st.session_state.get("user"):
    st.warning("Please sign in from the main page.")
    st.stop()

user = st.session_state.user
process_id = st.session_state.get("current_process_id", 1)
proc = get_process(process_id)

st.title("📋 Master Process Table")
st.caption(f"Sequential business steps and responsibility matrix for **{proc['name'] if proc else 'Process'}** ({proc['current_version'] if proc else 'v1.0'})")
render_deliverable_attribution("process_extraction_agent", "Sequential Process Steps & Responsibility Allocation")

steps = get_active_steps(process_id)

if not steps:
    st.info("No active process steps recorded. Capture a meeting or upload an SOP to extract steps.")
    st.stop()

col_tools1, col_tools2 = st.columns([1, 1])
with col_tools1:
    st.write(f"**Total Active Steps:** {len(steps)}")
with col_tools2:
    excel_bytes = export_process_table_excel(steps)
    st.download_button(
        "📥 Export Process Table (Excel .xlsx)",
        data=excel_bytes,
        file_name=f"{proc.get('code_prefix', 'PROC')}_Process_Table_{proc.get('current_version', 'v1.0')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

df_steps = pd.DataFrame(steps)
display_cols = [
    "step_code", "order_num", "description", "responsible_role", 
    "department", "system", "frequency", "is_decision", "confidence"
]
df_edit = df_steps[[c for c in display_cols if c in df_steps.columns]].copy()

edited_df = st.data_editor(
    df_edit,
    use_container_width=True,
    num_rows="dynamic",
    column_config={
        "step_code": st.column_config.TextColumn("Step Code", disabled=True),
        "order_num": st.column_config.NumberColumn("Order", min_value=1, step=1),
        "description": st.column_config.TextColumn("Step Description", width="large"),
        "responsible_role": st.column_config.TextColumn("Role"),
        "department": st.column_config.TextColumn("Department"),
        "system": st.column_config.TextColumn("System"),
        "frequency": st.column_config.SelectboxColumn("Frequency", options=["per transaction", "daily", "weekly", "monthly", "quarterly", "annual"]),
        "is_decision": st.column_config.CheckboxColumn("Decision Point?"),
        "confidence": st.column_config.ProgressColumn("Confidence", min_value=0.0, max_value=1.0, format="%.2f")
    }
)

if st.button("💾 Save Changes & Rebuild Deliverables", type="primary"):
    with st.spinner("Saving changes and updating flowchart..."):
        for _, row in edited_df.iterrows():
            db.execute(
                """
                UPDATE steps 
                SET order_num = %s, description = %s, responsible_role = %s, 
                    department = %s, system = %s, frequency = %s, is_decision = %s
                WHERE process_id = %s AND step_code = %s;
                """,
                (
                    row.get("order_num", 1), row.get("description", ""), row.get("responsible_role", ""),
                    row.get("department", ""), row.get("system", ""), row.get("frequency", "per transaction"),
                    row.get("is_decision", False), process_id, row.get("step_code")
                )
            )
        # Trigger deliverables graph rebuild
        run_task("rebuild_deliverables", {
            "process_id": process_id,
            "user_id": user["id"]
        })
        st.success("Changes saved successfully and flowchart regenerated!")
        st.rerun()
