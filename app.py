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


def render_login():
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


# Authentication Routing
if not st.session_state.user:
    pg = st.navigation([st.Page(render_login, title="Login", icon="🛡️")])
    pg.run()
else:
    # 4 Sections as requested: CAE, Auditor, Auditee, Configuration
    nav_sections = {
        "CAE": [
            st.Page("pages/12_CAE_Dashboard.py", title="CAE Dashboard", icon="📈"),
        ],
        "Auditor": [
            st.Page("pages/1_Engagements.py", title="Engagements", icon="📁", default=True),
            st.Page("pages/9_Preparation_&_Scoping.py", title="Preparation & Scoping", icon="📋"),
            st.Page("pages/2_Meeting_Capture.py", title="Meeting capture", icon="🎙️"),
            st.Page("pages/3_Review_Changes.py", title="Review Changes", icon="⚖️"),
            st.Page("pages/4_Process_Table.py", title="Process Table", icon="📊"),
            st.Page("pages/5_Flowchart.py", title="Flowchart", icon="📐"),
            st.Page("pages/6_RCM.py", title="RCM", icon="🛡️"),
            st.Page("pages/7_Audit_Program.py", title="Audit Program", icon="📜"),
            st.Page("pages/8_RAG_Documents.py", title="RAG Documents", icon="📄"),
            st.Page("pages/10_Testing_&_Analytics.py", title="Testing & Analytics", icon="🔬"),
            st.Page("pages/11_Findings_&_QA.py", title="Findings & QA", icon="📝"),
        ],
        "Auditee": [
            st.Page("pages/13_Auditee_Confirmation.py", title="Auditee Confirmation", icon="🤝"),
        ],
        "Configuration": [
            st.Page("pages/14_System_Admin.py", title="System Admin", icon="⚙️"),
            st.Page("pages/15_Centralized_Storage.py", title="Centralized Storage", icon="🗄️"),
        ],
    }

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

    pg = st.navigation(nav_sections)
    pg.run()
