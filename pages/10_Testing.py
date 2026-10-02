import streamlit as st
import pandas as pd
from pathlib import Path
from core.db import db
from core.model_repo import get_process
from core.agent_registry import render_active_agent_pill, render_deliverable_attribution
from core.ui import apply_inter_theme
from graphs.orchestrator import run_task

st.set_page_config(page_title="Audit Testing & Analytics · FieldAI", page_icon="🔬", layout="wide")
apply_inter_theme()

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
        data_source = st.radio(
            "Transaction Data Source:",
            ["Persistent Sample: 1,000 Procurement Invoices (Centralized Storage)", "Upload Custom Dataset (CSV / Excel)"],
            horizontal=True
        )
        data_file = None
        if "Upload" in data_source:
            data_file = st.file_uploader("Upload Transaction Dataset", type=["csv", "xlsx"])

    df_test = None
    if data_file:
        df_test = pd.read_csv(data_file) if data_file.name.endswith(".csv") else pd.read_excel(data_file)
    else:
        # Load 1,000 records persistent sample
        candidates = [
            Path("sample_data/invoices_extract_1000.csv"),
            Path("sample_data/invoices_extract.csv")
        ]
        for p in candidates:
            if p.exists():
                try:
                    df_test = pd.read_csv(p)
                    break
                except Exception:
                    pass

    if df_test is not None:
        total_amt = df_test["amount"].sum() if "amount" in df_test.columns else 0.0
        uniq_vendors = df_test["vendor_id"].nunique() if "vendor_id" in df_test.columns else 0
        min_date = str(df_test["date"].min())[:10] if "date" in df_test.columns else "N/A"
        max_date = str(df_test["date"].max())[:10] if "date" in df_test.columns else "N/A"

        m_c1, m_c2, m_c3, m_c4 = st.columns(4)
        with m_c1:
            st.metric("Total Transactions", f"{len(df_test):,}")
        with m_c2:
            st.metric("Population Spend", f"${total_amt:,.2f}")
        with m_c3:
            st.metric("Active Vendors", uniq_vendors)
        with m_c4:
            st.metric("Date Span", f"{min_date} to {max_date}")

        with st.expander(f"Preview Dataset ({len(df_test):,} Records · Centralized Storage Sample)", expanded=False):
            st.dataframe(df_test.head(10), use_container_width=True)

        col_run1, col_run2 = st.columns([1, 2])
        with col_run1:
            run_btn = st.button("🚀 Execute Analytics Test", type="primary", key="btn_run_an")
        with col_run2:
            make_rec = st.checkbox("Schedule as recurring continuous monitoring test", value=False, key="chk_rec_an")

        if run_btn:
            render_active_agent_pill("analytics_agent", f"Executing {selected_an_id} algorithms on full transaction dataset ({len(df_test)} rows)...")
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

    c_sod_src, c_sod_meta = st.columns([1.5, 1.5])
    with c_sod_src:
        sod_src = st.radio(
            "User Access Matrix Source:",
            ["Persistent Sample: Enterprise Access Matrix (80 Users, 120 Roles - Centralized Storage)", "Upload Custom Access Matrix (CSV / Excel)"],
            horizontal=True,
            key="rad_sod_src"
        )
    sod_file = None
    if "Upload" in sod_src:
        with c_sod_meta:
            sod_file = st.file_uploader("Upload User Access Matrix", type=["csv", "xlsx"], key="up_sod_file")

    df_sod_data = None
    if sod_file:
        df_sod_data = pd.read_csv(sod_file) if sod_file.name.endswith(".csv") else pd.read_excel(sod_file)
    else:
        for p in [Path("sample_data/user_access_matrix_large.csv"), Path("sample_data/user_access_matrix.csv")]:
            if p.exists():
                try:
                    df_sod_data = pd.read_csv(p)
                    break
                except Exception:
                    pass

    if df_sod_data is not None:
        total_assignments = len(df_sod_data)
        unique_users = df_sod_data["user_id"].nunique() if "user_id" in df_sod_data.columns else len(df_sod_data)
        dept_cnt = df_sod_data["department"].nunique() if "department" in df_sod_data.columns else 1

        sm1, sm2, sm3 = st.columns(3)
        with sm1:
            st.metric("Total Users Evaluated", unique_users)
        with sm2:
            st.metric("Role Assignments", total_assignments)
        with sm3:
            st.metric("Covered Departments", dept_cnt)

        with st.expander(f"Preview User Access Matrix ({total_assignments} assignments across {unique_users} users)", expanded=False):
            st.dataframe(df_sod_data.head(10), use_container_width=True)

    if st.button("🚀 Run SoD Conflict Analysis on User Access Matrix", type="primary", key="btn_run_sod"):
        render_active_agent_pill("sod_agent", "Evaluating user privilege matrix against toxic SoD rule catalog...")
        with st.spinner("Analyzing user permissions against SoD rule matrix..."):
            sod_res = run_task("run_test", {
                "task": "run_test",
                "process_id": process_id,
                "user_id": user["id"],
                "test_request": {
                    "test_type": "sod",
                    "user_access": df_sod_data
                }
            })
            conflicts = sod_res.get("sod_conflicts", [])
            st.warning(sod_res.get("summary", "Analysis complete."))
            for c in conflicts:
                badge_color = "#ef4444" if c.get("severity") == "Critical" else "#f59e0b"
                st.markdown(f"""
                <div style="border-left: 4px solid {badge_color}; padding-left: 12px; margin-bottom: 12px; background: rgba(255,255,255,0.02); padding: 8px 12px; border-radius: 4px;">
                    <div style="font-size: 14px; font-weight: 500;">
                        ⚠️ <strong>{c.get('user_name')}</strong> ({c.get('user_id')}) &bull; <span style="color: {badge_color}; font-size: 12px; text-transform: uppercase;">[{c.get('rule_code')} &bull; Severity: {c.get('severity')}]</span>
                    </div>
                    <div style="font-size: 13px; color: #94a3b8; margin-top: 4px;">{c.get('risk')}</div>
                    <div style="font-size: 12px; color: #64748b; margin-top: 4px;">
                        <strong>Assigned Roles:</strong> {', '.join(c.get('conflicting_roles', []))} | <strong>Impacted Lanes:</strong> {', '.join(c.get('impacted_lanes', []))}
                    </div>
                </div>
                """, unsafe_allow_html=True)

