import streamlit as st
import pandas as pd
import altair as alt
from typing import Dict, Any, Optional, List

def create_metric_card(label: str, value: str, subtext: str = "", delta_color: str = "#3b82f6"):
    """Helper to render a styled key metric block with non-bold Inter typography."""
    st.markdown(f"""
    <div style="background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 8px; padding: 12px 16px;">
        <div style="font-size: 12px; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.5px;">{label}</div>
        <div style="font-size: 24px; color: #f8fafc; margin: 4px 0;">{value}</div>
        <div style="font-size: 11px; color: {delta_color};">{subtext}</div>
    </div>
    """, unsafe_allow_html=True)

def render_an01_duplicate_charts(df_exc: pd.DataFrame, df_full: pd.DataFrame):
    """AN-01: Duplicate Payments Visualizations."""
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("##### 🏢 Duplicate Payment Exposure by Vendor")
        if "vendor_id" in df_exc.columns and "amount" in df_exc.columns:
            vendor_summary = df_exc.groupby("vendor_id")["amount"].sum().reset_index()
            vendor_summary = vendor_summary.sort_values(by="amount", ascending=False).head(10)
            chart = alt.Chart(vendor_summary).mark_bar(color="#ef4444", cornerRadiusTopRight=4, cornerRadiusBottomRight=4).encode(
                x=alt.X("amount:Q", title="Total Duplicate Amount ($)"),
                y=alt.Y("vendor_id:N", sort="-x", title="Vendor ID"),
                tooltip=[alt.Tooltip("vendor_id:N", title="Vendor"), alt.Tooltip("amount:Q", title="Duplicate Sum ($)", format="$,.2f")]
            ).properties(height=320)
            st.altair_chart(chart, use_container_width=True)
        else:
            st.info("Vendor and amount data not available.")

    with c2:
        st.markdown("##### 📅 Duplicate Postings Timeline")
        if "date" in df_exc.columns and "amount" in df_exc.columns:
            df_plot = df_exc.copy()
            df_plot["date_parsed"] = pd.to_datetime(df_plot["date"], errors="coerce")
            df_plot = df_plot.dropna(subset=["date_parsed"]).sort_values(by="date_parsed")
            timeline_summary = df_plot.groupby(df_plot["date_parsed"].dt.strftime("%Y-%m-%d"))["amount"].agg(["sum", "count"]).reset_index()
            timeline_summary.columns = ["Posting Date", "Total Duplicate ($)", "Exception Count"]
            
            chart = alt.Chart(timeline_summary).mark_circle(size=120, color="#f59e0b").encode(
                x=alt.X("Posting Date:T", title="Disbursement Date"),
                y=alt.Y("Total Duplicate ($):Q", title="Disbursement Sum ($)"),
                size=alt.Size("Exception Count:Q", title="Exception Count", scale=alt.Scale(range=[80, 300])),
                tooltip=[alt.Tooltip("Posting Date:T", format="%Y-%m-%d"), alt.Tooltip("Total Duplicate ($):Q", format="$,.2f"), alt.Tooltip("Exception Count:Q")]
            ).properties(height=320)
            st.altair_chart(chart, use_container_width=True)
        else:
            st.info("Date information not available.")

