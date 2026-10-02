import streamlit as st
from core.db import db
from core.auth import authenticate_user
from core.audit_log import log_audit
from graphs.orchestrator import run_task

st.set_page_config(
    page_title="FieldAI – Multi-Agent AI Audit Fieldwork Assistant",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize database on startup
db.init_db()

# Session State Initialization
if "user" not in st.session_state:
    st.session_state.user = None
if "current_engagement_id" not in st.session_state:
    eng = db.fetch_one("SELECT id FROM engagements ORDER BY id ASC LIMIT 1;")
    st.session_state.current_engagement_id = eng["id"] if eng else 1
if "current_process_id" not in st.session_state:
    proc = db.fetch_one("SELECT id FROM processes ORDER BY id ASC LIMIT 1;")
    st.session_state.current_process_id = proc["id"] if proc else 1

# Authentication Guard
if not st.session_state.user:
    st.markdown(
        """
        <div style="text-align: center; margin-top: 50px; margin-bottom: 30px;">
            <h1 style="font-size: 2.8rem; font-weight: 800; color: #38bdf8; margin-bottom: 8px;">🛡️ FieldAI</h1>
            <p style="font-size: 1.15rem; color: #94a3b8;">Multi-Agent AI Audit Fieldwork Assistant · LangGraph & PostgreSQL</p>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        st.markdown(
            """
            <div style="background-color: #1e293b; padding: 24px; border-radius: 12px; border: 1px solid #334155;">
                <h3 style="margin-top: 0; color: #f8fafc; font-size: 1.25rem;">Sign In to FieldAI</h3>
                <p style="color: #94a3b8; font-size: 0.9rem;">Enter your internal audit fieldwork credentials</p>
            </div>
            """,
            unsafe_allow_html=True
        )
        with st.form("login_form"):
            username = st.text_input("Username", value="admin")
            password = st.text_input("Password", type="password", value="admin123")
            submit = st.form_submit_button("Sign In", use_container_width=True)
            
            if submit:
                user = authenticate_user(username, password)
                if user:
                    st.session_state.user = user
                    log_audit(user["id"], "login", "user", user["id"])
                    st.success(f"Welcome back, {user['username']}!")
                    st.rerun()
                else:
                    st.error("Invalid username or password. (Default credentials: admin / admin123)")
    st.stop()

# --- Authenticated App Header & Sidebar ---
user = st.session_state.user

with st.sidebar:
    st.markdown(
        f"""
        <div style="padding: 10px; background-color: #0f172a; border-radius: 8px; border: 1px solid #334155; margin-bottom: 15px;">
            <div style="font-weight: 600; color: #38bdf8;">👤 {user['username']}</div>
            <div style="font-size: 0.8rem; color: #94a3b8;">Role: <b>{user['role']}</b></div>
        </div>
        """,
        unsafe_allow_html=True
    )
    if st.button("Log Out", use_container_width=True):
        st.session_state.user = None
        st.rerun()
    
    st.divider()
    
    # Active Engagement & Process Indicator
    eng = db.fetch_one("SELECT * FROM engagements WHERE id = %s;", (st.session_state.current_engagement_id,))
    proc = db.fetch_one("SELECT * FROM processes WHERE id = %s;", (st.session_state.current_process_id,))
    
    st.markdown(f"**Engagement:** {eng['name'] if eng else 'None'}")
    st.markdown(f"**Process:** {proc['name'] if proc else 'None'} (`{proc['code_prefix'] if proc else 'P2P'}`)")
    st.markdown(f"**Version:** `{proc['current_version'] if proc else 'v1.0'}`")

# Main Header & Global "Ask FieldAI" Assistant
col_t, col_q = st.columns([1.2, 1.8])
with col_t:
    st.title("🛡️ FieldAI Fieldwork Assistant")
    st.caption("AI-Powered Walkthrough Capture, RCM, Audit Programs, and Continuous Testing")

with col_q:
    with st.container():
        query = st.text_input("💬 Ask FieldAI (instant audit search, control guidance, standards)", placeholder="e.g. What are the delegation thresholds in the P2P SOP?")
        if query:
            with st.spinner("FieldAI analyzing documents & transcripts..."):
                res = run_task("ask", {
                    "task_input": query,
                    "process_id": st.session_state.current_process_id,
                    "user_id": user["id"]
                })
                qa_res = res.get("doc_qa_result", {})
                st.info(f"**Answer:** {qa_res.get('answer', 'Information retrieved.')}")
                citations = qa_res.get("citations", [])
                if citations:
                    st.caption("📌 **Verified Citations:**")
                    for cit in citations:
                        st.caption(f"- *{cit.get('source', '')} ({cit.get('locator', '')})*: \"{cit.get('quote', '')}\"")

st.divider()

# Overview Statistics Cards
c1, c2, c3, c4 = st.columns(4)

steps_count = db.fetch_one("SELECT COUNT(*) as c FROM steps WHERE process_id = %s AND status = 'active';", (st.session_state.current_process_id,))
risks_count = db.fetch_one("SELECT COUNT(*) as c FROM risks WHERE process_id = %s AND status = 'active';", (st.session_state.current_process_id,))
controls_count = db.fetch_one("SELECT COUNT(*) as c FROM controls WHERE process_id = %s AND status = 'active';", (st.session_state.current_process_id,))
tests_count = db.fetch_one("SELECT COUNT(*) as c FROM tests WHERE process_id = %s;", (st.session_state.current_process_id,))

with c1:
    st.metric("Process Steps", steps_count["c"] if steps_count else 0)
with c2:
    st.metric("Identified Risks", risks_count["c"] if risks_count else 0)
with c3:
    st.metric("Internal Controls", controls_count["c"] if controls_count else 0)
with c4:
    st.metric("Audit Tests", tests_count["c"] if tests_count else 0)

st.markdown("### 🚀 Fieldwork Workflow Navigator")
st.markdown("Navigate through each phase of the audit walkthrough process using the sidebar pages or quick access buttons below:")

row1_col1, row1_col2, row1_col3 = st.columns(3)
with row1_col1:
    st.markdown(
        """
        <div style="background-color: #1e293b; padding: 18px; border-radius: 8px; border-left: 4px solid #0284c7; height: 160px;">
            <h4 style="margin: 0; color: #f8fafc;">1. Capture & Interview</h4>
            <p style="color: #94a3b8; font-size: 0.85rem; margin-top: 8px;">Record audio walkthroughs with consent, transcribe speakers, and capture live interview prompts.</p>
        </div>
        """,
        unsafe_allow_html=True
    )
    if st.button("Open Capture Screen →", key="btn_nav_capture"):
        st.switch_page("pages/2_Capture.py")

with row1_col2:
    st.markdown(
        """
        <div style="background-color: #1e293b; padding: 18px; border-radius: 8px; border-left: 4px solid #10b981; height: 160px;">
            <h4 style="margin: 0; color: #f8fafc;">2. Master Model & Flowchart</h4>
            <p style="color: #94a3b8; font-size: 0.85rem; margin-top: 8px;">Review sequential process table, multi-lane swim lanes (Role/Dept/System), and risk/control badges.</p>
        </div>
        """,
        unsafe_allow_html=True
    )
    if st.button("View Flowchart & Swimlanes →", key="btn_nav_flowchart"):
        st.switch_page("pages/5_Flowchart.py")

with row1_col3:
    st.markdown(
        """
        <div style="background-color: #1e293b; padding: 18px; border-radius: 8px; border-left: 4px solid #f59e0b; height: 160px;">
            <h4 style="margin: 0; color: #f8fafc;">3. RCM & Audit Program</h4>
            <p style="color: #94a3b8; font-size: 0.85rem; margin-top: 8px;">Construct Risk-Control Matrix, framework mappings (COSO, NCA, ISO), and deterministic sample sizes.</p>
        </div>
        """,
        unsafe_allow_html=True
    )
    if st.button("Open RCM Matrix →", key="btn_nav_rcm"):
        st.switch_page("pages/6_RCM.py")

st.markdown("<br/>", unsafe_allow_html=True)

row2_col1, row2_col2, row2_col3 = st.columns(3)
with row2_col1:
    st.markdown(
        """
        <div style="background-color: #1e293b; padding: 18px; border-radius: 8px; border-left: 4px solid #8b5cf6; height: 160px;">
            <h4 style="margin: 0; color: #f8fafc;">4. Document Reconciliation</h4>
            <p style="color: #94a3b8; font-size: 0.85rem; margin-top: 8px;">Compare spoken walkthroughs against written SOPs with 5-category gap analysis.</p>
        </div>
        """,
        unsafe_allow_html=True
    )
    if st.button("Review Documents & SOPs →", key="btn_nav_docs"):
        st.switch_page("pages/8_Documents.py")

with row2_col2:
    st.markdown(
        """
        <div style="background-color: #1e293b; padding: 18px; border-radius: 8px; border-left: 4px solid #ec4899; height: 160px;">
            <h4 style="margin: 0; color: #f8fafc;">5. Analytics & Testing</h4>
            <p style="color: #94a3b8; font-size: 0.85rem; margin-top: 8px;">Run unit-tested analytics algorithms (duplicates, splits, Benford's law), SoD, and process mining.</p>
        </div>
        """,
        unsafe_allow_html=True
    )
    if st.button("Run Audit Tests →", key="btn_nav_tests"):
        st.switch_page("pages/10_Testing.py")

with row2_col3:
    st.markdown(
        """
        <div style="background-color: #1e293b; padding: 18px; border-radius: 8px; border-left: 4px solid #06b6d4; height: 160px;">
            <h4 style="margin: 0; color: #f8fafc;">6. CAE Executive Dashboard</h4>
            <p style="color: #94a3b8; font-size: 0.85rem; margin-top: 8px;">Executive visibility into audit coverage heat maps, control design adequacy, and exception counts.</p>
        </div>
        """,
        unsafe_allow_html=True
    )
    if st.button("Open CAE Dashboard →", key="btn_nav_dash"):
        st.switch_page("pages/12_Dashboard.py")
