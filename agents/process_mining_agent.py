import json
import pandas as pd
from typing import Dict, Any, List
from graphs.state import FieldAIState
from core.llm import llm

def generate_process_mining_ai_report(
    total_cases: int,
    total_events: int,
    distinct_variants: int,
    compliant_cases: int,
    conformance_rate: float,
    bypassed_cases_count: int,
    bypass_rate: float,
    variants: List[Dict[str, Any]],
    bypasses: List[Dict[str, Any]]
) -> str:
    """Generates an executive Process Mining Conformance & Control Bypass Report via LLM with structured fallback."""
    top_variant = variants[0]["variant_flow"] if variants else "Standard P2P Flow"
    top_var_freq = variants[0]["frequency_pct"] if variants else 0.0

    system_prompt = (
        "You are FieldAI Principal Process Mining & Operational Assurance Auditor. "
        "Generate a formal, executive Process Conformance & Control Gate Bypass Report based on ERP event logs. "
        "Use GitHub markdown with clear section headers, professional audit tone, and quantified metrics."
    )

    prompt = f"""
ERP Procure-to-Pay (P2P) Event Log Process Mining Assessment
Population Analyzed: {total_cases:,} cases across {total_events:,} discrete system audit events
Flow Variants Identified: {distinct_variants} distinct execution pathways
Golden Path Compliance: {compliant_cases:,} cases ({conformance_rate}% conformance rate)
Control Gate Bypasses: {bypassed_cases_count:,} cases ({bypass_rate}% deviation rate)
Dominant Process Path: {top_variant} ({top_var_freq}% frequency)

Please generate a formal Internal Audit Process Mining Conformance Report with the following 4 sections:
### 1. Executive Summary & Audit Conformance Observation
### 2. Process Pathway Deviations & Gate Circumvention Analysis
### 3. Operational Inefficiency, Working Capital & Fraud Risk Impact
### 4. Actionable Process Governance & ERP Hard-Stop Recommendations (Numbered 1-3)
"""
    try:
        report_text = llm.generate_text(prompt, system_prompt)
        if report_text and "Executive Summary" in report_text and len(report_text.strip()) > 150:
            return report_text.strip()
    except Exception as e:
        print(f"[ProcessMiningAgent] LLM generation error: {e}")

    return f"""### 1. Executive Summary & Audit Conformance Observation
FieldAI executed an automated **Process Mining & Conformance Assessment** across **{total_cases:,} end-to-end transaction cases** comprising **{total_events:,} logged system audit activities**. The mining algorithm reconstructed **{distinct_variants} unique execution pathways**, revealing an overall process conformance rate of **{conformance_rate}%** ({compliant_cases:,} fully compliant cases).

Critically, **{bypassed_cases_count:,} transactions ({bypass_rate}% of the population)** bypassed mandatory internal control gates, primarily through omission of physical goods receipt verification (GRN) prior to invoice entry, and retroactive purchase order approvals executed post-invoice receipt.

### 2. Process Pathway Deviations & Gate Circumvention Analysis
- **Missing Goods Receipt Verification (GRN Bypass):** Transactions proceeded directly from Purchase Order issuance to Invoice Posting and Payment Release without any documented warehouse or services receipt acknowledgement. This circumvents standard 3-Way Matching controls and invalidates liability verification.
- **Retroactive Purchase Requisitions & Approvals:** Invoices were posted in the financial ledger prior to formal requisition approval, demonstrating that commitments were entered into off-system with suppliers before budget authorization was secured.
- **Variant Fragmentation:** While the primary golden path accounts for **{top_var_freq}%** of transactions, the proliferation of non-standard variants indicates fragmented procurement habits and ad-hoc operational workarounds.

### 3. Operational Inefficiency, Working Capital & Fraud Risk Impact
- **Disbursement for Undelivered Goods:** Bypassing Goods Receipt significantly elevates the risk of settling invoices for undelivered, damaged, or phantom goods, resulting in unrecoverable cash loss.
- **Maverick Spend & Budgetary Overruns:** Retroactive purchase order approvals diminish executive budget governance, leading to unauthorized commitments and unbudgeted departmental expenditure.
- **Rework Cycles & Extended Lead Times:** Deviation from standard process paths increases transaction dispute resolution friction, vendor inquiry volume, and manual AP processing time.

### 4. Actionable Process Governance & ERP Hard-Stop Recommendations
1. **Enforce Mandatory 3-Way Match System Hard-Stops:** Configure ERP matching tolerance logic (e.g. SAP Three-Way Match / E-Invoicing Gate) to strictly block invoice posting for PO line items requiring goods receipt until a valid GRN document has been entered.
2. **Automate Purchase Order Cut-Off Controls:** Implement system validation preventing invoice registration against POs created after the supplier invoice issuance date, flagging retroactive orders for formal executive override and internal audit review.
3. **Establish Real-Time Continuous Process Conformance Dashboards:** Integrate automated weekly event-log mining into Procurement and Internal Audit monitoring routines to detect gate circumventions before bi-weekly payment runs are executed."""