def render_an02_split_charts(df_exc: pd.DataFrame, df_full: pd.DataFrame):
    """AN-02: Split Purchases Visualizations."""
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("##### 🏢 Split Purchase Total Spend by Vendor vs $10k Threshold")
        if "vendor_id" in df_exc.columns and "amount" in df_exc.columns:
            v_agg = df_exc.groupby("vendor_id")["amount"].sum().reset_index()
            v_agg = v_agg.sort_values(by="amount", ascending=False).head(10)
            
            bar = alt.Chart(v_agg).mark_bar(color="#f97316", cornerRadiusTopRight=4, cornerRadiusBottomRight=4).encode(
                x=alt.X("amount:Q", title="Aggregated Split Spend ($)"),
                y=alt.Y("vendor_id:N", sort="-x", title="Vendor ID"),
                tooltip=[alt.Tooltip("vendor_id:N"), alt.Tooltip("amount:Q", format="$,.2f", title="Total Sum ($)")]
            )
            rule = alt.Chart(pd.DataFrame({"x": [10000.0]})).mark_rule(color="#ef4444", strokeDash=[4, 4], strokeWidth=2).encode(x="x:Q")
            chart = (bar + rule).properties(height=320)
            st.altair_chart(chart, use_container_width=True)
        else:
            st.info("Vendor split data not available.")

    with c2:
        st.markdown("##### 🔍 Individual Invoices Clustering Under $10,000 Threshold")
        if "amount" in df_exc.columns:
            df_plot = df_exc.copy()
            df_plot["Invoice Index"] = range(1, len(df_plot) + 1)
            scatter = alt.Chart(df_plot).mark_circle(size=90, color="#38bdf8").encode(
                x=alt.X("Invoice Index:Q", title="Flagged Invoice #"),
                y=alt.Y("amount:Q", title="Individual Amount ($)", scale=alt.Scale(domain=[0, 11000])),
                color=alt.Color("vendor_id:N", title="Vendor", legend=None),
                tooltip=[alt.Tooltip("vendor_id:N", title="Vendor"), alt.Tooltip("amount:Q", title="Amount ($)", format="$,.2f"), alt.Tooltip("invoice_no:N", title="Invoice No")]
            )
            threshold_line = alt.Chart(pd.DataFrame({"y": [10000.0]})).mark_rule(color="#ef4444", strokeDash=[6, 4], strokeWidth=2).encode(y="y:Q")
            chart = (scatter + threshold_line).properties(height=320)
            st.altair_chart(chart, use_container_width=True)
        else:
            st.info("Amount data not available.")

def render_an03_weekend_charts(df_exc: pd.DataFrame, df_full: pd.DataFrame):
    """AN-03: Weekend Postings Visualizations."""
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("##### 📊 Transaction Volume by Day of Week")
        if "date" in df_full.columns:
            df_copy = df_full.copy()
            df_copy["parsed"] = pd.to_datetime(df_copy["date"], errors="coerce")
            df_copy = df_copy.dropna(subset=["parsed"])
            df_copy["day_name"] = df_copy["parsed"].dt.day_name()
            df_copy["is_weekend"] = df_copy["parsed"].dt.dayofweek.isin([5, 6])
            
            day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            day_counts = df_copy.groupby(["day_name", "is_weekend"])["amount"].agg(["count", "sum"]).reset_index()
            day_counts["day_name"] = pd.Categorical(day_counts["day_name"], categories=day_order, ordered=True)
            day_counts = day_counts.sort_values(by="day_name")
            
            chart = alt.Chart(day_counts).mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4).encode(
                x=alt.X("day_name:N", sort=day_order, title="Day of Week"),
                y=alt.Y("count:Q", title="Transaction Count"),
                color=alt.condition(
                    alt.datum.is_weekend,
                    alt.value("#ef4444"), # Red for Weekend
                    alt.value("#3b82f6")  # Blue for Weekday
                ),
                tooltip=[alt.Tooltip("day_name:N", title="Day"), alt.Tooltip("count:Q", title="Volume"), alt.Tooltip("sum:Q", format="$,.2f", title="Total Spend ($)")]
            ).properties(height=320)
            st.altair_chart(chart, use_container_width=True)
        else:
            st.info("Date data not available.")

    with c2:
        st.markdown("##### 👤 Weekend Postings by System User")
        if "user_id" in df_exc.columns and "amount" in df_exc.columns:
            u_agg = df_exc.groupby("user_id")["amount"].agg(["count", "sum"]).reset_index()
            u_agg = u_agg.sort_values(by="sum", ascending=False).head(10)
            chart = alt.Chart(u_agg).mark_bar(color="#a855f7", cornerRadiusTopRight=4, cornerRadiusBottomRight=4).encode(
                x=alt.X("sum:Q", title="Total Weekend Postings ($)"),
                y=alt.Y("user_id:N", sort="-x", title="User ID"),
                tooltip=[alt.Tooltip("user_id:N", title="User"), alt.Tooltip("count:Q", title="Transactions"), alt.Tooltip("sum:Q", format="$,.2f", title="Weekend Spend ($)")]
            ).properties(height=320)
            st.altair_chart(chart, use_container_width=True)
        else:
            st.info("User data not available.")

