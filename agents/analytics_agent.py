import io
import json
import pandas as pd
from typing import Dict, Any, List
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

def run(state: FieldAIState) -> Dict[str, Any]:
    """
    Analytics Agent (Option 11):
    Maps uploaded dataset columns to audit test parameters and executes unit-tested pandas algorithms.
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
    exc_count = len(exceptions_df) if benford_res is None else 0

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
            "summary": summary_msg,
            "exceptions_count": exc_count,
            "exceptions": exceptions_json
        }
    }