# Tab 3: Process Mining
with t3:
    st.subheader("🔄 ERP Event Log Process Mining & Control Bypass Detection")
    render_deliverable_attribution("process_mining_agent", "Event Log Conformance & Path Variance Analysis")
    st.markdown("Reconstructs actual transaction journeys from system event logs and flags path deviations where key controls were skipped.")

    c_pm_src, c_pm_meta = st.columns([1.5, 1.5])
    with c_pm_src:
        pm_src = st.radio(
            "ERP Event Log Source:",
            ["Persistent Sample: P2P ERP Event Log (100 Cases, 569 Events - Centralized Storage)", "Upload Custom ERP Event Log (CSV / Excel)"],
            horizontal=True,
            key="rad_pm_src"
        )
    pm_file = None
    if "Upload" in pm_src:
        with c_pm_meta:
            pm_file = st.file_uploader("Upload ERP Event Log", type=["csv", "xlsx"], key="up_pm_file")

    df_pm_data = None
    if pm_file:
        df_pm_data = pd.read_csv(pm_file) if pm_file.name.endswith(".csv") else pd.read_excel(pm_file)
    else:
        for p in [Path("sample_data/erp_event_log_large.csv"), Path("sample_data/erp_event_log.csv")]:
            if p.exists():
                try:
                    df_pm_data = pd.read_csv(p)
                    break
                except Exception:
                    pass

    if df_pm_data is not None:
        tot_events = len(df_pm_data)
        tot_cases = df_pm_data["case_id"].nunique() if "case_id" in df_pm_data.columns else 0
        tot_acts = df_pm_data["activity"].nunique() if "activity" in df_pm_data.columns else 0

        pmm1, pmm2, pmm3 = st.columns(3)
        with pmm1:
            st.metric("Total Cases (POs)", tot_cases)
        with pmm2:
            st.metric("Total Audit Events Logged", f"{tot_events:,}")
        with pmm3:
            st.metric("Distinct Lifecycle Activities", tot_acts)

        with st.expander(f"Preview ERP Event Log ({tot_events:,} events across {tot_cases} cases)", expanded=False):
            st.dataframe(df_pm_data.head(10), use_container_width=True)

    if st.button("🚀 Mine Process Variants from ERP Event Log", type="primary", key="btn_run_pm"):
        render_active_agent_pill("process_mining_agent", "Reconstructing transaction pathways and identifying bypasses...")
        with st.spinner("Calculating execution variants and checking control gates..."):
            mining_res = run_task("run_test", {
                "task": "run_test",
                "process_id": process_id,
                "user_id": user["id"],
                "test_request": {
                    "test_type": "process_mining",
                    "event_log": df_pm_data
                }
            })
            pm_data = mining_res.get("process_mining", {})
            st.write(f"**Total Processed Cases:** {pm_data.get('total_cases')} | **Distinct Flow Variants Identified:** {pm_data.get('distinct_variants')}")

            st.markdown("#### Identified Flow Variants:")
            for v in pm_data.get("variants", []):
                badge = "<span style='color: #10b981; font-weight: 500;'>🟢 Compliant Golden Path</span>" if v.get("compliant") else "<span style='color: #ef4444; font-weight: 500;'>🔴 Control Bypass Detected</span>"
                st.markdown(f"""
                <div style="background: rgba(255,255,255,0.02); padding: 8px 12px; border-radius: 4px; margin-bottom: 8px; border: 1px solid rgba(255,255,255,0.06);">
                    <div style="font-size: 13px;"><code>{v.get('variant_flow')}</code></div>
                    <div style="font-size: 12px; color: #94a3b8; margin-top: 4px;">
                        {v.get('case_count')} cases ({v.get('frequency_pct')}%) &bull; {badge}
                    </div>
                </div>
                """, unsafe_allow_html=True)

            bypasses = pm_data.get("bypassed_cases", [])
            if bypasses:
                st.markdown("#### 🚨 Bypassed Control Cases:")
                b_df = pd.DataFrame(bypasses)
                st.dataframe(b_df, use_container_width=True)

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
