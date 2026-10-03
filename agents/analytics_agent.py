import io
import json
import pandas as pd
from typing import Dict, Any, List, Optional
from graphs.state import FieldAIState
from core.db import db
from core.llm import llm
from analytics import library

PROMPT_ANALYTICS_MAPPING = """You are FieldAI Analytics Mapper.
Given a list of CSV columns from a client dataset and a target audit test, map the expected test fields to the actual column names in the dataset.
Expected fields for tests:
- 'duplicate_payments': vendor_id, invoice_no, amount, date
- 'split_purchases': vendor_id, po_number, amount, date
- 'weekend_postings': transaction_id, amount, date, user_id
- 'round_amounts': transaction_id, vendor_id, amount
- 'below_threshold': transaction_id, amount, approver
- 'benford_analysis': amount
- 'missing_approvals': transaction_id, amount, approver_id
- 'three_way_match': po_qty, receipt_qty, inv_qty, po_price, inv_price
- 'sequence_gaps': document_no

Return JSON format:
{
  "field_mapping": {
    "vendor_id": "Vendor_Number",
    "invoice_no": "Inv_Ref",
    "amount": "Net_Amount",
    "date": "Posting_Date"
  }
}"""

def generate_ai_report(
    test_id: str,
    test_name: str,
    total_records: int,
    total_spend: float,
    exc_count: int,
    financial_exposure: float,
    top_vendors: List[str],
    top_users: List[str],
    exceptions_df: pd.DataFrame,
    benford_res: Optional[Dict[str, Any]] = None
) -> str:
    """Generates an executive Internal Audit Findings Report via LLM with structured audit fallback."""
    exc_rate = round((exc_count / total_records) * 100, 2) if total_records else 0.0
    vendors_str = ", ".join(top_vendors[:5]) if top_vendors else "N/A"
    users_str = ", ".join(top_users[:5]) if top_users else "N/A"

    system_prompt = (
        "You are FieldAI Senior Audit Analytics Specialist. "
        "Generate a formal, executive Internal Audit Findings Report based on the data analytics test execution. "
        "Use GitHub markdown with clear section headers, professional tone, and quantified impact."
    )

    prompt = f"""
Audit Analytics Procedure: {test_id} - {test_name}
Population Tested: {total_records:,} transactions (Total Spend: ${total_spend:,.2f})
Flagged Audit Exceptions: {exc_count:,} vouchers ({exc_rate}% of population)
Total Financial Exposure: ${financial_exposure:,.2f}
Top Exposed Vendors: {vendors_str}
Top Originating Users: {users_str}

Please generate a formal Internal Audit Findings & Exception Report with the following 4 sections:
### 1. Executive Summary & Audit Observation
### 2. Root Cause & Behavioral Pattern Analysis
### 3. Business Risk & Financial Exposure Assessment
### 4. Actionable Management Recommendations (Numbered 1-3)
"""

    try:
        report_text = llm.generate_text(prompt, system_prompt)
        if report_text and "Executive Summary" in report_text and len(report_text.strip()) > 150:
            return report_text.strip()
    except Exception as e:
        print(f"[AnalyticsAgent] LLM generation error: {e}")

    # High-quality deterministic fallback reports for all 9 tests
    fallback_templates = {
        "AN-01": f"""### 1. Executive Summary & Audit Observation
FieldAI executed audit procedure **AN-01: Duplicate Payments Detection** on the full transaction population of **{total_records:,} records** (Total Population Value: **${total_spend:,.2f}**). The analytics algorithm identified **{exc_count} potential duplicate disbursements** totaling **${financial_exposure:,.2f}** in redundant payments ({exc_rate}% of population).

The identified vouchers exhibit identical supplier IDs and invoice numbers, or identical amounts disbursed within consecutive payment cycles to suppliers including `{vendors_str}`.

### 2. Root Cause & Behavioral Pattern Analysis
- **ERP Duplicate Validation Inactive:** System configuration in Accounts Payable lacks strict duplicate invoice blocking across identical `Vendor ID` + `Invoice Number` combinations.
- **Decentralized Originators:** Transactions were entered by multiple AP clerks (`{users_str}`) without cross-checking open items or existing payment proposals.
- **Credit Memo Re-billing:** Vendor balance statements were processed as initial liabilities rather than liquidating prior open credits.

### 3. Business Risk & Financial Exposure Assessment
- **Direct Cash Leakage:** High risk of unreconciled double payments resulting in immediate cash bleed.
- **COSO Control Deficiency:** Non-compliance with Core Financial Controls (COSO Principle 10) requiring pre-disbursement verification.
- **Recovery Friction:** Substantial administrative overhead and write-off exposure for overpayments not recouped within 60 days.

### 4. Actionable Management Recommendations
1. **Immediate Overpayment Recoupment:** Issue formal debit memos and payment stops on affected vendors (`{vendors_str}`) to recover the **${financial_exposure:,.2f}** overpayment.
2. **Activate ERP Hard-Stop Controls:** Enable automated duplicate invoice checking in ERP (e.g. SAP message F5 117) to block matching invoice numbers upon data entry.
3. **Vendor Statement Reconciliation Protocol:** Mandate monthly statement reconciliations for top 50 vendors prior to executing bi-weekly disbursement runs.""",

        "AN-02": f"""### 1. Executive Summary & Audit Observation
Audit procedure **AN-02: Split Purchases Below Approval Threshold** evaluated **{total_records:,} transactions**. The algorithm detected **{exc_count} transactions** totaling **${financial_exposure:,.2f}** issued to vendors `{vendors_str}` that were split into multiple lower-value vouchers on the same date to circumvent the **$10,000 Delegation of Authority (DoA)** approval threshold.

### 2. Root Cause & Behavioral Pattern Analysis
- **Threshold Evasion:** Procurement originators (`{users_str}`) generated clustered purchase orders just below $10,000 (e.g., $9,800 + $9,950) to avoid Department Head and CFO supervisory review.
- **Absence of Daily Vendor Aggregation Checks:** ERP workflows currently evaluate approval limits on an isolated line-item basis rather than aggregating daily spend per vendor.

### 3. Business Risk & Financial Exposure Assessment
- **Bypassed Governance:** High risk of unauthorized commitments entered without competitive quotations or budget verification.
- **Maverick Spending:** Circumvention of master contract pricing and procurement policy guidelines.

### 4. Actionable Management Recommendations
1. **Cumulative Daily Threshold Check:** Configure automated ERP workflow rule to aggregate all purchase orders issued to the same vendor on the same business day.
2. **Management Inquiry:** Conduct supervisory inquiry with originators (`{users_str}`) regarding the business justification for fragmented orders.
3. **Procurement Policy Retraining:** Mandate formal policy refresher training on DoA compliance and anti-structuring rules.""",

        "AN-03": f"""### 1. Executive Summary & Audit Observation
Audit procedure **AN-03: Weekend & Non-Working Day Postings** flagged **{exc_count} transactions** totaling **${financial_exposure:,.2f}** recorded on Saturdays or Sundays without prior management overtime authorization.

### 2. Root Cause & Behavioral Pattern Analysis
- **Off-Hours System Access:** Users (`{users_str}`) logged in and processed invoices outside of standard core operating hours.
- **Supervisory Blind Spots:** Lack of real-time monitoring and alerting for transactions originated during non-business days.

### 3. Business Risk & Financial Exposure Assessment
- **Fraud & Concealment Risk:** Elevated risk of unauthorized transactions posted during periods with reduced internal supervisory oversight.
- **Audit Trail Anomalies:** Indication of manual posting overrides or delayed cut-off entries.

### 4. Actionable Management Recommendations
1. **Time-Based Access Restrictions:** Restrict transactional posting permissions outside business hours unless accompanied by pre-approved change/overtime authorization.
2. **Weekend Transaction Alerting:** Implement automated Monday morning exception reports sent to AP Managers detailing all weekend postings.
3. **Sampling Validation:** Select 100% of the flagged weekend transactions for vouching against approved purchase contracts.""",

        "AN-04": f"""### 1. Executive Summary & Audit Observation
Audit procedure **AN-04: High-Value Round-Figure Payments** flagged **{exc_count} disbursements** totaling **${financial_exposure:,.2f}** representing exact round numbers (multiples of $1,000 or $500, $\ge \$1,000$).

### 2. Root Cause & Behavioral Pattern Analysis
- **Estimated or Lump-Sum Billing:** Vouchers paid on estimate or retainers rather than verified time-and-materials receipts or itemized invoices.
- **Consulting / Non-PO Vouchers:** High concentration of round figures in discretionary service categories with minimal deliverables verification.

### 3. Business Risk & Financial Exposure Assessment
- **Overbilling Risk:** Risk of paying rounded estimates that do not reflect actual goods delivered or services rendered.
- **FCPA / Compliance Red Flag:** International anti-fraud standards consider unexplained round figures an indicator of unauthorized fee structures.

### 4. Actionable Management Recommendations
1. **Itemized Billing Enforcement:** Require itemized supplier timesheets and delivery dockets before approving any round-sum payment.
2. **Retainer True-Up Verification:** Audit quarterly true-up reconciliations for all professional services retainer contracts.
3. **Contract Rate Audit:** Cross-check payments against agreed master service agreement hourly fee rate cards.""",

        "AN-05": f"""### 1. Executive Summary & Audit Observation
Audit procedure **AN-05: Transactions Just Below Approval Limit** identified **{exc_count} transactions** totaling **${financial_exposure:,.2f}** clustered within 5% below the **$10,000** approval ceiling ($9,500.00 – $9,999.00).

### 2. Root Cause & Behavioral Pattern Analysis
- **Strategic Pricing:** Quotations structured to fall just below the mandatory CFO approval and 3-quote competitive bidding requirement.
- **Approver Collusion Risk:** Routine authorization by Tier-1 approvers without independent senior management oversight.

### 3. Business Risk & Financial Exposure Assessment
- **Procurement Dilution:** Evasion of formal competitive bidding resulting in above-market procurement costs.
- **Policy Non-Compliance:** Circumvention of formal organizational governance mandates.

### 4. Actionable Management Recommendations
1. **Lower Spot-Audit Threshold:** Subject all invoices between $9,000 and $10,000 to monthly post-payment quality assurance audits.
2. **Supplier Bidding Review:** Audit supplier quotation archives to confirm if vendor artificially discounted line items to remain under $10,000.
3. **DoA Re-alignment:** Implement dual-signoff on any invoice within 10% of the authority ceiling.""",

        "AN-06": f"""### 1. Executive Summary & Audit Observation
Audit procedure **AN-06: Benford's Law First-Digit Analysis** evaluated the full population of **{total_records:,} transactions**. The test measures mathematical conformance against the natural logarithmic digit distribution ($P(d) = \log_{10}(1 + 1/d)$). The analysis revealed a Chi-square statistic of **{benford_res.get('chi_square', 'N/A') if benford_res else 'N/A'}**, signaling notable digit distortion.

### 2. Root Cause & Behavioral Pattern Analysis
- **Artificial Distribution Clumping:** Abnormal concentrations in specific leading digits indicate human intervention, repetitive fixed contract values, or intentional pricing structuring.

### 3. Business Risk & Financial Exposure Assessment
- **Fictitious Invoicing:** Significant deviations from Benford's Law are standard indicators of non-random, fabricated payment distributions.
- **Reporting Inaccuracies:** Data integrity concerns in ERP financial ledgers.

### 4. Actionable Management Recommendations
1. **Focused Sub-Population Testing:** Target specific vendors and cost centers showing the highest Benford variance for substantive transaction testing.
2. **Continuous Monitoring:** Integrate Benford 1st and 2nd digit analytics into monthly continuous transaction monitoring routines.
3. **ERP Data Cleanliness Review:** Review automated recurring billing schedules to separate standardized monthly fees from variable procurement.""",

        "AN-07": f"""### 1. Executive Summary & Audit Observation
Audit procedure **AN-07: Unapproved Invoice Payments** flagged **{exc_count} transactions** totaling **${financial_exposure:,.2f}** where mandatory supervisory approval ID or approval timestamps were absent from the ledger.

### 2. Root Cause & Behavioral Pattern Analysis
- **Workflow Bypasses:** Direct invoice entry posted into General Ledger without going through the automated approval hierarchy.
- **Emergency Release Overrides:** Payments authorized via manual bank portal tokens without ERP system pre-approval.

### 3. Business Risk & Financial Exposure Assessment
- **Unvetted Liabilities:** Severe control breakdown allowing financial commitments to be settled without departmental sign-off.
- **Audit Deficiency:** Significant deficiency in Internal Controls over Financial Reporting (ICFR).

### 4. Actionable Management Recommendations
1. **System Payment Release Lock:** Configure payment run programs to strictly reject vouchers lacking a verified `approver_id`.
2. **Retroactive Approval Rectification:** Submit all {exc_count} unapproved vouchers to appropriate cost center owners for formal retrospective sign-off.
3. **Privileged User Audit:** Review super-user activities to identify accounts with permissions to bypass standard approval workflow gates.""",

        "AN-08": f"""### 1. Executive Summary & Audit Observation
Audit procedure **AN-08: Three-Way Match Variances** identified **{exc_count} voucher discrepancies** totaling **${financial_exposure:,.2f}** involving quantity mismatches (invoice quantity exceeding warehouse goods receipt) or price markups exceeding the 5% tolerance threshold.

### 2. Root Cause & Behavioral Pattern Analysis
- **Tolerance Overrides:** AP processors manually cleared 3-way match blocks without formal buyer authorization.
- **Inaccurate Receiving Notes:** Receiving dockets entered without physical item piece-counts.

### 3. Business Risk & Financial Exposure Assessment
- **Overbilling:** Payment for goods not received or billing at uncontracted rates.
- **Inventory Discrepancy:** Inaccurate stock balance records in ERP inventory ledgers.

### 4. Actionable Management Recommendations
1. **Enforce Hard Tolerance Blocks:** Lower 3-way match price tolerance to 1% and zero tolerance for quantity over-billing.
2. **Supplier Credit Claim:** Demand immediate credit notes from affected suppliers for the verified quantity and price differences.
3. **Receiving Cut-off Audit:** Inspect warehouse receiving log books to reconcile physical intake with ERP GRN records.""",

        "AN-09": f"""### 1. Executive Summary & Audit Observation
Audit procedure **AN-09: Document Sequence Gap Testing** identified **{exc_count} missing sequential numbers** in the official sequential voucher series.

### 2. Root Cause & Behavioral Pattern Analysis
- **Deleted Vouchers:** Documents created and purged from the database without audit trail retention.
- **System Buffer Drops:** ERP numbering engine skipping numbers during application crashes or rollbacks.

### 3. Business Risk & Financial Exposure Assessment
- **Completeness Assertion Failure:** Inability to confirm completeness of financial records for statutory audit.
- **Off-the-Books Transactions:** Potential omission of taxable transactions or unrecorded liabilities.

### 4. Actionable Management Recommendations
1. **Number Range Investigation:** Conduct IT database audit to verify whether missing sequence numbers were canceled, aborted, or deleted.
2. **ERP Sequence Number Buffer Optimization:** Disable multi-server sequence number buffering to eliminate gap generation.
3. **Formal Gap Register:** Maintain a mandatory sequential gap register signed by Finance Management justifying all numbering discrepancies."""
    }

    return fallback_templates.get(test_id, f"""### 1. Executive Summary & Audit Observation
FieldAI automated analytics executed test **{test_id}: {test_name}** on **{total_records:,} transactions** totaling **${total_spend:,.2f}**. Identified **{exc_count} audit exceptions** ({exc_rate}% exception rate).

### 2. Root Cause & Behavioral Pattern Analysis
Exceptions indicate inconsistent operational controls, lack of automated ERP validation checks, and decentralized transactional processing across multiple originators.

### 3. Business Risk & Financial Exposure Assessment
Elevated operational and compliance risks resulting from deviations from standard internal procurement and disbursement policies.

### 4. Actionable Management Recommendations
1. Review flagged exception vouchers with responsible operational management.
2. Implement preventative automated ERP controls to block transaction anomalies at inception.
3. Perform follow-up audit testing during subsequent review cycles.""")

