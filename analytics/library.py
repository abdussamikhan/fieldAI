import math
from typing import Dict, Any, List, Tuple
import pandas as pd
import numpy as np

def duplicate_payments(df: pd.DataFrame, mapping: Dict[str, str]) -> pd.DataFrame:
    """
    AN-01: Detects duplicate disbursements with identical vendor and amount,
    or duplicate invoice numbers.
    """
    vendor_col = mapping.get("vendor_id", "vendor_id")
    inv_col = mapping.get("invoice_no", "invoice_no")
    amt_col = mapping.get("amount", "amount")
    
    req_cols = [c for c in [vendor_col, amt_col] if c in df.columns]
    if len(req_cols) < 2:
        return pd.DataFrame()

    # Duplicates on vendor + invoice_no OR vendor + amount
    dup_mask = df.duplicated(subset=[vendor_col, amt_col], keep=False)
    if inv_col in df.columns:
        dup_inv_mask = df.duplicated(subset=[vendor_col, inv_col], keep=False)
        dup_mask = dup_mask | dup_inv_mask
        
    return df[dup_mask].copy()

def split_purchases(
    df: pd.DataFrame,
    mapping: Dict[str, str],
    threshold: float = 10000.0
) -> pd.DataFrame:
    """
    AN-02: Identifies multiple POs issued to the same vendor on the same day
    individually below approval threshold but totaling >= threshold.
    """
    vendor_col = mapping.get("vendor_id", "vendor_id")
    date_col = mapping.get("date", "date")
    amt_col = mapping.get("amount", "amount")

    if not all(c in df.columns for c in [vendor_col, date_col, amt_col]):
        return pd.DataFrame()

    df_copy = df.copy()
    df_copy["_date_parsed"] = pd.to_datetime(df_copy[date_col], errors="coerce").dt.date
    # Filter items individually below threshold
    below_thresh = df_copy[df_copy[amt_col] < threshold]
    
    # Group by vendor and parsed date
    grouped = below_thresh.groupby([vendor_col, "_date_parsed"])
    split_indices = []
    
    for (vendor, d), group in grouped:
        if len(group) > 1 and group[amt_col].sum() >= threshold:
            split_indices.extend(group.index.tolist())
            
    return df.loc[split_indices].copy()

def weekend_postings(df: pd.DataFrame, mapping: Dict[str, str]) -> pd.DataFrame:
    """
    AN-03: Flags transactions posted on weekends (Saturday / Sunday).
    """
    date_col = mapping.get("date", "date")
    if date_col not in df.columns:
        return pd.DataFrame()

    df_copy = df.copy()
    parsed_dates = pd.to_datetime(df_copy[date_col], errors="coerce")
    weekend_mask = parsed_dates.dt.dayofweek >= 5
    return df[weekend_mask].copy()

def round_amounts(
    df: pd.DataFrame,
    mapping: Dict[str, str],
    min_amount: float = 1000.0
) -> pd.DataFrame:
    """
    AN-04: Highlights round-number amounts (multiples of $1,000 or $500).
    """
    amt_col = mapping.get("amount", "amount")
    if amt_col not in df.columns:
        return pd.DataFrame()

    amounts = pd.to_numeric(df[amt_col], errors="coerce")
    round_mask = (amounts >= min_amount) & ((amounts % 1000 == 0) | (amounts % 500 == 0))
    return df[round_mask].copy()

def below_threshold(
    df: pd.DataFrame,
    mapping: Dict[str, str],
    threshold: float = 10000.0,
    margin_pct: float = 0.05
) -> pd.DataFrame:
    """
    AN-05: Finds transactions within margin_pct (default 5%) below threshold.
    """
    amt_col = mapping.get("amount", "amount")
    if amt_col not in df.columns:
        return pd.DataFrame()

    amounts = pd.to_numeric(df[amt_col], errors="coerce")
    lower_bound = threshold * (1.0 - margin_pct)
    mask = (amounts >= lower_bound) & (amounts < threshold)
    return df[mask].copy()

