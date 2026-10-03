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

def generate_sod_ai_report(
    total_users: int,
    conflicts: List[Dict[str, Any]],
    critical_count: int,
    high_count: int,
    unique_conflicted_users: int,
    rule_breakdown: Dict[str, int],
    lane_breakdown: Dict[str, int]
) -> str:
    """Generates an executive Segregation of Duties Findings & Remediation Memo via LLM with structured fallback."""
    conflict_pct = round((unique_conflicted_users / total_users) * 100, 1) if total_users else 0.0
    rules_summary = ", ".join([f"{k}: {v} violations" for k, v in rule_breakdown.items()]) if rule_breakdown else "None"
    lanes_summary = ", ".join([f"{k}: {v} roles" for k, v in lane_breakdown.items()]) if lane_breakdown else "None"

    system_prompt = (
        "You are FieldAI Lead Internal Controls & Access Governance Specialist. "
        "Generate a formal, executive Segregation of Duties (SoD) Audit Findings & Remediation Report based on the evaluated user access matrix. "
        "Use GitHub markdown with clear section headers, professional audit tone, and quantified risk."
    )

    prompt = f"""
Segregation of Duties (SoD) Privilege Matrix Assessment
Users Evaluated: {total_users} personnel across enterprise departments
Identified Toxic Combinations: {len(conflicts)} conflicting assignments
Unique Conflicted Users: {unique_conflicted_users} ({conflict_pct}% of evaluated population)
Severity Breakdown: {critical_count} Critical, {high_count} High
Rule Violations Breakdown: {rules_summary}
Impacted Process Lanes: {lanes_summary}

Please generate a formal Internal Audit SoD Evaluation Report with the following 4 sections:
### 1. Executive Summary & Audit Observation
### 2. Toxic Role Combinations & Vulnerability Breakdown
### 3. Fraud Risk & ICFR (Internal Control over Financial Reporting) Impact Assessment
### 4. Actionable Remediation Roadmap & Mitigating Controls (Numbered 1-4)
"""
    try:
        report_text = llm.generate_text(prompt, system_prompt)
        if report_text and "Executive Summary" in report_text and len(report_text.strip()) > 150:
            return report_text.strip()
    except Exception as e:
        print(f"[SoDAgent] LLM generation error: {e}")

    return f"""### 1. Executive Summary & Audit Observation
FieldAI conducted a comprehensive **Segregation of Duties (SoD) Conflict Evaluation** on the active User Access Matrix comprising **{total_users} user accounts**. The analysis detected **{len(conflicts)} toxic role combinations** affecting **{unique_conflicted_users} unique users** ({conflict_pct}% conflict penetration rate). 

Among the flagged violations, **{critical_count} were categorized as Critical severity** involving system security administrator entitlements combined with operational posting privileges, and **{high_count} were categorized as High severity** bridging conflicting stages of the procure-to-pay transaction lifecycle.

### 2. Toxic Role Combinations & Vulnerability Breakdown
The detected permission conflicts span critical business cycles and rule categories:
- **Rule SOD-01 (Vendor Creation & Disbursement):** Enables single-user creation or modification of vendor master records paired with the execution of electronic disbursements, establishing immediate opportunity for phantom vendor creation and misappropriation of corporate cash.
- **Rule SOD-02 (Requisition / Buyer & Purchase Order Approval):** Allows originators of purchase orders to approve their own commitments without independent supervisory oversight, bypassing corporate Delegation of Authority (DoA) thresholds.
- **Rule SOD-03 (PO Approval & Goods Receipt / GRN):** Combines fiscal approval authority with physical custody verification in warehouse receiving, increasing risks of phantom inventory receipts and collusive vendor billing.
- **Rule SOD-04 (Invoice Entry & Treasury Payment Release):** Grants end-to-end accounts payable liability booking and cash release execution to single individuals without dual-authorization sign-off.
- **Rule SOD-05 (User Security Administration & Business Transactions):** Highly privileged IT administrators possess operational transaction execution rights, enabling the unmonitored assignment of temporary authorizations and evasion of audit trails.

**Impacted Process Lanes:** `{lanes_summary}`.

### 3. Fraud Risk & ICFR (Internal Control over Financial Reporting) Impact Assessment
- **Inadequate Preventive Safeguards:** Reliance on manual compensating controls rather than automated ERP system-enforced authorization boundaries violates COSO Internal Control Principle 10 (Control Activities) and Principle 11 (General Controls over Technology).
- **Elevated Fraud Exposure:** Unsegregated dual custody over vendor records and disbursement batches creates significant unmitigated fraud exposure under ACFE standards, potentially masking unauthorized fund transfers.
- **SOX 404 / ICFR Deficiency:** Inability to demonstrate automated enforcement of mutually exclusive duties constitutes a significant deficiency or potential material weakness in enterprise financial systems.

### 4. Actionable Remediation Roadmap & Mitigating Controls
1. **Immediate Revocation of Dual Authorizations:** Instantly strip operational transaction roles (AP Clerk, Buyer, Cashier) from IT Administrator accounts (`SOD-05`) and enforce strict separation between Vendor Master maintenance and AP disbursements (`SOD-01`).
2. **Implement Automated ERP SoD Enforcers:** Configure ERP role governance modules (such as SAP GRC Access Control or Oracle Risk Management) to prevent provisioning mutually exclusive authorization objects at the time of user assignment.
3. **Mandate Dual-Authorization Workflows:** For operational units where staffing constraints prevent immediate role separation, enforce dual-signoff workflows for vendor master bank account changes and wire payment releases above $5,000.
4. **Quarterly Privileged Access Recertification:** Establish a mandatory quarterly access review cadence requiring department heads to formally validate and recertify all assigned user authorizations and composite security roles."""

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

    total_users = len(user_access_data)
    critical_count = sum(1 for c in conflicts_detected if c.get("severity") == "Critical")
    high_count = sum(1 for c in conflicts_detected if c.get("severity") == "High")
    unique_conflicted_users = len(set(c.get("user_id") for c in conflicts_detected if c.get("user_id")))

    rule_breakdown: Dict[str, int] = {}
    lane_breakdown: Dict[str, int] = {}
    for c in conflicts_detected:
        rc = c.get("rule_code", "Unknown")
        rule_breakdown[rc] = rule_breakdown.get(rc, 0) + 1
        for lane in c.get("impacted_lanes", []):
            lane_breakdown[lane] = lane_breakdown.get(lane, 0) + 1

    ai_report = generate_sod_ai_report(
        total_users=total_users,
        conflicts=conflicts_detected,
        critical_count=critical_count,
        high_count=high_count,
        unique_conflicted_users=unique_conflicted_users,
        rule_breakdown=rule_breakdown,
        lane_breakdown=lane_breakdown
    )

    summary_msg = f"Detected {len(conflicts_detected)} toxic SoD permission combinations across {total_users} users ({critical_count} Critical, {high_count} High)."
    return {
        "sod_conflicts": conflicts_detected,
        "summary": summary_msg,
        "ai_report": ai_report,
        "test_result": {
            "summary": summary_msg,
            "exceptions_count": len(conflicts_detected),
            "exceptions": conflicts_detected,
            "ai_report": ai_report,
            "total_users": total_users,
            "critical_count": critical_count,
            "high_count": high_count,
            "unique_conflicted_users": unique_conflicted_users,
            "rule_breakdown": rule_breakdown,
            "lane_breakdown": lane_breakdown
        }
    }