def render_an04_round_charts(df_exc: pd.DataFrame, df_full: pd.DataFrame):
    """AN-04: Round Figures Visualizations."""
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("##### 🎯 Distribution of High-Value Round Sums")
        if "amount" in df_exc.columns:
            amt_counts = df_exc["amount"].value_counts().reset_index()
            amt_counts.columns = ["Round Amount ($)", "Count"]
            amt_counts["Amount_Str"] = amt_counts["Round Amount ($)"].apply(lambda x: f"${x:,.0f}")
            amt_counts = amt_counts.sort_values(by="Round Amount ($)")
            
            chart = alt.Chart(amt_counts).mark_bar(color="#06b6d4", cornerRadiusTopLeft=4, cornerRadiusTopRight=4).encode(
                x=alt.X("Amount_Str:N", sort=list(amt_counts["Amount_Str"]), title="Disbursement Tier"),
                y=alt.Y("Count:Q", title="Frequency"),
                tooltip=[alt.Tooltip("Amount_Str:N", title="Tier"), alt.Tooltip("Count:Q", title="Vouchers")]
            ).properties(height=320)
            st.altair_chart(chart, use_container_width=True)
        else:
            st.info("Amount data not available.")

    with c2:
        st.markdown("##### 🏢 Top Vendors Receiving Round Figures")
        if "vendor_id" in df_exc.columns and "amount" in df_exc.columns:
            v_agg = df_exc.groupby("vendor_id")["amount"].sum().reset_index()
            v_agg = v_agg.sort_values(by="amount", ascending=False).head(10)
            chart = alt.Chart(v_agg).mark_bar(color="#3b82f6", cornerRadiusTopRight=4, cornerRadiusBottomRight=4).encode(
                x=alt.X("amount:Q", title="Total Round Payments ($)"),
                y=alt.Y("vendor_id:N", sort="-x", title="Vendor ID"),
                tooltip=[alt.Tooltip("vendor_id:N", title="Vendor"), alt.Tooltip("amount:Q", format="$,.2f", title="Total ($)")]
            ).properties(height=320)
            st.altair_chart(chart, use_container_width=True)
        else:
            st.info("Vendor data not available.")

def render_an05_below_threshold_charts(df_exc: pd.DataFrame, df_full: pd.DataFrame):
    """AN-05: Transactions Just Below Approval Threshold."""
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("##### 📉 Threshold Proximity Clustering ($9,500 – $9,999)")
        if "amount" in df_exc.columns:
            chart = alt.Chart(df_exc).mark_bar(color="#f59e0b", bin=alt.Bin(maxbins=15)).encode(
                x=alt.X("amount:Q", title="Transaction Amount ($)", scale=alt.Scale(domain=[9500, 10000])),
                y=alt.Y("count()", title="Voucher Count"),
                tooltip=[alt.Tooltip("count()", title="Transactions in Bin")]
            ).properties(height=320)
            st.altair_chart(chart, use_container_width=True)
        else:
            st.info("Amount data not available.")

    with c2:
        st.markdown("##### 👤 Near-Threshold Approvers / Originators")
        user_col = "approver_id" if "approver_id" in df_exc.columns and df_exc["approver_id"].dropna().any() else "user_id"
        if user_col in df_exc.columns and "amount" in df_exc.columns:
            u_agg = df_exc.groupby(user_col)["amount"].agg(["count", "sum"]).reset_index()
            u_agg = u_agg.sort_values(by="count", ascending=False).head(10)
            chart = alt.Chart(u_agg).mark_bar(color="#ec4899", cornerRadiusTopRight=4, cornerRadiusBottomRight=4).encode(
                x=alt.X("count:Q", title="Voucher Count"),
                y=alt.Y(f"{user_col}:N", sort="-x", title="Approver / User"),
                tooltip=[alt.Tooltip(f"{user_col}:N"), alt.Tooltip("count:Q"), alt.Tooltip("sum:Q", format="$,.2f", title="Total Spend ($)")]
            ).properties(height=320)
            st.altair_chart(chart, use_container_width=True)
        else:
            st.info("Approver data not available.")

