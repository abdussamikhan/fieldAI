import pandas as pd
import pytest
from analytics import library

@pytest.fixture
def sample_invoices_df():
    return pd.DataFrame([
        {"vendor_id": "V-1", "invoice_no": "INV-100", "amount": 1000.0, "date": "2026-03-01", "approver_id": "USR-1", "document_no": 101},
        {"vendor_id": "V-1", "invoice_no": "INV-100", "amount": 1000.0, "date": "2026-03-05", "approver_id": "USR-1", "document_no": 102}, # Dup
        {"vendor_id": "V-2", "invoice_no": "INV-101", "amount": 9600.0, "date": "2026-03-08", "approver_id": "USR-2", "document_no": 103}, # Just below 10k
        {"vendor_id": "V-3", "invoice_no": "INV-102", "amount": 5000.0, "date": "2026-03-15", "approver_id": "", "document_no": 105},      # Weekend (Sun) & Missing approver
        {"vendor_id": "V-4", "invoice_no": "INV-103", "amount": 20000.0, "date": "2026-03-10", "approver_id": "USR-3", "document_no": 106}  # Round 20k
    ])

def test_duplicate_payments(sample_invoices_df):
    dups = library.duplicate_payments(sample_invoices_df, {"vendor_id": "vendor_id", "invoice_no": "invoice_no", "amount": "amount"})
    assert len(dups) == 2
    assert "INV-100" in dups["invoice_no"].values

def test_below_threshold(sample_invoices_df):
    below = library.below_threshold(sample_invoices_df, {"amount": "amount"}, threshold=10000.0, margin_pct=0.05)
    assert len(below) == 1
    assert below.iloc[0]["amount"] == 9600.0

def test_round_amounts(sample_invoices_df):
    rounds = library.round_amounts(sample_invoices_df, {"amount": "amount"}, min_amount=1000.0)
    assert len(rounds) >= 3

def test_weekend_postings(sample_invoices_df):
    weekends = library.weekend_postings(sample_invoices_df, {"date": "date"})
    assert len(weekends) == 3

def test_missing_approvals(sample_invoices_df):
    missing = library.missing_approvals(sample_invoices_df, {"approver_id": "approver_id"})
    assert len(missing) == 1
    assert missing.iloc[0]["invoice_no"] == "INV-102"

def test_sequence_gaps(sample_invoices_df):
    gaps = library.sequence_gaps(sample_invoices_df, {"document_no": "document_no"})
    assert 104 in gaps

def test_benford_analysis(sample_invoices_df):
    res = library.benford_analysis(sample_invoices_df, {"amount": "amount"})
    assert "chi_square" in res
    assert res["total_records"] == 5

def test_three_way_match():
    match_df = pd.DataFrame([
        {"po_qty": 10, "receipt_qty": 10, "inv_qty": 10, "po_price": 100.0, "inv_price": 100.0}, # Matched
        {"po_qty": 10, "receipt_qty": 8, "inv_qty": 10, "po_price": 100.0, "inv_price": 100.0},  # Inv > Receipt
        {"po_qty": 10, "receipt_qty": 10, "inv_qty": 10, "po_price": 100.0, "inv_price": 120.0}  # Price variance
    ])
    discrepancies = library.three_way_match(match_df, {
        "po_qty": "po_qty", "receipt_qty": "receipt_qty", "inv_qty": "inv_qty",
        "po_price": "po_price", "inv_price": "inv_price"
    })
    assert len(discrepancies) == 2
