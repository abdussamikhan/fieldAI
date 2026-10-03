import pytest
from exports.csv_export import export_rcm_csv, export_audit_program_csv
from exports.pdf import export_findings_pdf, export_executive_audit_report_pdf

def test_export_rcm_csv():
    rcm_rows = [
        {
            "risk_code": "R-P2P-01",
            "risk_description": "Unauthorized vendor creation",
            "inherent_rating": "High",
            "control_code": "C-P2P-01",
            "control_description": "Vendor master approval workflow",
            "control_type": "preventive",
            "nature": "automated",
            "frequency": "per transaction",
            "owner": "Finance Manager",
            "key_control": True,
            "design_rating": "Adequate",
            "criteria_ref": "Policy 4.1",
            "framework_refs": ["COSO-CC5.2", "NCA-CCC-1"]
        }
    ]
    csv_bytes = export_rcm_csv(rcm_rows)
    assert isinstance(csv_bytes, bytes)
    assert len(csv_bytes) > 0
    text = csv_bytes.decode("utf-8-sig")
    assert "Risk Code,Risk Description" in text
    assert "R-P2P-01" in text
    assert "COSO-CC5.2" in text

def test_export_audit_program_csv():
    tests = [
        {
            "test_code": "T-P2P-01",
            "control_code": "C-P2P-01",
            "objective": "Verify vendor approval audit trail",
            "test_type": "ToE",
            "procedure": "Inspect sample of 25 approved vendors",
            "sample_size": 25,
            "sample_basis": "Frequency table",
            "evidence_pbc": "ERP Workflow Logs",
            "performer": "Auditor",
            "reviewer": "Audit Manager",
            "wp_ref": "WP-401",
            "result": "Pass",
            "exception_note": "None"
        }
    ]
    csv_bytes = export_audit_program_csv(tests)
    assert isinstance(csv_bytes, bytes)
    assert len(csv_bytes) > 0
    text = csv_bytes.decode("utf-8-sig")
    assert "Test Code,Control Code" in text
    assert "T-P2P-01" in text
    assert "ERP Workflow Logs" in text

def test_export_findings_pdf():
    findings = [
        {
            "finding_code": "FIND-01",
            "title": "Split Purchase Orders Detected",
            "rating": "High",
            "status": "approved",
            "condition_text": "14 purchase orders split below threshold.",
            "criteria_text": "Procurement Manual Section 3.",
            "cause_text": "Lack of supervisory system block.",
            "effect_text": "$250,000 unapproved procurement.",
            "recommendation_text": "Enforce automated threshold aggregation.",
            "linked_controls": "C-P2P-02",
            "linked_tests": "AN-02"
        }
    ]
    pdf_bytes = export_findings_pdf(findings, "Procure-to-Pay")
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 1000
    assert pdf_bytes.startswith(b"%PDF")

def test_export_executive_audit_report_pdf():
    report_text = """Audit Analytics Procedure: AN-01 – Duplicate Invoice Payments
Report Date: October 03, 2026
Overall Risk Rating: High

| Report Metric | Result |
|---|---:|
| Population Tested | 1,000 transactions |
| Total Spend Tested | $14,846,576.45 |

---

1. Executive Summary & Audit Observation
FieldAI executed audit procedure **AN-01: Duplicate Payments Detection**.

| Indicator | Evidence | Potential Root Cause |
|---|---|---|
| Ineffective duplicate detection | 24 duplicate-related exceptions | ERP lacks matching |

- Found 12 potential duplicate invoice payments totaling $45,000.

1. Suspend identified pending disbursements immediately.
2. Reconcile vendor statements for matching invoice numbers.
"""
    pdf_bytes = export_executive_audit_report_pdf("Executive Analytics Summary", report_text, "AN-01")
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 1000
    assert pdf_bytes.startswith(b"%PDF")

