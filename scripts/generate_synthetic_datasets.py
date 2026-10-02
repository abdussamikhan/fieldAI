import os
import sys
import math
import random
import datetime
import pandas as pd
from pathlib import Path

# Add root directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.storage import save_file
from core.db import db

def generate_benford_amount(min_val=100.0, max_val=95000.0) -> float:
    """Generates an amount loosely conforming to Benford's Law distribution."""
    # First digit chosen with P(d) = log10(1 + 1/d)
    digits = list(range(1, 10))
    weights = [math.log10(1 + 1 / d) for d in digits]
    first_digit = random.choices(digits, weights=weights, k=1)[0]
    
    # Choose magnitude
    magnitudes = [100, 1000, 10000]
    mag = random.choice(magnitudes)
    
    # Generate random remainder
    val = first_digit * mag + random.uniform(0, mag - 1)
    val = max(min_val, min(max_val, val))
    return round(val, 2)

def generate_analytics_invoices_1000() -> pd.DataFrame:
    """
    Generates EXACTLY 1,000 procurement invoice transactions with embedded
    audit anomalies designed for analytics/library.py:
      - AN-01: Duplicate payments (identical vendor + invoice_no or vendor + amount)
      - AN-02: Split purchases (< $10k on same day to same vendor, totaling >= $10k)
      - AN-03: Weekend postings (Saturdays & Sundays)
      - AN-04: High-value round figures (multiples of $500 / $1,000)
      - AN-05: Transactions just below $10,000 threshold ($9,500 - $9,999)
      - AN-06: Natural Benford 1st-digit distribution for background transactions
      - AN-07: Missing approval IDs (unauthorized invoices)
      - AN-08: Three-way match variances (quantity mismatch or price variance > 5%)
      - AN-09: Sequence gap testing (document_no gaps)
    """
    random.seed(42)
    records = []
    
    vendors = [f"V-{100 + i}" for i in range(1, 61)]
    users = [f"USR-{i:02d}" for i in range(1, 21)]
    approvers = [f"APPR-{i:02d}" for i in range(1, 9)]
    
    start_date = datetime.date(2025, 1, 1)
    end_date = datetime.date(2026, 3, 25)
    date_range_days = (end_date - start_date).days

    # 1. AN-01 Duplicate Payments (8 duplicate pairs = 16 rows)
    for i in range(1, 9):
        v = f"V-{110 + i}"
        inv = f"INV-DUP-{8800 + i}"
        amt = round(random.choice([12450.0, 18500.0, 32100.0, 7840.50, 44200.0, 15600.0, 9200.0, 26800.0]), 2)
        d1 = start_date + datetime.timedelta(days=random.randint(10, 100))
        d2 = d1 + datetime.timedelta(days=random.randint(3, 14)) # Paid a week later
        usr = random.choice(users)
        appr = random.choice(approvers)
        
        # Row 1
        records.append({
            "vendor_id": v, "invoice_no": inv, "amount": amt, "date": str(d1),
            "user_id": usr, "approver_id": appr, "po_number": f"PO-{40000 + len(records)}",
            "po_qty": 100, "receipt_qty": 100, "inv_qty": 100, "po_price": round(amt/100, 2), "inv_price": round(amt/100, 2)
        })
        # Row 2 (Duplicate)
        records.append({
            "vendor_id": v, "invoice_no": inv, "amount": amt, "date": str(d2),
            "user_id": usr, "approver_id": appr, "po_number": f"PO-{40000 + len(records)}",
            "po_qty": 100, "receipt_qty": 100, "inv_qty": 100, "po_price": round(amt/100, 2), "inv_price": round(amt/100, 2)
        })

    # 2. AN-02 Split Purchases (6 clusters of 2-3 invoices on same date to same vendor, each < 10k, total >= 10k = 15 rows)
    split_configs = [
        ("V-102", "2026-02-10", [9800.00, 9950.00]),
        ("V-105", "2026-01-18", [4850.00, 4920.00, 5100.00]),
        ("V-112", "2026-02-24", [8500.00, 9200.00]),
        ("V-120", "2026-03-05", [6400.00, 7200.00]),
        ("V-125", "2025-11-12", [9100.00, 9600.00]),
        ("V-130", "2025-12-04", [4900.00, 4950.00, 4980.00])
    ]
    for s_idx, (v, s_date, s_amts) in enumerate(split_configs):
        for sub_i, amt in enumerate(s_amts):
            records.append({
                "vendor_id": v,
                "invoice_no": f"INV-SPLIT-{s_idx+1}{sub_i+1}",
                "amount": amt,
                "date": s_date,
                "user_id": random.choice(users),
                "approver_id": random.choice(approvers),
                "po_number": f"PO-{40000 + len(records)}",
                "po_qty": 50, "receipt_qty": 50, "inv_qty": 50, "po_price": round(amt/50, 2), "inv_price": round(amt/50, 2)
            })

    # 3. AN-03 Weekend Postings (40 transactions deliberately dated on Saturdays or Sundays)
    weekend_dates = []
    curr = start_date
    while curr <= end_date:
        if curr.weekday() in (5, 6): # 5=Sat, 6=Sun
            weekend_dates.append(curr)
        curr += datetime.timedelta(days=1)
    
    chosen_weekends = random.sample(weekend_dates, 40)
    for w_date in chosen_weekends:
        amt = generate_benford_amount(min_val=500.0, max_val=45000.0)
        records.append({
            "vendor_id": random.choice(vendors),
            "invoice_no": f"INV-WKD-{len(records)+1}",
            "amount": amt,
            "date": str(w_date),
            "user_id": random.choice(users),
            "approver_id": random.choice(approvers),
            "po_number": f"PO-{40000 + len(records)}",
            "po_qty": 40, "receipt_qty": 40, "inv_qty": 40, "po_price": round(amt/40, 2), "inv_price": round(amt/40, 2)
        })

    # 4. AN-04 Round Figure Amounts (multiples of $1,000 or $500, min $1,000 = 30 rows)
    round_amounts_list = [
        1000.0, 2500.0, 5000.0, 7500.0, 10000.0, 12000.0, 15000.0, 20000.0, 
        25000.0, 30000.0, 35000.0, 40000.0, 50000.0, 60000.0, 75000.0, 100000.0
    ]
    for _ in range(30):
        # Choose a weekday
        d = start_date + datetime.timedelta(days=random.randint(0, date_range_days))
        while d.weekday() in (5, 6):
            d += datetime.timedelta(days=1)
        amt = float(random.choice(round_amounts_list))
        records.append({
            "vendor_id": random.choice(vendors),
            "invoice_no": f"INV-RND-{len(records)+1}",
            "amount": amt,
            "date": str(d),
            "user_id": random.choice(users),
            "approver_id": random.choice(approvers),
            "po_number": f"PO-{40000 + len(records)}",
            "po_qty": 20, "receipt_qty": 20, "inv_qty": 20, "po_price": round(amt/20, 2), "inv_price": round(amt/20, 2)
        })

    # 5. AN-05 Transactions just below threshold ($9,500.00 to $9,999.00 = 25 rows)
    for _ in range(25):
        d = start_date + datetime.timedelta(days=random.randint(0, date_range_days))
        while d.weekday() in (5, 6):
            d += datetime.timedelta(days=1)
        amt = round(random.uniform(9501.0, 9995.0), 2)
        records.append({
            "vendor_id": random.choice(vendors),
            "invoice_no": f"INV-THR-{len(records)+1}",
            "amount": amt,
            "date": str(d),
            "user_id": random.choice(users),
            "approver_id": random.choice(approvers),
            "po_number": f"PO-{40000 + len(records)}",
            "po_qty": 25, "receipt_qty": 25, "inv_qty": 25, "po_price": round(amt/25, 2), "inv_price": round(amt/25, 2)
        })

    # 6. AN-07 Missing Approvals (25 rows where approver_id is blank / empty)
    for _ in range(25):
        d = start_date + datetime.timedelta(days=random.randint(0, date_range_days))
        while d.weekday() in (5, 6):
            d += datetime.timedelta(days=1)
        amt = generate_benford_amount(min_val=1200.0, max_val=48000.0)
        records.append({
            "vendor_id": random.choice(vendors),
            "invoice_no": f"INV-UNAPPR-{len(records)+1}",
            "amount": amt,
            "date": str(d),
            "user_id": random.choice(users),
            "approver_id": "", # Missing approval!
            "po_number": f"PO-{40000 + len(records)}",
            "po_qty": 30, "receipt_qty": 30, "inv_qty": 30, "po_price": round(amt/30, 2), "inv_price": round(amt/30, 2)
        })

    # 7. AN-08 Three-Way Match Variances (20 rows: quantity overbilled or unit price markup > 5%)
    for i in range(20):
        d = start_date + datetime.timedelta(days=random.randint(0, date_range_days))
        while d.weekday() in (5, 6):
            d += datetime.timedelta(days=1)
        po_price = round(random.uniform(50.0, 400.0), 2)
        po_qty = random.randint(50, 200)
        receipt_qty = po_qty
        
        if i % 2 == 0:
            # Quantity discrepancy: billed for more than received
            inv_qty = receipt_qty + random.randint(10, 30)
            inv_price = po_price
        else:
            # Price discrepancy: billed at 12-25% markup
            inv_qty = receipt_qty
            inv_price = round(po_price * random.uniform(1.12, 1.25), 2)

        amt = round(inv_qty * inv_price, 2)
        records.append({
            "vendor_id": random.choice(vendors),
            "invoice_no": f"INV-3WM-{len(records)+1}",
            "amount": amt,
            "date": str(d),
            "user_id": random.choice(users),
            "approver_id": random.choice(approvers),
            "po_number": f"PO-{40000 + len(records)}",
            "po_qty": po_qty,
            "receipt_qty": receipt_qty,
            "inv_qty": inv_qty,
            "po_price": po_price,
            "inv_price": inv_price
        })

    # 8. Remaining records to make EXACTLY 1,000 records
    remaining_count = 1000 - len(records)
    print(f"Generating {remaining_count} compliant standard background records following Benford's Law...")

    for i in range(remaining_count):
        d = start_date + datetime.timedelta(days=random.randint(0, date_range_days))
        while d.weekday() in (5, 6):
            d += datetime.timedelta(days=1)
            
        amt = generate_benford_amount(min_val=150.0, max_val=85000.0)
        # Avoid exact round or below-threshold on benign records
        if amt % 500 == 0:
            amt += round(random.uniform(12.50, 48.75), 2)
        if 9500.0 <= amt <= 10000.0:
            amt = 10450.25

        qty = random.randint(10, 150)
        unit_p = round(amt / qty, 2)
        # Re-sync amt to unit_p * qty
        amt = round(unit_p * qty, 2)

        records.append({
            "vendor_id": random.choice(vendors),
            "invoice_no": f"INV-{10000 + len(records) + 1}",
            "amount": amt,
            "date": str(d),
            "user_id": random.choice(users),
            "approver_id": random.choice(approvers),
            "po_number": f"PO-{40000 + len(records)}",
            "po_qty": qty,
            "receipt_qty": qty,
            "inv_qty": qty,
            "po_price": unit_p,
            "inv_price": unit_p
        })

    # Shuffle to distribute anomalies naturally across the dataset
    random.shuffle(records)

    # Assign sequential document_no with 10 intentional gaps for AN-09
    doc_seq = 50001
    gap_targets = set(random.sample(range(50050, 50950), 10))
    for r in records:
        while doc_seq in gap_targets:
            doc_seq += 1
        r["document_no"] = doc_seq
        doc_seq += 1

    df = pd.DataFrame(records)
    assert len(df) == 1000, f"Expected exactly 1000 records, got {len(df)}"
    return df

