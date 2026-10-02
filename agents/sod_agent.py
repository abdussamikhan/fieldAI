import json
from typing import Dict, Any, List
import pandas as pd
from graphs.state import FieldAIState
from core.db import db
from core.llm import llm

PROMPT_SOD_MAPPING = """You are FieldAI Segregation of Duties (SoD) Specialist.
Map the client system permission/role names to standard internal audit SoD business functions:
Functions:
- 'Vendor Creation/Maintenance'
- 'Payment Processing'
- 'Purchase Order Creation'
- 'Purchase Order Approval'
- 'Goods Receipt Entry'
- 'Invoice Entry'
- 'Payment Release / Signoff'
- 'Bank Account Reconciliation'
- 'User Security Admin'

Return JSON format:
{
  "mappings": [
    {"client_role": "SAP_MM_BUYER_01", "standard_function": "Purchase Order Creation"},
    {"client_role": "SAP_MM_APPROVER_02", "standard_function": "Purchase Order Approval"}
  ]
}"""

def run(state: FieldAIState) -> Dict[str, Any]:
    """
    SoD Agent (Option 13):
    Evaluates user-access permissions against conflicting SoD rules and maps conflicts to process lanes.
    """
    test_request = state.get("test_request", {})
    user_access_data = test_request.get("user_access")

    # If no data provided, load from sample CSV
    if user_access_data is None:
        import os
        from pathlib import Path
        csv_candidates = [
            Path("sample_data/user_access_matrix_large.csv"),
            Path("sample_data/user_access_matrix.csv")
        ]
        for p in csv_candidates:
            if p.exists():
                try:
                    user_access_data = pd.read_csv(p)
                    break
                except Exception:
                    pass

    # If user_access_data is a DataFrame, group rows by user_id
    if isinstance(user_access_data, pd.DataFrame):
        df = user_access_data.copy()
        name_col = "username" if "username" in df.columns else ("name" if "name" in df.columns else "user_name")
        role_col = "assigned_role" if "assigned_role" in df.columns else ("role" if "role" in df.columns else "roles")
        grouped = []
        if "user_id" in df.columns and role_col in df.columns:
            for uid, grp in df.groupby("user_id"):
                uname = grp[name_col].iloc[0] if name_col in grp.columns else str(uid)
                roles = grp[role_col].dropna().astype(str).tolist()
                dept = grp["department"].iloc[0] if "department" in grp.columns else "General"
                grouped.append({
                    "user_id": str(uid),
                    "name": uname,
                    "department": dept,
                    "assigned_roles": roles
                })
            user_access_data = grouped
        else:
            user_access_data = df.to_dict(orient="records")

    # Fallback default if still empty
    if not user_access_data:
        user_access_data = [
            {"user_id": "U101", "name": "Ahmed Al-Harbi", "assigned_roles": ["Vendor Master Admin", "AP Disbursement Clerk"]},
            {"user_id": "U102", "name": "Elena Rostova", "assigned_roles": ["PO Requisitioner", "PO Approver Tier 1"]},
            {"user_id": "U103", "name": "Michael Chang", "assigned_roles": ["Warehouse Logistics Receiving"]},
            {"user_id": "U104", "name": "Fatima Zahra", "assigned_roles": ["AP Invoice Processor", "Treasury Payment Release"]}
        ]

    conflicts_detected = []
    
    # Conflict evaluation
    for u in user_access_data:
        roles = u.get("assigned_roles", [])
        if isinstance(roles, str):
            roles = [r.strip() for r in roles.split(",") if r.strip()]
        roles_lower = [r.lower() for r in roles]

        # Check SOD-01: Vendor Creation + Payment/Disbursement
        if any("vendor" in r for r in roles_lower) and any("disbursement" in r or "payment" in r or "cashier" in r for r in roles_lower):
            conflicts_detected.append({
                "rule_code": "SOD-01",
                "user_id": u.get("user_id"),
                "user_name": u.get("name") or u.get("username"),
                "conflicting_roles": roles,
                "risk": "User can create fictitious vendors and disburse payments directly to them.",
                "severity": "High",
                "impacted_lanes": ["Procurement", "Finance"]
            })

        # Check SOD-02: PO Create + PO Approve
        if any("requisitioner" in r or "buyer" in r or "sourcing" in r for r in roles_lower) and any("approver" in r for r in roles_lower):
            conflicts_detected.append({
                "rule_code": "SOD-02",
                "user_id": u.get("user_id"),
                "user_name": u.get("name") or u.get("username"),
                "conflicting_roles": roles,
                "risk": "User can initiate purchase orders and approve them without independent review.",
                "severity": "High",
                "impacted_lanes": ["Operations", "Procurement"]
            })

        # Check SOD-03: PO Approval + Goods Receipt
        if any("approver" in r for r in roles_lower) and any("receiving" in r or "grn" in r or "warehouse" in r for r in roles_lower):
            conflicts_detected.append({
                "rule_code": "SOD-03",
                "user_id": u.get("user_id"),
                "user_name": u.get("name") or u.get("username"),
                "conflicting_roles": roles,
                "risk": "User can approve purchase commitments and acknowledge receipt of goods.",
                "severity": "High",
                "impacted_lanes": ["Operations", "Logistics"]
            })

        # Check SOD-04: Invoice Entry + Payment Release
        if any("invoice" in r for r in roles_lower) and any("payment release" in r or "release" in r or "treasury" in r for r in roles_lower):
            conflicts_detected.append({
                "rule_code": "SOD-04",
                "user_id": u.get("user_id"),
                "user_name": u.get("name") or u.get("username"),
                "conflicting_roles": roles,
                "risk": "User can enter unauthorized invoices and release payment batches.",
                "severity": "High",
                "impacted_lanes": ["Finance"]
            })

        # Check SOD-05: User Security Admin + Business Transaction Processing
        if any("security" in r or "admin" in r for r in roles_lower) and any("disbursement" in r or "clerk" in r or "accountant" in r or "buyer" in r for r in roles_lower):
            conflicts_detected.append({
                "rule_code": "SOD-05",
                "user_id": u.get("user_id"),
                "user_name": u.get("name") or u.get("username"),
                "conflicting_roles": roles,
                "risk": "Privileged user can grant self unauthorized transaction authorities and perform operational transactions.",
                "severity": "Critical",
                "impacted_lanes": ["IT Security", "Finance"]
            })

    summary_msg = f"Detected {len(conflicts_detected)} toxic SoD permission combinations across {len(user_access_data)} users."
    return {
        "sod_conflicts": conflicts_detected,
        "summary": summary_msg,
        "test_result": {
            "summary": summary_msg,
            "exceptions_count": len(conflicts_detected),
            "exceptions": conflicts_detected
        }
    }
