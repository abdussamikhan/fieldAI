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
</style>
"""

def apply_inter_theme():
    """Injects global CSS enforcing Inter font and normal (non-bold) weight across all UI features while preserving icons."""
    st.markdown(INTER_CSS, unsafe_allow_html=True)