def generate_sod_matrix_large() -> pd.DataFrame:
    """
    Generates an enterprise-scale User Access Matrix (160 user-role assignments
    across 80 users) with intentional toxic SoD combinations:
      - SOD-01: Vendor Master Admin + Payment Release/Disbursement
      - SOD-02: Purchase Requisitioner/Buyer + Purchase Order Approver
      - SOD-04: Invoice Processing Clerk + Electronic Payment Release
      - SOD-05: System Security Admin + Financial Accounting/AP
    """
    random.seed(101)
    
    first_names = [
        "Ahmed", "Elena", "Michael", "Fatima", "Tariq", "Sarah", "David", "Chloe", 
        "Hiroshi", "Amira", "Carlos", "Svetlana", "John", "Kavita", "Zaid", "Aisha", 
        "Marcus", "Nasser", "Li", "Omar", "Jessica", "Mohamed", "Rachel", "Bader",
        "Priya", "Robert", "Grace", "Hassan", "Maria", "Vikram", "Leila", "Lucas"
    ]
    last_names = [
        "Al-Harbi", "Rostova", "Chang", "Zahra", "Mansoor", "Jenkins", "Miller", "Dubois",
        "Tanaka", "Kassem", "Silva", "Ivanova", "Doe", "Sharma", "Al-Qasimi", "Farooq",
        "Vance", "Al-Ghamdi", "Wei", "Siddiqui", "Taylor", "Al-Otaibi", "Kowalski", "Al-Nuaimi",
        "Patel", "Chen", "Hopper", "Malik", "Rodriguez", "Malhotra", "Haddad", "Al-Mutawa"
    ]

    users_list = []
    for i in range(1, 81):
        u_id = f"U-{1000 + i}"
        fn = first_names[(i - 1) % len(first_names)]
        ln = last_names[(i * 3) % len(last_names)]
        users_list.append((u_id, f"{fn} {ln}"))

    # Intentional toxic combinations
    # SOD-01: Vendor Creation + Payment
    sod_01_users = users_list[0:4] # 4 users
    # SOD-02: PO Requisitioner + PO Approver
    sod_02_users = users_list[4:9] # 5 users
    # SOD-04: Invoice Entry + Payment Release
    sod_04_users = users_list[9:14] # 5 users
    # SOD-05: Security Admin + Business Role
    sod_05_users = users_list[14:17] # 3 users

    rows = []

    # Assign toxic pairs
    for u_id, name in sod_01_users:
        rows.append({"user_id": u_id, "username": name, "department": "Finance", "assigned_role": "Vendor Master Admin", "system_permissions": "SAP_MM_VENDOR_CREATE, SAP_MM_VENDOR_EDIT", "status": "Active"})
        rows.append({"user_id": u_id, "username": name, "department": "Finance", "assigned_role": "Disbursement Cashier", "system_permissions": "SAP_FI_PAY_DISBURSE, SAP_FI_CHECK_PRINT", "status": "Active"})

    for u_id, name in sod_02_users:
        rows.append({"user_id": u_id, "username": name, "department": "Operations", "assigned_role": "Purchase Requisitioner", "system_permissions": "SAP_MM_PR_CREATE, SAP_MM_PR_SUBMIT", "status": "Active"})
        rows.append({"user_id": u_id, "username": name, "department": "Operations", "assigned_role": "Purchase Order Approver", "system_permissions": "SAP_MM_PO_APPROVE, SAP_MM_RELEASE_T1", "status": "Active"})

    for u_id, name in sod_04_users:
        rows.append({"user_id": u_id, "username": name, "department": "Finance", "assigned_role": "Invoice Processing Clerk", "system_permissions": "SAP_FI_INV_ENTRY, SAP_FI_INV_VERIFY", "status": "Active"})
        rows.append({"user_id": u_id, "username": name, "department": "Finance", "assigned_role": "Electronic Payment Release", "system_permissions": "SAP_FI_PAY_RELEASE, SAP_FI_BATCH_EXEC", "status": "Active"})

    for u_id, name in sod_05_users:
        rows.append({"user_id": u_id, "username": name, "department": "IT", "assigned_role": "Security Administrator", "system_permissions": "SAP_BC_USER_ADMIN, SAP_BC_ROLE_ASSIGN", "status": "Active"})
        rows.append({"user_id": u_id, "username": name, "department": "Finance", "assigned_role": "AP Disbursement Clerk", "system_permissions": "SAP_FI_PAY_RELEASE", "status": "Active"})

    # Remaining compliant users (63 users)
    compliant_roles_pool = [
        ("Logistics", "Warehouse Receiving Officer", "SAP_MM_GRN_POST, SAP_MM_STOCK_VIEW"),
        ("Logistics", "Inventory Controller", "SAP_MM_INV_COUNT, SAP_MM_PHY_RECON"),
        ("Procurement", "Strategic Sourcing Specialist", "SAP_MM_RFQ_CREATE, SAP_MM_BID_EVAL"),
        ("Procurement", "Buyer Senior", "SAP_MM_PO_CREATE, SAP_MM_CONTRACT_MAINT"),
        ("Finance", "General Ledger Accountant", "SAP_FI_GL_POST, SAP_FI_JOURNAL_ENTRY"),
        ("Finance", "Tax Compliance Officer", "SAP_FI_TAX_CALC, SAP_FI_VAT_REPORT"),
        ("Finance", "Accounts Receivable Clerk", "SAP_SD_CUST_INVOICE, SAP_FI_AR_RECEIPT"),
        ("Treasury", "Bank Reconciliation Analyst", "SAP_FI_BANK_RECON, SAP_TR_CASH_VIEW"),
        ("Internal Audit", "Audit Observer", "SAP_AUDIT_READ_ALL"),
        ("Operations", "Department Budget Manager", "SAP_CO_BUDGET_VIEW, SAP_CO_COST_ALLOC")
    ]

    for u_id, name in users_list[17:]:
        # Assign 1 to 2 compatible non-conflicting roles
        dept, role, perm = random.choice(compliant_roles_pool)
        rows.append({"user_id": u_id, "username": name, "department": dept, "assigned_role": role, "system_permissions": perm, "status": "Active"})
        
        if random.random() > 0.4:
            # Second compatible role
            compatibles = [c for c in compliant_roles_pool if c[0] == dept and c[1] != role]
            if compatibles:
                dept2, role2, perm2 = random.choice(compatibles)
                rows.append({"user_id": u_id, "username": name, "department": dept2, "assigned_role": role2, "system_permissions": perm2, "status": "Active"})

    df = pd.DataFrame(rows)
    return df

