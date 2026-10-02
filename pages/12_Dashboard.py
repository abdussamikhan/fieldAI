import streamlit as st
import pandas as pd
from core.db import db
from core.model_repo import get_process
from core.agent_registry import render_deliverable_attribution
from core.ui import apply_inter_theme

st.set_page_config(page_title="CAE Executive Dashboard · FieldAI", page_icon="📈", layout="wide")
apply_inter_theme()

if not st.session_state.get("user"):
    st.warning("Please sign in from the main page.")
    st.stop()

user = st.session_state.user
process_id = st.session_state.get("current_process_id", 1)
proc = get_process(process_id)

st.title("📈 Chief Audit Executive (CAE) Dashboard")
st.caption(f"Real-time audit coverage, control design ratings, and exception analytics for **{proc['name'] if proc else 'Process'}**")
render_deliverable_attribution("monitoring_agent", "Executive Audit Telemetry & Heat Map Metrics")

# Metrics summary
m1, m2, m3, m4 = st.columns(4)

steps = db.fetch_all("SELECT * FROM steps WHERE process_id = %s AND status = 'active';", (process_id,))
risks = db.fetch_all("SELECT * FROM risks WHERE process_id = %s AND status = 'active';", (process_id,))
controls = db.fetch_all("SELECT * FROM controls WHERE process_id = %s AND status = 'active';", (process_id,))
tests = db.fetch_all("SELECT * FROM tests WHERE process_id = %s;", (process_id,))
findings = db.fetch_all("SELECT * FROM findings WHERE process_id = %s;", (process_id,))

with m1:
    st.metric("Total Steps", len(steps))
with m2:
    high_risks = [r for r in risks if r.get("inherent_rating") == "High"]
    st.metric("High Risks Identified", len(high_risks))
with m3:
    key_ctrls = [c for c in controls if c.get("key_control")]
    st.metric("Key Controls", len(key_ctrls))
with m4:
    st.metric("Open Findings", len(findings))

st.divider()

col_ch1, col_ch2 = st.columns(2)

with col_ch1:
    st.subheader("Control Design Adequacy Distribution")
    design_counts = {"Adequate": 0, "Partially adequate": 0, "Inadequate": 0}
    for c in controls:
        r = c.get("design_rating", "Adequate")
        design_counts[r] = design_counts.get(r, 0) + 1
    
    df_design = pd.DataFrame(list(design_counts.items()), columns=["Rating", "Count"])
    st.bar_chart(df_design.set_index("Rating"))

with col_ch2:
    st.subheader("Fieldwork Testing Execution Status")
    test_results = {"Untested": 0, "Pass": 0, "Exception": 0, "Inconclusive": 0}
    for t in tests:
        res = t.get("result", "Untested")
        test_results[res] = test_results.get(res, 0) + 1
    
    df_res = pd.DataFrame(list(test_results.items()), columns=["Result", "Count"])
    st.bar_chart(df_res.set_index("Result"))

st.divider()

st.subheader("🚨 Automated Exceptions & Continuous Monitoring Alerts")
test_runs = db.fetch_all("SELECT * FROM test_runs ORDER BY id DESC LIMIT 5;")
if test_runs:
    df_runs = pd.DataFrame(test_runs)[["run_type", "result_summary", "exceptions_count", "run_at", "recurring"]]
    st.dataframe(df_runs, use_container_width=True)
else:
    st.info("No exceptions recorded yet from analytics or recurring cron tests.")