def benford_analysis(df: pd.DataFrame, mapping: Dict[str, str]) -> Dict[str, Any]:
    """
    AN-06: Benford's Law First-Digit Analysis.
    Expected P(d) = log10(1 + 1/d) for d in 1..9.
    """
    amt_col = mapping.get("amount", "amount")
    if amt_col not in df.columns:
        return {"error": f"Column {amt_col} not found"}

    amounts = pd.to_numeric(df[amt_col], errors="coerce").dropna()
    amounts = amounts[amounts > 0]
    
    first_digits = [int(str(a).lstrip("0.")[0]) for a in amounts if str(a).lstrip("0.")]
    first_digits = [d for d in first_digits if 1 <= d <= 9]
    
    total = len(first_digits)
    if total == 0:
        return {"total_records": 0, "digits": {}}

    digits_count = pd.Series(first_digits).value_counts().to_dict()
    analysis = {}
    chi_square = 0.0

    for d in range(1, 10):
        actual_cnt = digits_count.get(d, 0)
        actual_pct = (actual_cnt / total) * 100
        expected_pct = math.log10(1 + 1 / d) * 100
        expected_cnt = (expected_pct / 100) * total
        diff = actual_pct - expected_pct
        chi_square += ((actual_cnt - expected_cnt) ** 2) / (expected_cnt or 1)
        
        analysis[str(d)] = {
            "actual_count": actual_cnt,
            "actual_pct": round(actual_pct, 2),
            "expected_pct": round(expected_pct, 2),
            "variance": round(diff, 2)
        }

    return {
        "total_records": total,
        "chi_square": round(chi_square, 2),
        "digits": analysis
    }

def missing_approvals(df: pd.DataFrame, mapping: Dict[str, str]) -> pd.DataFrame:
    """
    AN-07: Identifies transactions where approver or approval timestamp is missing.
    """
    approver_col = mapping.get("approver_id", "approver_id")
    if approver_col not in df.columns:
        return pd.DataFrame()

    mask = df[approver_col].isna() | (df[approver_col].astype(str).str.strip() == "")
    return df[mask].copy()

def three_way_match(
    df: pd.DataFrame,
    mapping: Dict[str, str],
    tolerance_pct: float = 0.05
) -> pd.DataFrame:
    """
    AN-08: Three-Way Match Discrepancies between PO, Receipt, and Invoice.
    """
    po_qty = mapping.get("po_qty", "po_qty")
    rec_qty = mapping.get("receipt_qty", "receipt_qty")
    inv_qty = mapping.get("inv_qty", "inv_qty")
    po_price = mapping.get("po_price", "po_price")
    inv_price = mapping.get("inv_price", "inv_price")

    if not all(c in df.columns for c in [po_qty, rec_qty, inv_qty, po_price, inv_price]):
        return pd.DataFrame()

    qty_diff = (df[inv_qty] > df[rec_qty]) | (df[inv_qty] > df[po_qty])
    price_variance = (df[inv_price] - df[po_price]).abs() / df[po_price].replace(0, np.nan)
    price_diff = price_variance > tolerance_pct

    return df[qty_diff | price_diff].copy()

def sequence_gaps(df: pd.DataFrame, mapping: Dict[str, str]) -> List[int]:
    """
    AN-09: Sequence gap testing in sequentially numbered documents.
    """
    doc_col = mapping.get("document_no", "document_no")
    if doc_col not in df.columns:
        return []

    nums = pd.to_numeric(df[doc_col], errors="coerce").dropna().astype(int).sort_values().unique()
    if len(nums) < 2:
        return []

    full_range = set(range(nums[0], nums[-1] + 1))
    present = set(nums)
    gaps = sorted(list(full_range - present))
    return gaps[:100] # Return up to 100 missing sequence numbers