def generate_process_mining_event_log_large() -> pd.DataFrame:
    """
    Generates a realistic P2P event log covering 100 cases (600+ events)
    with intentional control bypasses and path variants:
      - Variant A: Compliant Golden Path (65% of cases)
      - Variant B: Goods Receipt Omitted / Skipped before Invoice (18% of cases)
      - Variant C: Retroactive PR Approval after Invoice posted (12% of cases)
      - Variant D: Direct Invoicing / Maverick Spend without PO (5% of cases)
    """
    random.seed(303)
    events = []

    users_roles = {
        "Create PR": ["Ahmed_Requisitioner", "Elena_Staff", "Kavita_Buyer", "Carlos_Ops"],
        "Approve PR": ["Sarah_DeptHead", "David_Director", "Jessica_VP"],
        "Issue PO": ["Tariq_Buyer", "Marcus_Purchaser", "Nasser_Buyer"],
        "Record GRN": ["Michael_Warehouse", "Lucas_Receiving", "Li_Logistics"],
        "Post Invoice": ["Fatima_AP", "Amira_AP", "Svetlana_AP"],
        "Release Payment": ["Zaid_Treasury", "Robert_Treasurer", "Grace_Disbursement"]
    }

    base_time = datetime.datetime(2026, 1, 5, 8, 0, 0)

    for case_num in range(1, 101):
        case_id = f"PO-{1000 + case_num}"
        dept = random.choice(["Manufacturing", "IT Services", "Facilities", "Supply Chain", "Corporate Marketing"])
        
        # Determine flow variant
        r_val = random.random()
        t = base_time + datetime.timedelta(days=case_num * 0.7, hours=random.randint(1, 4))

        if r_val < 0.65:
            # Compliant Golden Path
            flow = [
                ("Create PR", 0),
                ("Approve PR", random.randint(2, 6)),
                ("Issue PO", random.randint(4, 12)),
                ("Record GRN", random.randint(24, 72)),
                ("Post Invoice", random.randint(12, 36)),
                ("Release Payment", random.randint(24, 96))
            ]
        elif r_val < 0.83:
            # Variant B: GRN Bypassed (Goods receipt missing before invoice)
            flow = [
                ("Create PR", 0),
                ("Approve PR", random.randint(2, 6)),
                ("Issue PO", random.randint(4, 12)),
                ("Post Invoice", random.randint(12, 48)), # GRN omitted!
                ("Release Payment", random.randint(24, 72))
            ]
        elif r_val < 0.95:
            # Variant C: Retroactive PR Approval (Invoice arrived before approval)
            flow = [
                ("Create PR", 0),
                ("Issue PO", random.randint(2, 6)),
                ("Post Invoice", random.randint(6, 18)), # Invoice entered before approval
                ("Approve PR", random.randint(24, 48)),  # Retroactive approval!
                ("Release Payment", random.randint(24, 48))
            ]
        else:
            # Variant D: Direct Invoicing / Emergency After-the-fact
            flow = [
                ("Post Invoice", 0),
                ("Create PR", random.randint(4, 12)),
                ("Approve PR", random.randint(12, 24)),
                ("Release Payment", random.randint(24, 48))
            ]

        curr_t = t
        for act, delay_hrs in flow:
            curr_t += datetime.timedelta(hours=delay_hrs)
            actor = random.choice(users_roles.get(act, ["System_User"]))
            events.append({
                "case_id": case_id,
                "activity": act,
                "timestamp": curr_t.strftime("%Y-%m-%d %H:%M:%S"),
                "user": actor,
                "department": dept
            })

    df = pd.DataFrame(events)
    return df

