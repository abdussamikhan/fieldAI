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

    # Default sample user-access matrix if not provided
    if not user_access_data:
        user_access_data = [
            {"user_id": "U101", "name": "Ahmed Al-Harbi", "assigned_roles": ["Vendor Master Admin", "AP Disbursement Clerk"]},
            {"user_id": "U102", "name": "Elena Rostova", "assigned_roles": ["PO Requisitioner", "PO Approver Tier 1"]},
            {"user_id": "U103", "name": "Michael Chang", "assigned_roles": ["Warehouse Logistics Receiving"]},
            {"user_id": "U104", "name": "Fatima Zahra", "assigned_roles": ["AP Invoice Processor", "Treasury Payment Release"]}
        ]

    # Retrieve rules from sod_rules table
    rules = db.fetch_all("SELECT rule_code, function_a, function_b, risk_description, severity FROM sod_rules;")

    conflicts_detected = []
    
    # Conflict evaluation
    for u in user_access_data:
        roles = u.get("assigned_roles", [])
        roles_lower = " ".join(roles).lower()

        # Check SOD-01: Vendor + Payment
        if any("vendor" in r.lower() for r in roles) and any("disbursement" in r.lower() or "payment" in r.lower() for r in roles):
            conflicts_detected.append({
                "rule_code": "SOD-01",
                "user_id": u.get("user_id"),
                "user_name": u.get("name"),
                "conflicting_roles": roles,
                "risk": "User can create fictitious vendors and disburse payments directly to them.",
                "severity": "High",
                "impacted_lanes": ["Procurement", "Finance"]
            })

        # Check SOD-02: PO Create + PO Approve
        if any("requisitioner" in r.lower() or "buyer" in r.lower() for r in roles) and any("approver" in r.lower() for r in roles):
            conflicts_detected.append({
                "rule_code": "SOD-02",
                "user_id": u.get("user_id"),
                "user_name": u.get("name"),
                "conflicting_roles": roles,
                "risk": "User can initiate purchase orders and approve them without independent review.",
                "severity": "High",
                "impacted_lanes": ["Operations", "Procurement"]
            })

        # Check SOD-04: Invoice Entry + Payment Release
        if any("invoice" in r.lower() for r in roles) and any("payment release" in r.lower() or "release" in r.lower() for r in roles):
            conflicts_detected.append({
                "rule_code": "SOD-04",
                "user_id": u.get("user_id"),
                "user_name": u.get("name"),
                "conflicting_roles": roles,
                "risk": "User can enter unauthorized invoices and release payment batches.",
                "severity": "High",
                "impacted_lanes": ["Finance"]
            })

    return {
        "sod_conflicts": conflicts_detected,
        "summary": f"Detected {len(conflicts_detected)} toxic SoD permission combinations across {len(user_access_data)} users."
    }