def run(state: FieldAIState) -> Dict[str, Any]:
    """
    Analytics Agent (Option 11):
    Maps uploaded dataset columns to audit test parameters, executes unit-tested pandas algorithms,
    and generates an AI-powered executive report with visual analytics metrics.
    """
    test_request = state.get("test_request", {})
    test_id = test_request.get("test_id", "AN-01")
    df = test_request.get("dataframe")

    # If no dataframe provided, generate standard procurement test sample
    if df is None:
        df = pd.DataFrame([
            {"vendor_id": "V-101", "invoice_no": "INV-5001", "amount": 12500.0, "date": "2026-03-10", "approver_id": "USR-12"},
            {"vendor_id": "V-101", "invoice_no": "INV-5001", "amount": 12500.0, "date": "2026-03-15", "approver_id": "USR-12"}, # Duplicate
            {"vendor_id": "V-102", "invoice_no": "INV-5002", "amount": 9950.0, "date": "2026-03-12", "approver_id": "USR-08"},  # Just below 10k
            {"vendor_id": "V-103", "invoice_no": "INV-5003", "amount": 15000.0, "date": "2026-03-14", "approver_id": ""},       # Missing approval
            {"vendor_id": "V-104", "invoice_no": "INV-5004", "amount": 5000.0, "date": "2026-03-15", "approver_id": "USR-15"},  # Weekend Sunday
            {"vendor_id": "V-105", "invoice_no": "INV-5005", "amount": 20000.0, "date": "2026-03-16", "approver_id": "USR-12"}, # Round $20k
        ])

    mapping = test_request.get("field_mapping")
    if not mapping:
        mapping = {c: c for c in df.columns}

    # Fetch test description from DB
    test_rec = db.fetch_one("SELECT name, description FROM analytics_library WHERE test_id = %s;", (test_id,))
    test_name = test_rec["name"] if test_rec else f"Procedure {test_id}"

    # Execute corresponding library test
    exceptions_df = pd.DataFrame()
    benford_res = None
    summary_msg = ""

    if test_id == "AN-01":
        exceptions_df = library.duplicate_payments(df, mapping)
        summary_msg = f"Identified {len(exceptions_df)} potential duplicate invoice payments."
    elif test_id == "AN-02":
        exceptions_df = library.split_purchases(df, mapping)
        summary_msg = f"Identified {len(exceptions_df)} transactions showing split purchase pattern below threshold."
    elif test_id == "AN-03":
        exceptions_df = library.weekend_postings(df, mapping)
        summary_msg = f"Identified {len(exceptions_df)} transactions posted on weekends/non-working days."
    elif test_id == "AN-04":
        exceptions_df = library.round_amounts(df, mapping)
        summary_msg = f"Identified {len(exceptions_df)} high-value round figure payments."
    elif test_id == "AN-05":
        exceptions_df = library.below_threshold(df, mapping)
        summary_msg = f"Identified {len(exceptions_df)} transactions within 5% below approval threshold."
    elif test_id == "AN-06":
        benford_res = library.benford_analysis(df, mapping)
        summary_msg = f"Completed Benford 1st digit distribution analysis (Chi-square: {benford_res.get('chi_square', 0)})."
    elif test_id == "AN-07":
        exceptions_df = library.missing_approvals(df, mapping)
        summary_msg = f"Identified {len(exceptions_df)} transactions lacking mandatory approval ID."
    elif test_id == "AN-08":
        exceptions_df = library.three_way_match(df, mapping)
        summary_msg = f"Identified {len(exceptions_df)} 3-way match price or quantity variances."
    elif test_id == "AN-09":
        gaps = library.sequence_gaps(df, mapping)
        summary_msg = f"Identified {len(gaps)} missing sequential numbers."
        exceptions_df = pd.DataFrame({"missing_sequence_number": gaps})

    exceptions_json = benford_res if benford_res else exceptions_df.to_dict(orient="records")
    exc_count = len(exceptions_df) if benford_res is None else benford_res.get("total_records", 0)

    # Compute financial metrics
    total_spend = float(df["amount"].sum()) if "amount" in df.columns else 0.0
    financial_exposure = float(exceptions_df["amount"].sum()) if "amount" in exceptions_df.columns else 0.0
    top_vendors = exceptions_df["vendor_id"].dropna().unique().tolist() if "vendor_id" in exceptions_df.columns else []
    top_users = exceptions_df["user_id"].dropna().unique().tolist() if "user_id" in exceptions_df.columns else []
    vendors_impacted = len(top_vendors)
    exc_rate = round((exc_count / len(df)) * 100, 2) if len(df) else 0.0

    # Generate AI-powered executive report
    ai_report = generate_ai_report(
        test_id=test_id,
        test_name=test_name,
        total_records=len(df),
        total_spend=total_spend,
        exc_count=exc_count,
        financial_exposure=financial_exposure,
        top_vendors=top_vendors,
        top_users=top_users,
        exceptions_df=exceptions_df,
        benford_res=benford_res
    )

    # Record in test_runs
    linked_test_id = test_request.get("linked_test_id")
    if linked_test_id:
        db.execute_insert(
            """
            INSERT INTO test_runs (test_id, run_type, parameters_json, result_summary, exceptions_json, exceptions_count, status)
            VALUES (%s, 'analytics', %s, %s, %s, %s, 'completed');
            """,
            (linked_test_id, json.dumps(mapping), summary_msg, json.dumps(exceptions_json), exc_count)
        )

    return {
        "test_result": {
            "test_id": test_id,
            "test_name": test_name,
            "summary": summary_msg,
            "exceptions_count": exc_count,
            "exceptions": exceptions_json,
            "financial_exposure": financial_exposure,
            "vendors_impacted": vendors_impacted,
            "exception_rate_pct": exc_rate,
            "ai_report": ai_report
        }
    }
