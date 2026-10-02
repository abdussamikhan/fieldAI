import streamlit as st
from core.db import db
from core.audit_log import log_audit
from core.ui import apply_inter_theme

st.set_page_config(page_title="Engagements & Processes · FieldAI", page_icon="📁", layout="wide")
apply_inter_theme()

if not st.session_state.get("user"):
    st.warning("Please sign in from the main page.")
    st.stop()

user = st.session_state.user
st.title("📁 Engagements & Audit Processes")
st.caption("Manage audit scopes, entities, and business processes under review.")

col1, col2 = st.columns([1.2, 1.8])

with col1:
    st.subheader("Select Active Context")
    engagements = db.fetch_all("SELECT * FROM engagements ORDER BY id ASC;")
    
    eng_options = {e["id"]: f"{e['name']} ({e['entity']} - {e['period']})" for e in engagements}
    curr_eng = st.session_state.get("current_engagement_id", 1)
    
    selected_eng = st.selectbox(
        "Current Audit Engagement",
        options=list(eng_options.keys()),
        format_func=lambda x: eng_options.get(x, ""),
        index=list(eng_options.keys()).index(curr_eng) if curr_eng in eng_options else 0
    )
    st.session_state.current_engagement_id = selected_eng

    # Processes for selected engagement
    processes = db.fetch_all("SELECT * FROM processes WHERE engagement_id = %s ORDER BY id ASC;", (selected_eng,))
    if processes:
        proc_options = {p["id"]: f"{p['name']} [Prefix: {p['code_prefix']}] ({p['current_version']})" for p in processes}
        curr_proc = st.session_state.get("current_process_id", processes[0]["id"])
        selected_proc = st.selectbox(
            "Current Process Under Audit",
            options=list(proc_options.keys()),
            format_func=lambda x: proc_options.get(x, ""),
            index=list(proc_options.keys()).index(curr_proc) if curr_proc in proc_options else 0
        )
        st.session_state.current_process_id = selected_proc
    else:
        st.info("No processes created under this engagement yet.")

    st.divider()

    st.subheader("➕ Create New Engagement")
    with st.form("new_eng_form"):
        eng_name = st.text_input("Engagement Name", placeholder="e.g. FY2026 Internal Audit Plan")
        eng_entity = st.text_input("Audited Entity", placeholder="e.g. Alpha Operations KSA")
        eng_period = st.text_input("Audit Period", placeholder="e.g. FY2026 Q1-Q4")
        submit_eng = st.form_submit_button("Create Engagement")

        if submit_eng and eng_name and eng_entity:
            new_id = db.execute_insert(
                "INSERT INTO engagements (name, entity, period) VALUES (%s, %s, %s);",
                (eng_name, eng_entity, eng_period)
            )
            log_audit(user["id"], "create_engagement", "engagement", new_id)
            st.success(f"Created engagement #{new_id}: {eng_name}")
            st.session_state.current_engagement_id = new_id
            st.rerun()

with col2:
    st.subheader("➕ Create New Process Under Current Engagement")
    with st.form("new_proc_form"):
        proc_name = st.text_input("Process Name", placeholder="e.g. Order-to-Cash (O2C)")
        code_prefix = st.text_input("Process Code Prefix", value="O2C", help="Prefix for step IDs (e.g., P2P, O2C, ITGC)")
        submit_proc = st.form_submit_button("Create Process")

        if submit_proc and proc_name:
            new_pid = db.execute_insert(
                "INSERT INTO processes (engagement_id, name, code_prefix, current_version) VALUES (%s, %s, %s, 'v1.0');",
                (selected_eng, proc_name, code_prefix.strip().upper())
            )
            log_audit(user["id"], "create_process", "process", new_pid)
            st.success(f"Created process: {proc_name} ({code_prefix})")
            st.session_state.current_process_id = new_pid
            st.rerun()

    st.divider()
    st.subheader("Active Process Details")
    active_proc = db.fetch_one("SELECT * FROM processes WHERE id = %s;", (st.session_state.get("current_process_id", 1),))
    if active_proc:
        st.write(f"**Process Name:** {active_proc['name']}")
        st.write(f"**Code Prefix:** `{active_proc['code_prefix']}`")
        st.write(f"**Current Version:** `{active_proc['current_version']}`")

        versions = db.fetch_all("SELECT * FROM versions WHERE process_id = %s ORDER BY id DESC;", (active_proc["id"],))
        st.markdown("#### Version History")
        if versions:
            for v in versions:
                st.markdown(f"- **{v['version_label']}** ({v['created_at']}): {v['change_log'] or 'Baseline'}")
        else:
            st.caption("No historical locked snapshots yet.")