def run(state: FieldAIState) -> Dict[str, Any]:
    """
    Process Mining Agent (Option 10):
    Calculates execution variants, cycle times, and flags transactions that bypass key control gates.
    """
    test_request = state.get("test_request", {})
    event_log_df = test_request.get("event_log")

    if event_log_df is None:
        from pathlib import Path
        for p in [Path("sample_data/erp_event_log_large.csv"), Path("sample_data/erp_event_log.csv")]:
            if p.exists():
                try:
                    event_log_df = pd.read_csv(p)
                    break
                except Exception:
                    pass

    if event_log_df is None:
        # Default fallback sample ERP event log
        event_log_df = pd.DataFrame([
            {"case_id": "PO-1001", "activity": "Create PR", "timestamp": "2026-01-02 09:00", "user": "John"},
            {"case_id": "PO-1001", "activity": "Approve PR", "timestamp": "2026-01-02 11:30", "user": "Sarah"},
            {"case_id": "PO-1001", "activity": "Issue PO", "timestamp": "2026-01-02 14:00", "user": "Tariq"},
            {"case_id": "PO-1001", "activity": "Record GRN", "timestamp": "2026-01-05 10:00", "user": "Ali"},
            {"case_id": "PO-1001", "activity": "Post Invoice", "timestamp": "2026-01-06 15:00", "user": "Fatima"},
            {"case_id": "PO-1001", "activity": "Release Payment", "timestamp": "2026-01-08 12:00", "user": "Zaid"},
            
            # Variant B: GRN Bypassed (Goods receipt missing before invoice)
            {"case_id": "PO-1002", "activity": "Create PR", "timestamp": "2026-01-03 09:00", "user": "Elena"},
            {"case_id": "PO-1002", "activity": "Approve PR", "timestamp": "2026-01-03 10:00", "user": "Sarah"},
            {"case_id": "PO-1002", "activity": "Issue PO", "timestamp": "2026-01-03 12:00", "user": "Tariq"},
            {"case_id": "PO-1002", "activity": "Post Invoice", "timestamp": "2026-01-04 11:00", "user": "Fatima"}, # GRN skipped!
            {"case_id": "PO-1002", "activity": "Release Payment", "timestamp": "2026-01-05 14:00", "user": "Zaid"},

            # Variant C: Retroactive PO Approval (Invoice received before PO approved)
            {"case_id": "PO-1003", "activity": "Create PR", "timestamp": "2026-01-04 10:00", "user": "John"},
            {"case_id": "PO-1003", "activity": "Post Invoice", "timestamp": "2026-01-04 14:00", "user": "Fatima"}, # Before approval!
            {"case_id": "PO-1003", "activity": "Approve PR", "timestamp": "2026-01-06 16:00", "user": "Sarah"},
            {"case_id": "PO-1003", "activity": "Release Payment", "timestamp": "2026-01-07 10:00", "user": "Zaid"},
        ])

    event_log_df["timestamp"] = pd.to_datetime(event_log_df["timestamp"])
    sorted_log = event_log_df.sort_values(by=["case_id", "timestamp"])

    # Group by case to find process paths
    paths = sorted_log.groupby("case_id")["activity"].apply(lambda acts: " -> ".join(acts)).reset_index()
    variant_counts = paths["activity"].value_counts().to_dict()

    total_cases = len(paths)
    total_events = len(event_log_df)
    variants = []
    bypassed_cases = []

    for path_str, count in variant_counts.items():
        is_compliant = ("Record GRN" in path_str) and (path_str.index("Record GRN") < path_str.index("Post Invoice") if "Post Invoice" in path_str and "Record GRN" in path_str else True)
        variants.append({
            "variant_flow": path_str,
            "case_count": count,
            "frequency_pct": round((count / total_cases) * 100, 1),
            "compliant": is_compliant
        })

    # Find cases where GRN was skipped or retroactive approvals occurred
    for case_id, group in sorted_log.groupby("case_id"):
        acts = list(group["activity"])
        if "Post Invoice" in acts and "Record GRN" not in acts:
            bypassed_cases.append({
                "case_id": case_id,
                "reason": "Control Bypass: Goods receipt (GRN) was omitted before invoice was posted for payment.",
                "severity": "High"
            })
        elif "Post Invoice" in acts and "Approve PR" in acts:
            inv_time = group[group["activity"] == "Post Invoice"]["timestamp"].iloc[0]
            appr_time = group[group["activity"] == "Approve PR"]["timestamp"].iloc[0]
            if inv_time < appr_time:
                bypassed_cases.append({
                    "case_id": case_id,
                    "reason": "Control Violation: Invoice posted prior to retroactive PR approval.",
                    "severity": "Medium"
                })

    compliant_cases = sum(v.get("case_count", 0) for v in variants if v.get("compliant"))
    conformance_rate = round((compliant_cases / total_cases) * 100, 1) if total_cases else 0.0
    bypassed_count = len(bypassed_cases)
    bypass_rate = round((bypassed_count / total_cases) * 100, 1) if total_cases else 0.0

    ai_report = generate_process_mining_ai_report(
        total_cases=total_cases,
        total_events=total_events,
        distinct_variants=len(variants),
        compliant_cases=compliant_cases,
        conformance_rate=conformance_rate,
        bypassed_cases_count=bypassed_count,
        bypass_rate=bypass_rate,
        variants=variants,
        bypasses=bypassed_cases
    )

    summary_msg = f"Mined {total_cases} cases across {len(variants)} flow variants with {conformance_rate}% conformance ({bypassed_count} control bypasses detected)."

    return {
        "process_mining": {
            "total_cases": total_cases,
            "total_events": total_events,
            "distinct_variants": len(variants),
            "variants": variants,
            "bypassed_cases": bypassed_cases,
            "conformance_rate": conformance_rate,
            "bypass_rate": bypass_rate,
            "compliant_cases": compliant_cases,
            "ai_report": ai_report
        },
        "test_result": {
            "summary": summary_msg,
            "exceptions_count": bypassed_count,
            "exceptions": bypassed_cases,
            "ai_report": ai_report,
            "total_cases": total_cases,
            "conformance_rate": conformance_rate,
            "bypass_rate": bypass_rate,
            "compliant_cases": compliant_cases
        }
    }