def render_an06_benford_charts(benford_res: Dict[str, Any]):
    """AN-06: Benford's Law First Digit Distribution Visualizations."""
    digits_data = benford_res.get("digits", {})
    if not digits_data:
        st.info("Benford distribution data not available.")
        return

    plot_rows = []
    for d, stats in digits_data.items():
        plot_rows.append({"Digit": int(d), "Frequency (%)": stats.get("actual_pct", 0), "Type": "Actual Frequency"})
        plot_rows.append({"Digit": int(d), "Frequency (%)": stats.get("expected_pct", 0), "Type": "Benford Expected"})

    df_benford = pd.DataFrame(plot_rows)
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("##### 📊 Actual vs Expected Benford Distribution")
        chart1 = alt.Chart(df_benford).mark_bar().encode(
            x=alt.X("Digit:O", title="Leading Digit (1–9)"),
            y=alt.Y("Frequency (%):Q", title="Percentage (%)"),
            color=alt.Color("Type:N", scale=alt.Scale(domain=["Actual Frequency", "Benford Expected"], range=["#38bdf8", "#64748b"])),
            xOffset="Type:N",
            tooltip=[alt.Tooltip("Digit:O"), alt.Tooltip("Type:N"), alt.Tooltip("Frequency (%):Q", format=".2f")]
        ).properties(height=320)
        st.altair_chart(chart1, use_container_width=True)

    with c2:
        st.markdown("##### 🔍 Percentage Variance by First Digit")
        variance_rows = []
        for d, stats in digits_data.items():
            variance_rows.append({"Digit": int(d), "Variance (%)": stats.get("variance", 0)})
        df_var = pd.DataFrame(variance_rows)
        chart2 = alt.Chart(df_var).mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4).encode(
            x=alt.X("Digit:O", title="Leading Digit (1–9)"),
            y=alt.Y("Variance (%):Q", title="Variance from Benford (%)"),
            color=alt.condition(
                alt.datum["Variance (%)"] > 0,
                alt.value("#ef4444"), # Over-represented
                alt.value("#10b981")  # Under-represented
            ),
            tooltip=[alt.Tooltip("Digit:O"), alt.Tooltip("Variance (%):Q", format="+.2f")]
        ).properties(height=320)
        st.altair_chart(chart2, use_container_width=True)

