import streamlit as st

INTER_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500&display=swap');

/* Enforce Inter font and non-bold font weight across all UI elements */
html, body, [class*="css"], [class*="st-"], [data-testid],
div, span, p, a, button, input, select, textarea, label,
h1, h2, h3, h4, h5, h6, b, strong, th, td, table, code, pre,
.stMarkdown, .stButton, .stDownloadButton, [data-testid="stSidebarNav"] {
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
</style>
"""

def apply_inter_theme():
    """Injects global CSS enforcing Inter font and normal (non-bold) weight across all UI features."""
    st.markdown(INTER_CSS, unsafe_allow_html=True)
