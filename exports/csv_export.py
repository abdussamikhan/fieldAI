import io
import csv
from typing import List, Dict, Any

def export_rcm_csv(rcm_rows: List[Dict[str, Any]]) -> bytes:
    """Exports Risk & Control Matrix rows to standard CSV format (UTF-8 with BOM for Excel compatibility)."""
    output = io.StringIO()
    writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL)
    headers = [
        "Risk Code", "Risk Description", "Inherent Rating",
        "Control Code", "Control Description", "Control Type",
        "Nature", "Frequency", "Control Owner", "Key Control",
        "Design Rating", "Criteria / SOP Ref", "Framework Mapping"
    ]
    writer.writerow(headers)
    for r in rcm_rows:
        frameworks = r.get("framework_refs", [])
        if isinstance(frameworks, list):
            fw_str = ", ".join(frameworks)
        else:
            fw_str = str(frameworks or "")

        writer.writerow([
            r.get("risk_code", ""),
            r.get("risk_description", ""),
            r.get("inherent_rating", "Medium"),
            r.get("control_code", ""),
            r.get("control_description", ""),
            r.get("control_type", "preventive"),
            r.get("nature", "automated"),
            r.get("frequency", "per transaction"),
            r.get("owner", ""),
            "Yes" if r.get("key_control", True) else "No",
            r.get("design_rating", "Adequate"),
            r.get("criteria_ref", ""),
            fw_str
        ])
    return output.getvalue().encode("utf-8-sig")

def export_audit_program_csv(tests: List[Dict[str, Any]]) -> bytes:
    """Exports Audit Program test steps to standard CSV format (UTF-8 with BOM for Excel compatibility)."""
    output = io.StringIO()
    writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL)
    headers = [
        "Test Code", "Control Code", "Test Objective", "Test Type",
        "Audit Procedure", "Sample Size", "Sample Basis", "Evidence / PBC",
        "Performer", "Reviewer", "WP Ref", "Result", "Exceptions / Notes"
    ]
    writer.writerow(headers)
    for t in tests:
        writer.writerow([
            t.get("test_code", ""),
            t.get("control_code", ""),
            t.get("objective", ""),
            t.get("test_type", "ToE"),
            t.get("procedure", ""),
            t.get("sample_size", 25),
            t.get("sample_basis", "Frequency-based sampling table"),
            t.get("evidence_pbc", ""),
            t.get("performer", "Auditor"),
            t.get("reviewer", "Audit Manager"),
            t.get("wp_ref", ""),
            t.get("result", "Untested"),
            t.get("exception_note", "")
        ])
    return output.getvalue().encode("utf-8-sig")