def render_an07_approvals_charts(df_exc: pd.DataFrame, df_full: pd.DataFrame):
    """AN-07: Missing Approvals Visualizations."""
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("##### 🏢 Unapproved Invoices by Vendor")
        if "vendor_id" in df_exc.columns and "amount" in df_exc.columns:
            v_agg = df_exc.groupby("vendor_id")["amount"].agg(["count", "sum"]).reset_index()
            v_agg = v_agg.sort_values(by="sum", ascending=False).head(10)
            chart = alt.Chart(v_agg).mark_bar(color="#ef4444", cornerRadiusTopRight=4, cornerRadiusBottomRight=4).encode(
                x=alt.X("sum:Q", title="Unapproved Spend ($)"),
                y=alt.Y("vendor_id:N", sort="-x", title="Vendor ID"),
                tooltip=[alt.Tooltip("vendor_id:N"), alt.Tooltip("count:Q", title="Unapproved Invoices"), alt.Tooltip("sum:Q", format="$,.2f", title="Unapproved Sum ($)")]
            ).properties(height=320)
            st.altair_chart(chart, use_container_width=True)
        else:
            st.info("Vendor data not available.")

    with c2:
        st.markdown("##### 👤 Unapproved Transactions by Originating User")
        if "user_id" in df_exc.columns and "amount" in df_exc.columns:
            u_agg = df_exc.groupby("user_id")["amount"].agg(["count", "sum"]).reset_index()
            u_agg = u_agg.sort_values(by="count", ascending=False).head(10)
            chart = alt.Chart(u_agg).mark_bar(color="#f59e0b", cornerRadiusTopRight=4, cornerRadiusBottomRight=4).encode(
                x=alt.X("count:Q", title="Unapproved Count"),
                y=alt.Y("user_id:N", sort="-x", title="Originating User"),
                tooltip=[alt.Tooltip("user_id:N"), alt.Tooltip("count:Q", title="Invoices"), alt.Tooltip("sum:Q", format="$,.2f", title="Total Amount ($)")]
            ).properties(height=320)
            st.altair_chart(chart, use_container_width=True)
        else:
            st.info("User data not available.")

def render_an08_threeway_charts(df_exc: pd.DataFrame, df_full: pd.DataFrame):
    """AN-08: Three-Way Match Variances Visualizations."""
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("##### 📦 Quantity Variances (Billed vs Received)")
        if "inv_qty" in df_exc.columns and "receipt_qty" in df_exc.columns:
            df_plot = df_exc.copy()
            df_plot["qty_discrepancy"] = df_plot["inv_qty"] - df_plot["receipt_qty"]
            df_qty = df_plot[df_plot["qty_discrepancy"] != 0].head(10)
            
            chart = alt.Chart(df_qty).mark_bar(color="#ef4444", cornerRadiusTopRight=4, cornerRadiusBottomRight=4).encode(
                x=alt.X("qty_discrepancy:Q", title="Overbilled Quantity (Units)"),
                y=alt.Y("invoice_no:N", sort="-x", title="Invoice No"),
                tooltip=[alt.Tooltip("invoice_no:N"), alt.Tooltip("vendor_id:N"), alt.Tooltip("receipt_qty:Q", title="Received Qty"), alt.Tooltip("inv_qty:Q", title="Billed Qty"), alt.Tooltip("qty_discrepancy:Q", title="Excess Billed")]
            ).properties(height=320)
            st.altair_chart(chart, use_container_width=True)
        else:
            st.info("Quantity matching columns not found.")

    with c2:
        st.markdown("##### 💵 Unit Price Markups Billed over PO Agreed Price")
        if "po_price" in df_exc.columns and "inv_price" in df_exc.columns:
            df_plot = df_exc.copy()
            df_plot["price_markup_pct"] = ((df_plot["inv_price"] - df_plot["po_price"]) / df_plot["po_price"].replace(0, 1)) * 100
            df_price = df_plot[df_plot["price_markup_pct"] > 0].sort_values(by="price_markup_pct", ascending=False).head(10)
            
            chart = alt.Chart(df_price).mark_bar(color="#f59e0b", cornerRadiusTopRight=4, cornerRadiusBottomRight=4).encode(
                x=alt.X("price_markup_pct:Q", title="Price Markup (%)"),
                y=alt.Y("invoice_no:N", sort="-x", title="Invoice No"),
                tooltip=[alt.Tooltip("invoice_no:N"), alt.Tooltip("vendor_id:N"), alt.Tooltip("po_price:Q", format="$,.2f", title="PO Agreed Unit Price"), alt.Tooltip("inv_price:Q", format="$,.2f", title="Billed Unit Price"), alt.Tooltip("price_markup_pct:Q", format=".1f", title="Markup %")]
            ).properties(height=320)
            st.altair_chart(chart, use_container_width=True)
        else:
            st.info("Price matching columns not found.")

