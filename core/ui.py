import streamlit as st

INTER_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500&display=swap');

/* Apply Inter font across the app via typography inheritance */
html, body, p, a, input, select, textarea, label,
h1, h2, h3, h4, h5, h6, b, strong, th, td, table,
.stMarkdown, .stTextInput, .stSelectbox, .stTextArea,
[data-testid="stSidebarNav"] span,
[data-testid*="stMetric"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
    font-weight: 400 !important;
}

/* Explicitly strip bold styling from headings, metrics, badges, and table headers */
h1, h2, h3, h4, h5, h6,
b, strong, th,
[data-testid*="stMetricValue"],
[data-testid*="stMetricLabel"],
.stMarkdown h1, .stMarkdown h2, .stMarkdown h3, .stMarkdown h4, .stMarkdown h5, .stMarkdown h6,
.stMarkdown strong, .stMarkdown b,
.stButton > button,
.stDownloadButton > button,
[data-testid="stExpander"] summary {
    font-family: 'Inter', sans-serif !important;
    font-weight: 400 !important;
}

/* Preserve Material Symbols and Icon fonts for Streamlit UI buttons and navigation */
.material-symbols-rounded,
.material-symbols-outlined,
.material-icons,
[class*="material-symbols"],
[class*="material-icons"],
[data-testid*="Icon"],
[data-testid="stSidebarCollapseButton"] *,
[data-testid="baseButton-headerNoPadding"] *,
[data-testid="stHeader"] button * {
    font-family: "Material Symbols Rounded", "Material Symbols Outlined", "Material Icons" !important;
    font-style: normal !important;
    text-transform: none !important;
    letter-spacing: normal !important;
    word-wrap: normal !important;
    white-space: nowrap !important;
    direction: ltr !important;
}

/* Sidebar Navigation Section Headers */
[data-testid="stSidebarNavSectionHeader"],
div[data-testid="stSidebarNavItems"] > div > span,
[data-testid="stSidebarNav"] h2,
[data-testid="stSidebarNav"] h3 {
    font-family: 'Inter', sans-serif !important;
    font-size: 0.78rem !important;
    font-weight: 600 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.08em !important;
    color: #38bdf8 !important;
    margin-top: 14px !important;
    margin-bottom: 6px !important;
}

/* Sidebar Menu Tile Renaming */
[data-testid="stSidebarNav"] span[label="app"],
[data-testid="stSidebarNav"] span[label="App"] {
    font-size: 0 !important;
    display: inline-flex !important;
    align-items: center !important;
}
[data-testid="stSidebarNav"] span[label="app"]::after,
[data-testid="stSidebarNav"] span[label="App"]::after {
    content: "Login" !important;
    font-size: 0.875rem !important;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
    font-weight: 400 !important;
    visibility: visible !important;
}

[data-testid="stSidebarNav"] span[label="Capture"] {
    font-size: 0 !important;
    display: inline-flex !important;
    align-items: center !important;
}
[data-testid="stSidebarNav"] span[label="Capture"]::after {
    content: "Meeting Capture" !important;
    font-size: 0.875rem !important;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
    font-weight: 400 !important;
    visibility: visible !important;
}

[data-testid="stSidebarNav"] span[label="Documents"] {
    font-size: 0 !important;
    display: inline-flex !important;
    align-items: center !important;
}
[data-testid="stSidebarNav"] span[label="Documents"]::after {
    content: "RAG Documents" !important;
    font-size: 0.875rem !important;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
    font-weight: 400 !important;
    visibility: visible !important;
}

[data-testid="stSidebarNav"] span[label="Prep"] {
    font-size: 0 !important;
    display: inline-flex !important;
    align-items: center !important;
}
[data-testid="stSidebarNav"] span[label="Prep"]::after {
    content: "Preparation & Scoping" !important;
    font-size: 0.875rem !important;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
    font-weight: 400 !important;
    visibility: visible !important;
}

[data-testid="stSidebarNav"] span[label="Testing"] {
    font-size: 0 !important;
    display: inline-flex !important;
    align-items: center !important;
}
[data-testid="stSidebarNav"] span[label="Testing"]::after {
    content: "Testing & Analytics" !important;
    font-size: 0.875rem !important;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
    font-weight: 400 !important;
    visibility: visible !important;
}

[data-testid="stSidebarNav"] span[label="Findings"] {
    font-size: 0 !important;
    display: inline-flex !important;
    align-items: center !important;
}
[data-testid="stSidebarNav"] span[label="Findings"]::after {
    content: "Findings & QA" !important;
    font-size: 0.875rem !important;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
    font-weight: 400 !important;
    visibility: visible !important;
}

[data-testid="stSidebarNav"] span[label="Dashboard"] {
    font-size: 0 !important;
    display: inline-flex !important;
    align-items: center !important;
}
[data-testid="stSidebarNav"] span[label="Dashboard"]::after {
    content: "CAE Dashboard" !important;
    font-size: 0.875rem !important;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
    font-weight: 400 !important;
    visibility: visible !important;
}

[data-testid="stSidebarNav"] span[label="Confirm"] {
    font-size: 0 !important;
    display: inline-flex !important;
    align-items: center !important;
}
[data-testid="stSidebarNav"] span[label="Confirm"]::after {
    content: "Auditee Confirmation" !important;
    font-size: 0.875rem !important;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
    font-weight: 400 !important;
    visibility: visible !important;
}

[data-testid="stSidebarNav"] span[label="Admin"] {
    font-size: 0 !important;
    display: inline-flex !important;
    align-items: center !important;
}
[data-testid="stSidebarNav"] span[label="Admin"]::after {
    content: "System Admin" !important;
    font-size: 0.875rem !important;
    visibility: visible !important;
}

/* Hide developer file-change / rerun prompt in header */
[data-testid="stStatusWidget"] {
    display: none !important;
}
</style>


"""

def apply_inter_theme():
    """Injects global CSS enforcing Inter font and normal (non-bold) weight across all UI features while preserving icons."""
    st.markdown(INTER_CSS, unsafe_allow_html=True)
