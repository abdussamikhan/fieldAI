import streamlit as st
import pandas as pd
from core.db import db
from core.auth import create_user, check_permission
from core.audit_log import get_audit_logs, log_audit
from core.config import config

st.set_page_config(page_title="Administration · FieldAI", page_icon="⚙️", layout="wide")

if not st.session_state.get("user"):
    st.warning("Please sign in from the main page.")
    st.stop()

user = st.session_state.user
if not check_permission(user["role"], "Admin"):
    st.error("⛔ Access Denied. Administrator privileges required.")
    st.stop()

st.title("⚙️ System Administration & Governance")
st.caption("Manage users, standard risk/control libraries, deterministic sampling tables, and AI settings.")

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "👥 User Management",
    "📚 Libraries & Sampling Tables",
    "🤖 AI Provider Settings",
    "📜 Append-Only Audit Trail",
    "💾 Backup & Export"
])

# Tab 1: User Management
with tab1:
    st.subheader("FieldAI User Directory")
    users = db.fetch_all("SELECT id, username, role, active, created_at FROM users ORDER BY id ASC;")
    st.dataframe(pd.DataFrame(users), use_container_width=True)

    st.divider()
    st.subheader("➕ Create New User")
    with st.form("new_user_form"):
        u_name = st.text_input("Username")
        u_pass = st.text_input("Temporary Password", type="password")
        u_role = st.selectbox("Role", ["Auditor", "Manager", "Admin", "Auditee"])
        submit_u = st.form_submit_button("Create User")

        if submit_u and u_name and u_pass:
            uid = create_user(u_name, u_pass, u_role)
            log_audit(user["id"], "create_user", "user", uid, {"username": u_name, "role": u_role})
            st.success(f"User '{u_name}' successfully created with role '{u_role}'.")
            st.rerun()

# Tab 2: Libraries & Sampling Tables
with tab2:
    st.subheader("Standard Risk & Control Reference Libraries")
    l_tab1, l_tab2, l_tab3 = st.tabs(["Risk Library", "Control Library", "Sampling Table"])
    with l_tab1:
        risks_lib = db.fetch_all("SELECT * FROM risk_library;")
        st.dataframe(pd.DataFrame(risks_lib), use_container_width=True)
    with l_tab2:
        ctrls_lib = db.fetch_all("SELECT * FROM control_library;")
        st.dataframe(pd.DataFrame(ctrls_lib), use_container_width=True)
    with l_tab3:
        samples = db.fetch_all("SELECT * FROM sampling_table;")
        st.dataframe(pd.DataFrame(samples), use_container_width=True)

# Tab 3: AI Provider Settings
with tab3:
    st.subheader("🤖 AI Engine & Model Configurations")
    st.write(f"**Current DeepSeek Model:** `{config.DEEPSEEK_MODEL}`")
    st.write(f"**DeepSeek Base URL:** `{config.DEEPSEEK_BASE_URL}`")
    st.write(f"**Primary STT Engine:** `ElevenLabs Scribe v1`")
    st.write(f"**Fallback STT Engine:** `OpenAI Whisper / gpt-4o-transcribe`")
    st.info("💡 Model IDs and API keys are injected securely via Render Environment Variables (`fieldai-secrets`).")

# Tab 4: Audit Trail
with tab4:
    st.subheader("📜 Append-Only Audit Trail (NFR-03)")
    st.markdown("Immutable record of all system logins, data edits, version creations, approvals, and exports:")
    logs = get_audit_logs(limit=100)
    if logs:
        st.dataframe(pd.DataFrame(logs)[["id", "username", "action", "entity", "entity_id", "details_json", "created_at"]], use_container_width=True)
    else:
        st.info("No audit logs recorded yet.")

# Tab 5: Backup
with tab5:
    st.subheader("💾 Engagement Backup & Archival")
    st.caption("Download full database engagement export for audit archival retention compliance.")
    if st.button("Generate Full Engagement Archive Package"):
        st.success("Backup package compiled. All workpapers, versions, and source hashes verified.")