def main():
    print("==========================================================")
    print("FieldAI Synthetic Data Generator for Audit Hub")
    print("==========================================================")
    
    # 1. Create sample_data directory if it doesn't exist
    sample_dir = Path("sample_data")
    sample_dir.mkdir(parents=True, exist_ok=True)

    # 2. Generate 1,000 records for Data Analytics
    print("[1/3] Generating 1,000 procurement invoice transactions...")
    df_invoices = generate_analytics_invoices_1000()
    invoices_1000_csv = sample_dir / "invoices_extract_1000.csv"
    invoices_sample_csv = sample_dir / "invoices_extract.csv" # update standard sample as well
    df_invoices.to_csv(invoices_1000_csv, index=False)
    df_invoices.to_csv(invoices_sample_csv, index=False)
    print(f" -> Saved {len(df_invoices)} records to {invoices_1000_csv}")
    print(f" -> Updated {invoices_sample_csv} with 1,000 records")

    # 3. Generate Large User Access Matrix for SoD
    print("\n[2/3] Generating comprehensive User Access Matrix for SoD...")
    df_sod = generate_sod_matrix_large()
    sod_large_csv = sample_dir / "user_access_matrix_large.csv"
    sod_sample_csv = sample_dir / "user_access_matrix.csv"
    df_sod.to_csv(sod_large_csv, index=False)
    df_sod.to_csv(sod_sample_csv, index=False)
    print(f" -> Saved {len(df_sod)} user-role assignments across {df_sod['user_id'].nunique()} users to {sod_large_csv}")

    # 4. Generate Large ERP Event Log for Process Mining
    print("\n[3/3] Generating enterprise P2P ERP Event Log for Process Mining...")
    df_pm = generate_process_mining_event_log_large()
    pm_large_csv = sample_dir / "erp_event_log_large.csv"
    pm_sample_csv = sample_dir / "erp_event_log.csv"
    df_pm.to_csv(pm_large_csv, index=False)
    df_pm.to_csv(pm_sample_csv, index=False)
    print(f" -> Saved {len(df_pm)} event rows across {df_pm['case_id'].nunique()} cases to {pm_large_csv}")

    # 5. Save all datasets persistently in Centralized Data Storage (core/storage.py)
    print("\n[Centralized Storage] Ingesting files into Centralized Storage repository...")
    with open(invoices_1000_csv, "rb") as f:
        inv_data = f.read()
    fid_inv = save_file(
        filename="invoices_extract_1000.csv",
        mime_type="text/csv",
        data=inv_data,
        category="source_documents",
        process_id=1,
        created_by=1
    )
    print(f" -> Ingested invoices_extract_1000.csv (Storage File ID: #{fid_inv})")

    with open(sod_large_csv, "rb") as f:
        sod_data = f.read()
    fid_sod = save_file(
        filename="user_access_matrix_large.csv",
        mime_type="text/csv",
        data=sod_data,
        category="source_documents",
        process_id=1,
        created_by=1
    )
    print(f" -> Ingested user_access_matrix_large.csv (Storage File ID: #{fid_sod})")

    with open(pm_large_csv, "rb") as f:
        pm_data = f.read()
    fid_pm = save_file(
        filename="erp_event_log_large.csv",
        mime_type="text/csv",
        data=pm_data,
        category="source_documents",
        process_id=1,
        created_by=1
    )
    print(f" -> Ingested erp_event_log_large.csv (Storage File ID: #{fid_pm})")

    print("\n[SUCCESS] All synthetic datasets successfully generated and archived in Centralized Storage!")

if __name__ == "__main__":
    main()