def render_generic_charts(df_exc: pd.DataFrame, df_full: pd.DataFrame):
    """Generic fallback visualizations for any other test."""
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("##### 🏢 Exception Distribution by Vendor")
        if "vendor_id" in df_exc.columns:
            v_agg = df_exc["vendor_id"].value_counts().reset_index().head(10)
            v_agg.columns = ["vendor_id", "count"]
            chart = alt.Chart(v_agg).mark_bar(color="#3b82f6", cornerRadiusTopRight=4, cornerRadiusBottomRight=4).encode(
                x=alt.X("count:Q", title="Exception Count"),
                y=alt.Y("vendor_id:N", sort="-x", title="Vendor ID"),
                tooltip=[alt.Tooltip("vendor_id:N"), alt.Tooltip("count:Q")]
            ).properties(height=320)
            st.altair_chart(chart, use_container_width=True)
        else:
            st.info("Vendor details not present.")

    with c2:
        st.markdown("##### 💰 Value Distribution of Exceptions")
        if "amount" in df_exc.columns:
            chart = alt.Chart(df_exc).mark_bar(color="#10b981", bin=alt.Bin(maxbins=20)).encode(
                x=alt.X("amount:Q", title="Exception Value ($)"),
                y=alt.Y("count()", title="Frequency"),
                tooltip=[alt.Tooltip("count()")]
            ).properties(height=320)
            st.altair_chart(chart, use_container_width=True)
        else:
            st.info("Amount values not present.")

def render_test_visualizations(test_id: str, df_exc: pd.DataFrame, df_full: pd.DataFrame, benford_res: Optional[Dict[str, Any]] = None):
    """Dispatches the appropriate interactive Altair visualization suite for the given audit procedure."""
    if test_id == "AN-01":
        render_an01_duplicate_charts(df_exc, df_full)
    elif test_id == "AN-02":
        render_an02_split_charts(df_exc, df_full)
    elif test_id == "AN-03":
        render_an03_weekend_charts(df_exc, df_full)
    elif test_id == "AN-04":
        render_an04_round_charts(df_exc, df_full)
    elif test_id == "AN-05":
        render_an05_below_threshold_charts(df_exc, df_full)
    elif test_id == "AN-06" and benford_res:
        render_an06_benford_charts(benford_res)
    elif test_id == "AN-07":
        render_an07_approvals_charts(df_exc, df_full)
    elif test_id == "AN-08":
        render_an08_threeway_charts(df_exc, df_full)
    else:
        render_generic_charts(df_exc, df_full)

def render_sod_visualizations(conflicts: List[Dict[str, Any]], df_user_access: pd.DataFrame):
    """Renders interactive charts for Segregation of Duties conflict analysis."""
    if not conflicts:
        st.info("No SoD conflicts to visualize.")
        return

    df_c = pd.DataFrame(conflicts)
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("##### 🛡️ Conflicting Privileges by Toxic Rule Code")
        if "rule_code" in df_c.columns:
            rule_counts = df_c.groupby(["rule_code", "severity"]).size().reset_index(name="count")
            chart = alt.Chart(rule_counts).mark_bar(cornerRadiusTopRight=4, cornerRadiusBottomRight=4).encode(
                x=alt.X("count:Q", title="Number of Toxic Assignments"),
                y=alt.Y("rule_code:N", sort="-x", title="SoD Rule Code"),
                color=alt.Color("severity:N", scale=alt.Scale(domain=["Critical", "High", "Medium"], range=["#ef4444", "#f59e0b", "#3b82f6"]), title="Severity"),
                tooltip=[alt.Tooltip("rule_code:N", title="Rule"), alt.Tooltip("severity:N"), alt.Tooltip("count:Q", title="Violations")]
            ).properties(height=320)
            st.altair_chart(chart, use_container_width=True)

    with c2:
        st.markdown("##### 🏢 Conflict Distribution Across Process Lanes")
        lanes = []
        for c in conflicts:
            for l in c.get("impacted_lanes", []):
                lanes.append({"lane": l, "severity": c.get("severity", "High")})
        if lanes:
            df_lanes = pd.DataFrame(lanes)
            lane_counts = df_lanes.groupby(["lane", "severity"]).size().reset_index(name="count")
            chart2 = alt.Chart(lane_counts).mark_bar(cornerRadiusTopRight=4, cornerRadiusBottomRight=4).encode(
                x=alt.X("count:Q", title="Conflicting Roles"),
                y=alt.Y("lane:N", sort="-x", title="Process Lane"),
                color=alt.Color("severity:N", scale=alt.Scale(domain=["Critical", "High", "Medium"], range=["#ef4444", "#f59e0b", "#3b82f6"]), title="Severity"),
                tooltip=[alt.Tooltip("lane:N", title="Lane"), alt.Tooltip("count:Q", title="Conflicts")]
            ).properties(height=320)
            st.altair_chart(chart2, use_container_width=True)

