import streamlit as st
import pandas as pd
from core.db import db
from core.model_repo import get_process, get_process_master_model
from core.storage import save_generated_document
from core.agent_registry import render_deliverable_attribution
from core.ui import apply_inter_theme
from exports.excel import export_rcm_excel

st.set_page_config(page_title="Risk-Control Matrix · FieldAI", page_icon="🛡️", layout="wide")
apply_inter_theme()

if not st.session_state.get("user"):
    st.warning("Please sign in from the main page.")
    st.stop()

user = st.session_state.user
process_id = st.session_state.get("current_process_id", 1)
proc = get_process(process_id)
model = get_process_master_model(process_id)

st.title("🛡️ Risk & Control Matrix (RCM)")
st.caption(f"Comprehensive internal control matrix and design adequacy evaluations for **{proc['name'] if proc else 'Process'}** ({proc['current_version'] if proc else 'v1.0'})")
render_deliverable_attribution(["rcm_agent", "risk_control_agent"], "Risk & Control Matrix & Control Design Adequacy Ratings")

risks = model.get("risks", [])
controls = model.get("controls", [])

if not risks and not controls:
    st.info("No risks or controls logged yet. Complete meeting capture or document ingestion first.")
    st.stop()

# Build RCM combined view
rcm_rows = []
ctrl_map = {c.get("control_code"): c for c in controls}

for r in risks:
    c_codes = r.get("control_codes", [])
    if c_codes:
        for c_code in c_codes:
            c = ctrl_map.get(c_code, {})
            rcm_rows.append({
                "risk_code": r.get("risk_code"),
                "risk_description": r.get("description"),
                "inherent_rating": r.get("inherent_rating", "Medium"),
                "control_code": c_code,
                "control_description": c.get("description", ""),
                "control_type": c.get("type", "preventive"),
                "nature": c.get("nature", "automated"),
                "frequency": c.get("frequency", "per transaction"),
                "owner": c.get("owner", ""),
                "key_control": c.get("key_control", True),
                "design_rating": c.get("design_rating", "Adequate"),
                "criteria_ref": c.get("criteria_ref", "SOP-FIN-04 §3"),
                "framework_refs": ["COSO Principle 10", "ISO 27001 A.5.15"]
            })
    else:
        # Unmitigated Risk Gap
        rcm_rows.append({
            "risk_code": r.get("risk_code"),
            "risk_description": r.get("description"),
            "inherent_rating": r.get("inherent_rating", "High"),
            "control_code": "GAP / UNMITIGATED",
            "control_description": "⚠️ No mitigating control mapped! Propose control from library.",
            "control_type": "-",
            "nature": "-",
            "frequency": "-",
            "owner": "Unassigned",
            "key_control": False,
            "design_rating": "Inadequate",
            "criteria_ref": "-",
            "framework_refs": []
        })

col_t1, col_t2 = st.columns([1, 1])
with col_t1:
    st.write(f"**Total Mapped Control Activities:** {len(rcm_rows)}")
with col_t2:
    excel_rcm = export_rcm_excel(rcm_rows)
    save_generated_document(
        filename=f"{proc.get('code_prefix', 'PROC')}_RCM_{proc.get('current_version', 'v1.0')}.xlsx",
        mime_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        data=excel_rcm,
        process_id=process_id,
        created_by=user["id"]
    )
    st.download_button(
        "📥 Export RCM to Excel (.xlsx)",
        data=excel_rcm,
        file_name=f"{proc.get('code_prefix', 'PROC')}_RCM_{proc.get('current_version', 'v1.0')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

st.divider()

# Interactive Table
df_rcm = pd.DataFrame(rcm_rows)
st.dataframe(
    df_rcm,
    use_container_width=True,
    column_config={
        "risk_code": st.column_config.TextColumn("Risk ID", width="small"),
        "risk_description": st.column_config.TextColumn("Inherent Risk Description", width="large"),
        "inherent_rating": st.column_config.TextColumn("Inherent Rating"),
        "control_code": st.column_config.TextColumn("Control ID", width="small"),
        "control_description": st.column_config.TextColumn("Control Activity", width="large"),
        "control_type": st.column_config.TextColumn("Type"),
        "nature": st.column_config.TextColumn("Nature"),
        "frequency": st.column_config.TextColumn("Frequency"),
        "owner": st.column_config.TextColumn("Owner"),
        "key_control": st.column_config.CheckboxColumn("Key Control"),
        "design_rating": st.column_config.TextColumn("Design Rating")
    }
)

st.divider()

# Unmitigated Gaps / Suggested Controls Section
unmitigated = [r for r in rcm_rows if r["control_code"] == "GAP / UNMITIGATED"]
if unmitigated:
    st.subheader("⚠️ Unmitigated Risk Gaps (Option 7)")
    st.warning(f"Identified {len(unmitigated)} risks with no mitigating control.")
    for g in unmitigated:
        st.markdown(f"**{g['risk_code']}:** {g['risk_description']}")
        if st.button(f"💡 Suggest Mitigating Control for {g['risk_code']}", key=f"sug_{g['risk_code']}"):
            st.success(f"Recommended Control: Dual review and telephone callback verification (C-LIB-01) from Library.")
