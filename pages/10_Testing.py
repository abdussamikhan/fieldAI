import streamlit as st
import pandas as pd
from core.db import db
from core.model_repo import get_process
from core.agent_registry import render_active_agent_pill, render_deliverable_attribution
from graphs.orchestrator import run_task

st.set_page_config(page_title="Audit Testing & Analytics · FieldAI", page_icon="🔬", layout="wide")

if not st.session_state.get("user"):
    st.warning("Please sign in from the main page.")
    st.stop()

user = st.session_state.user
process_id = st.session_state.get("current_process_id", 1)
proc = get_process(process_id)

st.title("🔬 Audit Testing & Analytics Hub")
st.caption("Execute fixed pandas audit algorithms, SoD conflict checks, process mining, and evidence readers.")

t1, t2, t3, t4, t5 = st.tabs([
    "📊 Data Analytics Tests",
    "🛡️ Segregation of Duties (SoD)",
    "🔄 Process Mining",
    "📑 Evidence Reader",
    "⏰ Continuous Monitoring"
])

# Tab 1: Data Analytics Tests
with t1:
    st.subheader("Fixed Audit Analytics Library")
    render_deliverable_attribution("analytics_agent", "Full-Population Transaction Analytics Exception List")
    analytics_tests = db.fetch_all("SELECT * FROM analytics_library ORDER BY test_id ASC;")
    test_dict = {t["test_id"]: f"{t['test_id']}: {t['name']}" for t in analytics_tests}

    c_sel, c_up = st.columns([1, 1])
    with c_sel:
        selected_an_id = st.selectbox("Select Analytics Procedure", options=list(test_dict.keys()), format_func=lambda x: test_dict[x])
        selected_an = next((t for t in analytics_tests if t["test_id"] == selected_an_id), {})
        st.caption(f"**Test Description:** {selected_an.get('description', '')}")

    with c_up:
        data_file = st.file_uploader("Upload Transaction Dataset (CSV / Excel)", type=["csv", "xlsx"])
        use_sample = st.checkbox("Or use built-in sample procurement invoice extract", value=True)

    df_test = None
    if data_file:
        df_test = pd.read_csv(data_file) if data_file.name.endswith(".csv") else pd.read_excel(data_file)
    elif use_sample:
        df_test = pd.read_csv("sample_data/invoices_extract.csv")

    if df_test is not None:
        st.write(f"**Loaded Dataset:** {len(df_test)} transactions")
        with st.expander("Preview Dataset"):
            st.dataframe(df_test.head(6), use_container_width=True)

        col_run1, col_run2 = st.columns([1, 2])
        with col_run1:
            run_btn = st.button("🚀 Execute Analytics Test", type="primary")
        with col_run2:
            make_rec = st.checkbox("Schedule as recurring continuous monitoring test", value=False)

        if run_btn:
            render_active_agent_pill("analytics_agent", f"Executing {selected_an_id} algorithms on full transaction dataset...")
            with st.spinner(f"Running {selected_an_id} algorithms..."):
                res = run_task("run_test", {
                    "task": "run_test",
                    "process_id": process_id,
                    "user_id": user["id"],
                    "test_request": {
                        "test_id": selected_an_id,
                        "test_type": "analytics",
                        "dataframe": df_test,
                        "make_recurring": make_rec
                    }
                })
                t_res = res.get("test_result", {})
                st.success(f"Execution complete: {t_res.get('summary')}")
                
                exc = t_res.get("exceptions")
                if isinstance(exc, list) and exc:
                    st.warning(f"Found {len(exc)} audit exceptions:")
                    st.dataframe(pd.DataFrame(exc), use_container_width=True)
                elif isinstance(exc, dict):
                    st.json(exc)

# Tab 2: SoD Checks
with t2:
    st.subheader("🛡️ User Access & Segregation of Duties (SoD) Analysis")
    render_deliverable_attribution("sod_agent", "Segregation of Duties Conflict Analysis")
    st.markdown("Identifies toxic combinations of user privileges across procurement, disbursement, and master file administration.")
    
    if st.button("Run SoD Conflict Analysis on User Access Matrix"):
        render_active_agent_pill("sod_agent", "Evaluating user privilege matrix against toxic SoD rule catalog...")
        with st.spinner("Analyzing user permissions against SoD rule matrix..."):
            sod_res = run_task("run_test", {
                "task": "run_test",
                "process_id": process_id,
                "user_id": user["id"],
                "test_request": {
                    "test_type": "sod"
                }
            })
            conflicts = sod_res.get("sod_conflicts", [])
            st.warning(sod_res.get("summary", "Analysis complete."))
            for c in conflicts:
                st.error(f"⚠️ **{c.get('user_name')} ({c.get('user_id')}):** {c.get('risk')} [Severity: {c.get('severity')}]")
                st.caption(f"Assigned Roles: {', '.join(c.get('conflicting_roles', []))} | Impacted Lanes: {', '.join(c.get('impacted_lanes', []))}")

