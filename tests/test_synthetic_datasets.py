import pytest
import pandas as pd
from pathlib import Path
from analytics import library
from agents import sod_agent, process_mining_agent
from core.storage import list_storage_files, get_storage_stats

def test_invoices_1000_dataset():
    p = Path("sample_data/invoices_extract_1000.csv")
    assert p.exists()
    df = pd.read_csv(p)
    assert len(df) == 1000
    
    mapping = {c: c for c in df.columns}
    
    # Test AN-01 Duplicate payments
    dup = library.duplicate_payments(df, mapping)
    assert len(dup) >= 10
    
    # Test AN-02 Split purchases
    split = library.split_purchases(df, mapping)
    assert len(split) >= 5
    
    # Test AN-03 Weekend postings
    wkd = library.weekend_postings(df, mapping)
    assert len(wkd) >= 20
    
    # Test AN-04 Round amounts
    rnd = library.round_amounts(df, mapping)
    assert len(rnd) >= 15
    
    # Test AN-05 Below threshold
    below = library.below_threshold(df, mapping)
    assert len(below) >= 10
    
    # Test AN-06 Benford analysis
    benford = library.benford_analysis(df, mapping)
    assert benford["total_records"] == 1000
    assert "digits" in benford
    assert len(benford["digits"]) == 9
    
    # Test AN-07 Missing approvals
    appr = library.missing_approvals(df, mapping)
    assert len(appr) >= 15
    
    # Test AN-08 Three-way match
    twm = library.three_way_match(df, mapping)
    assert len(twm) >= 10
    
    # Test AN-09 Sequence gaps
    gaps = library.sequence_gaps(df, mapping)
    assert len(gaps) >= 5

def test_sod_large_dataset():
    p = Path("sample_data/user_access_matrix_large.csv")
    assert p.exists()
    df = pd.read_csv(p)
    assert len(df) >= 100
    assert df["user_id"].nunique() >= 50
    
    res = sod_agent.run({"test_request": {"test_type": "sod", "user_access": df}})
    conflicts = res.get("sod_conflicts", [])
    assert len(conflicts) >= 10

def test_process_mining_large_dataset():
    p = Path("sample_data/erp_event_log_large.csv")
    assert p.exists()
    df = pd.read_csv(p)
    assert len(df) >= 400
    assert df["case_id"].nunique() >= 50
    
    res = process_mining_agent.run({"test_request": {"test_type": "process_mining", "event_log": df}})
    pm = res.get("process_mining", {})
    assert pm.get("total_cases") >= 50
    assert pm.get("distinct_variants") >= 3
    assert len(pm.get("bypassed_cases", [])) >= 10

def test_centralized_storage_samples():
    files = list_storage_files()
    filenames = [f["filename"] for f in files]
    assert "invoices_extract_1000.csv" in filenames
    assert "user_access_matrix_large.csv" in filenames
    assert "erp_event_log_large.csv" in filenames

def test_orchestrator_process_mining_e2e():
    from graphs.orchestrator import run_task
    res = run_task("run_test", {
        "task": "run_test",
        "process_id": 1,
        "user_id": 1,
        "test_request": {
            "test_type": "process_mining"
        }
    })
    assert "process_mining" in res
    pm = res["process_mining"]
    assert pm.get("total_cases") == 100
    assert pm.get("distinct_variants") >= 3
    assert len(pm.get("bypassed_cases", [])) >= 10

def test_orchestrator_sod_e2e():
    from graphs.orchestrator import run_task
    res = run_task("run_test", {
        "task": "run_test",
        "process_id": 1,
        "user_id": 1,
        "test_request": {
            "test_type": "sod"
        }
    })
    assert "sod_conflicts" in res
    assert len(res["sod_conflicts"]) >= 10
