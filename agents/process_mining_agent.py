import json
import pandas as pd
from typing import Dict, Any, List
from graphs.state import FieldAIState

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

    # Find cases where GRN was skipped
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

    return {
        "process_mining": {
            "total_cases": total_cases,
            "distinct_variants": len(variants),
            "variants": variants,
            "bypassed_cases": bypassed_cases
        }
    }
