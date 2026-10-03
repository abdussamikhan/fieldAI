import streamlit as st
from core.db import db
from core.auth import authenticate_user
from core.audit_log import log_audit
from core.ui import apply_inter_theme

st.set_page_config(
    page_title="FieldAI – Multi-Agent AI Audit Fieldwork Assistant",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

apply_inter_theme()

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
        "<div style='font-family: \"Inter\", sans-serif; text-align: center; margin-top: 50px; margin-bottom: 30px;'>"
        "<h1 style='font-family: \"Inter\", sans-serif; font-size: 2.8rem; font-weight: 400; color: #38bdf8; margin-bottom: 8px;'>🛡️ FieldAI</h1>"
        "<p style='font-family: \"Inter\", sans-serif; font-size: 1.15rem; color: #94a3b8; font-weight: 400;'>Multi-Agent AI Audit Fieldwork Assistant · LangGraph & PostgreSQL</p>"
        "</div>",
        unsafe_allow_html=True
    )
    
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        st.markdown(
            "<div style='font-family: \"Inter\", sans-serif; background-color: #1e293b; padding: 24px; border-radius: 12px; border: 1px solid #334155;'>"
            "<h3 style='font-family: \"Inter\", sans-serif; margin-top: 0; color: #f8fafc; font-size: 1.25rem; font-weight: 400;'>Sign In to FieldAI</h3>"
            "<p style='font-family: \"Inter\", sans-serif; color: #94a3b8; font-size: 0.9rem; font-weight: 400;'>Enter your internal audit fieldwork credentials</p>"
            "</div>",
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
        f"<div style='padding: 10px; background-color: #0f172a; border-radius: 8px; border: 1px solid #334155; margin-bottom: 15px;'>"
        f"<div style='font-weight: 600; color: #38bdf8;'>👤 {user['username']}</div>"
        f"<div style='font-size: 0.8rem; color: #94a3b8;'>Role: <b>{user['role']}</b></div>"
        f"</div>",
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

# Main Header
st.title("🛡️ FieldAI Fieldwork Assistant")
st.caption("AI-Powered Walkthrough Capture, RCM, Audit Programs, and Continuous Testing")

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
def render_nav_card(title: str, desc: str, border_color: str):
    card_html = (
        f"<div style='font-family: \"Inter\", sans-serif; background-color: #1e293b; padding: 18px; border-radius: 8px; border-left: 4px solid {border_color}; height: 160px;'>"
        f"<h4 style='font-family: \"Inter\", sans-serif; font-weight: 400; margin: 0; color: #f8fafc;'>{title}</h4>"
        f"<p style='font-family: \"Inter\", sans-serif; font-weight: 400; color: #94a3b8; font-size: 0.85rem; margin-top: 8px;'>{desc}</p>"
        f"</div>"
    )
    st.markdown(card_html, unsafe_allow_html=True)

with row1_col1:
    render_nav_card("1. Meeting Capture & Interview", "Record audio walkthroughs with consent, transcribe speakers, and capture live interview prompts.", "#0284c7")
    if st.button("Open Meeting Capture Screen →", key="btn_nav_capture"):
        st.switch_page("pages/2_Meeting_Capture.py")

with row1_col2:
    render_nav_card("2. Master Model & Flowchart", "Review sequential process table, multi-lane swim lanes (Role/Dept/System), and risk/control badges.", "#10b981")
    if st.button("View Flowchart & Swimlanes →", key="btn_nav_flowchart"):
        st.switch_page("pages/5_Flowchart.py")

with row1_col3:
    render_nav_card("3. RCM & Audit Program", "Construct Risk-Control Matrix, framework mappings (COSO, NCA, ISO), and deterministic sample sizes.", "#f59e0b")
    if st.button("Open RCM Matrix →", key="btn_nav_rcm"):
        st.switch_page("pages/6_RCM.py")

st.markdown("<br/>", unsafe_allow_html=True)

row2_col1, row2_col2, row2_col3 = st.columns(3)
with row2_col1:
    render_nav_card("4. RAG Documents Reconciliation", "Compare spoken walkthroughs against written SOPs with 5-category gap analysis.", "#8b5cf6")
    if st.button("Review RAG Documents & SOPs →", key="btn_nav_docs"):
        st.switch_page("pages/8_RAG_Documents.py")

with row2_col2:
    render_nav_card("5. Testing & Analytics", "Run unit-tested analytics algorithms (duplicates, splits, Benford's law), SoD, and process mining.", "#ec4899")
    if st.button("Run Testing & Analytics →", key="btn_nav_tests"):
        st.switch_page("pages/10_Testing_&_Analytics.py")

with row2_col3:
    render_nav_card("6. CAE Dashboard", "Executive visibility into audit coverage heat maps, control design adequacy, and exception counts.", "#06b6d4")
    if st.button("Open CAE Dashboard →", key="btn_nav_dash"):
        st.switch_page("pages/12_CAE_Dashboard.py")

st.markdown("<br/>", unsafe_allow_html=True)

row3_col1, row3_col2, row3_col3 = st.columns(3)
with row3_col1:
    render_nav_card("7. Centralized Data Storage", "Unified permanent repository for all walkthrough recordings, source documents, generated deliverables, and exports.", "#14b8a6")
    if st.button("Explore Central Storage →", key="btn_nav_storage"):
        st.switch_page("pages/15_Centralized_Storage.py")

with row3_col2:
    render_nav_card("8. Walkthrough Preparation & Scoping", "Generate bilingual interview packs, scoping metrics, and save/load them from central database storage.", "#f97316")
    if st.button("Open Preparation & Scoping →", key="btn_nav_prep"):
        st.switch_page("pages/9_Preparation_&_Scoping.py")

with row3_col3:
    render_nav_card("9. Findings & QA", "Draft 5 Cs findings, manage review notes, and export professional Word (.docx) audit memos.", "#6366f1")
    if st.button("Review Findings & QA →", key="btn_nav_findings"):
        st.switch_page("pages/11_Findings_&_QA.py")

st.markdown("<br/>", unsafe_allow_html=True)

row4_col1, row4_col2, row4_col3 = st.columns(3)
with row4_col1:
    render_nav_card("10. Auditee Confirmation", "Secure walkthrough verification and clarification interface for client process owners.", "#3b82f6")
    if st.button("Open Auditee Confirmation →", key="btn_nav_confirm"):
        st.switch_page("pages/13_Auditee_Confirmation.py")

with row4_col2:
    render_nav_card("11. System Admin", "Configure user permissions, audit trail logs, sampling tables, and platform credentials.", "#64748b")
    if st.button("Open System Admin →", key="btn_nav_admin"):
        st.switch_page("pages/14_System_Admin.py")
