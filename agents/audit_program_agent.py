import json
from typing import Dict, Any, List
from graphs.state import FieldAIState
from core.db import db
from core.llm import llm
from core.model_repo import get_process_master_model, get_next_code

PROMPT_PROGRAM_PROCEDURES = """You are FieldAI, an expert internal auditor developing detailed audit test procedures and testing attributes.
For each control, produce:
- objective: Purpose of the test
- test_type: 'ToD' (Test of Design) or 'ToE' (Test of Operating Effectiveness) or 'analytics'
- procedure: Actionable step-by-step test procedure (Inquiry, Observation, Inspection, Re-performance)
- evidence_pbc: Specific documents required from auditee
- attributes: List of specific test attributes (e.g. ['Valid PO exists', 'Authorized approval signature', '3-way match verified', 'No price variance > 0%'])
- criteria_ref: Relevant SOP or policy clause citation

Return JSON format:
{
  "procedures": [
    {
      "control_code": "C-01",
      "objective": "Verify that all purchase requisitions above $10,000 are formally approved...",
      "test_type": "ToE",
      "procedure": "Select a representative sample of approved POs. Inspect approval log in SAP to verify...",
      "evidence_pbc": "SAP Purchase Order approval history report for the fiscal year",
      "attributes": ["Approved by authorized department head", "Approval occurred prior to PO release", "Budget verification confirmed"],
      "criteria_ref": "SOP-FIN-04 §3.1"
    }
  ]
}"""

def get_deterministic_sample_size(frequency: str, risk_level: str) -> int:
    """
    Looks up sample size deterministically from sampling_table (FR-5.5).
    Never invented by LLM.
    """
    row = db.fetch_one(
        "SELECT sample_size FROM sampling_table WHERE frequency = %s AND risk_level = %s;",
        (frequency, risk_level)
    )
    if row:
        return row["sample_size"]
    # Fallback to standard 25 items
    return 25

def run(state: FieldAIState) -> Dict[str, Any]:
    """
    Audit Program Agent (FR-5.3-5.8, FR-7.6):
    Generates audit test procedures, sample sizes from sampling table, attributes, and PBC evidence links.
    """
    process_id = state.get("process_id", 1)
    model = get_process_master_model(process_id)
    controls = model.get("controls") or state.get("extracted_controls", [])
    
    # Request LLM procedures
    res = llm.generate_json(
        prompt=f"Generate audit test procedures for these controls:\n{json.dumps(controls, indent=2, ensure_ascii=False)}",
        system_prompt=PROMPT_PROGRAM_PROCEDURES
    )

    procedures = res.get("procedures", [])
    proc_by_ctrl = {p.get("control_code"): p for p in procedures}

    program_rows = []
    
    for idx, c in enumerate(controls, 1):
        c_code = c.get("control_code", f"C-{idx:02d}")
        p_info = proc_by_ctrl.get(c_code, {})

        freq = c.get("frequency", "per transaction")
        # Inherent risk rating from linked risk or default to Medium
        sample_size = get_deterministic_sample_size(freq, "Medium")
        test_code = f"T-{idx:02d}"

        test_data = {
            "test_code": test_code,
            "control_code": c_code,
            "objective": p_info.get("objective") or f"Test operating effectiveness of {c_code}",
            "test_type": p_info.get("test_type", "ToE"),
            "procedure": p_info.get("procedure") or f"Select sample of transactions. Inspect evidence in ERP to verify {c.get('description', '')}.",
            "sample_size": sample_size,
            "sample_basis": f"Deterministic sampling table ({freq} / Medium Risk)",
            "evidence_pbc": p_info.get("evidence_pbc") or "Sample transaction listing and ERP audit trails",
            "attributes": p_info.get("attributes", ["Authorized approval", "Timely execution", "Supporting documentation attached"]),
            "performer": "Auditor",
            "reviewer": "Audit Manager",
            "wp_ref": f"WP-{test_code}",
            "result": "Untested",
            "exception_note": "",
            "status": "draft"
        }
        program_rows.append(test_data)

        # Upsert into tests table
        db.execute(
            """
            INSERT INTO tests (process_id, test_code, control_code, objective, test_type, procedure, sample_size, sample_basis, evidence_pbc, attributes_json, performer, reviewer, wp_ref, result, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
            """,
            (
                process_id, test_code, c_code, test_data["objective"], test_data["test_type"],
                test_data["procedure"], sample_size, test_data["sample_basis"], test_data["evidence_pbc"],
                json.dumps(test_data["attributes"]), test_data["performer"], test_data["reviewer"],
                test_data["wp_ref"], test_data["result"], test_data["status"]
            )
        )

    deliverables = state.get("deliverables", {})
    deliverables["program_rows"] = program_rows
    return {"deliverables": deliverables}