def render_process_mining_visualizations(pm_data: Dict[str, Any], df_event_log: pd.DataFrame):
    """Renders interactive charts for Process Mining variant & bypass analysis."""
    variants = pm_data.get("variants", [])
    bypasses = pm_data.get("bypassed_cases", [])
    if not variants:
        st.info("No process mining variants to visualize.")
        return

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("##### 🔄 Process Execution Flow Variant Distribution")
        df_vars = pd.DataFrame(variants).copy()
        df_vars["Variant"] = [f"Variant {chr(65+i)} ({v.get('case_count')} cases)" for i, v in enumerate(variants)]
        df_vars["Status"] = df_vars["compliant"].apply(lambda x: "Compliant Golden Path" if x else "Control Bypass")
        
        chart1 = alt.Chart(df_vars).mark_bar(cornerRadiusTopRight=4, cornerRadiusBottomRight=4).encode(
            x=alt.X("frequency_pct:Q", title="Share of Total Population (%)"),
            y=alt.Y("Variant:N", sort="-x", title="Identified Variant Pathway"),
            color=alt.Color("Status:N", scale=alt.Scale(domain=["Compliant Golden Path", "Control Bypass"], range=["#10b981", "#ef4444"]), title="Control State"),
            tooltip=[alt.Tooltip("Variant:N"), alt.Tooltip("frequency_pct:Q", title="Share (%)", format=".1f"), alt.Tooltip("case_count:Q", title="Cases"), alt.Tooltip("Status:N")]
        ).properties(height=320)
        st.altair_chart(chart1, use_container_width=True)

    with c2:
        st.markdown("##### 🚨 Control Gate Bypasses by Root Violation Type")
        if bypasses:
            df_b = pd.DataFrame(bypasses).copy()
            df_b["Violation Category"] = df_b["reason"].apply(
                lambda r: "Missing Goods Receipt (GRN)" if "receipt" in r.lower() or "grn" in r.lower() 
                else ("Retroactive PR Approval" if "retroactive" in r.lower() or "prior" in r.lower()
                else "Emergency / Unbudgeted PO")
            )
            b_counts = df_b.groupby(["Violation Category", "severity"]).size().reset_index(name="count")
            chart2 = alt.Chart(b_counts).mark_bar(cornerRadiusTopRight=4, cornerRadiusBottomRight=4).encode(
                x=alt.X("count:Q", title="Number of Bypassed Cases"),
                y=alt.Y("Violation Category:N", sort="-x", title="Control Gate Bypassed"),
                color=alt.Color("severity:N", scale=alt.Scale(domain=["Critical", "High", "Medium"], range=["#ef4444", "#f59e0b", "#38bdf8"]), title="Severity"),
                tooltip=[alt.Tooltip("Violation Category:N"), alt.Tooltip("count:Q", title="Cases Affected"), alt.Tooltip("severity:N")]
            ).properties(height=320)
            st.altair_chart(chart2, use_container_width=True)
        else:
            st.success("All transactions adhered strictly to defined control gates!")