# Tab 3: Process Mining
with t3:
    st.subheader("🔄 ERP Event Log Process Mining & Control Bypass Detection")
    render_deliverable_attribution("process_mining_agent", "Event Log Conformance & Path Variance Analysis")
    st.markdown("Reconstructs actual transaction journeys from system event logs and flags path deviations where key controls were skipped.")

    if st.button("Mine Process Variants from ERP Event Log"):
        render_active_agent_pill("process_mining_agent", "Reconstructing transaction pathways and identifying bypasses...")
        with st.spinner("Calculating execution variants and checking control gates..."):
            mining_res = run_task("run_test", {
                "task": "run_test",
                "process_id": process_id,
                "user_id": user["id"],
                "test_request": {
                    "test_type": "process_mining"
                }
            })
            pm_data = mining_res.get("process_mining", {})
            st.write(f"**Total Processed Cases:** {pm_data.get('total_cases')} | **Distinct Flow Variants:** {pm_data.get('distinct_variants')}")

            st.markdown("#### Identified Flow Variants:")
            for v in pm_data.get("variants", []):
                badge = "🟢 Compliant" if v.get("compliant") else "🔴 Control Bypass"
                st.markdown(f"- **{v.get('variant_flow')}** ({v.get('case_count')} cases, `{v.get('frequency_pct')}%`) – {badge}")

            bypasses = pm_data.get("bypassed_cases", [])
            if bypasses:
                st.markdown("#### 🚨 Bypassed Control Cases:")
                for b in bypasses:
                    st.error(f"Case **{b.get('case_id')}**: {b.get('reason')}")

# Tab 4: Evidence Reader
with t4:
    st.subheader("📑 Sample Evidence Document Attribute Inspector")
    render_deliverable_attribution("evidence_agent", "Voucher Document OCR & Attribute Validation")
    st.markdown("Inspects sample invoices, PO approvals, or payment receipts against defined audit attributes.")
    
    sample_text = st.text_area(
        "Sample Evidence Content (from OCR or text extract)",
        value="PURCHASE ORDER: PO-9921\nVendor: TechSupplies Ltd | Date: 2026-02-14\nTotal PO Amount: $48,000.00\nApproval: Approved by John Doe (Operations VP) on 2026-02-14 09:12 UTC\nINVOICE: INV-1002\nBilled To: Alpha Corp | Total Amount: $54,200.00\nPayment Terms: Net 30"
    )

    if st.button("Inspect Sample Attributes"):
        render_active_agent_pill("evidence_agent", "Evaluating evidence against audit attributes...")
        with st.spinner("Evaluating evidence against audit attributes..."):
            ev_res = run_task("run_test", {
                "task": "run_test",
                "process_id": process_id,
                "user_id": user["id"],
                "test_request": {
                    "test_type": "evidence"
                },
                "task_input": sample_text
            })
            eval_data = ev_res.get("evidence_evaluation", {})
            for attr in eval_data.get("attributes_evaluated", []):
                st_color = "🟢 PASS" if attr.get("status") == "Pass" else "🔴 FAIL"
                st.markdown(f"**Attribute:** {attr.get('attribute')} – **{st_color}**")
                st.caption(f"Quoted Evidence: *\"{attr.get('quoted_evidence')}\"*")
                if attr.get("finding_note"):
                    st.warning(attr.get("finding_note"))

# Tab 5: Continuous Monitoring
with t5:
    st.subheader("⏰ Continuous Automated Monitoring")
    render_deliverable_attribution("monitoring_agent", "Continuous Scheduled Audit Monitor")
    st.markdown("Review tests configured for recurring execution via the Render background cron job.")

    rec_tests = db.fetch_all("SELECT tr.*, t.test_code, t.control_code FROM test_runs tr JOIN tests t ON tr.test_id = t.id WHERE tr.recurring = TRUE;")
    if rec_tests:
        st.dataframe(pd.DataFrame(rec_tests), use_container_width=True)
    else:
        st.info("No recurring tests configured. Check the 'Schedule as recurring' box when running analytics above.")
