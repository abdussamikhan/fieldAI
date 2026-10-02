import json
from typing import Dict, Any, List
from graphs.state import FieldAIState
from core.db import db
from core.llm import llm
from core.model_repo import get_process_master_model

PROMPT_QA_CHECKLIST = """You are FieldAI Quality Assurance Inspector.
Evaluate the completeness of this internal audit engagement file against the IIA Global Internal Audit Standards (2024) and standard firm methodology.
Checklist requirements:
1. Risk Coverage: Every identified risk must link to at least one control or be flagged with a formal gap memo.
2. Control Testing: Every key control must have an associated test of design or operating effectiveness.
3. Traceability: Every audit test step must specify required evidence/PBC and sample size basis.
4. Review & Approvals: Manager review notes must be formally documented.

Evaluate the file and generate specific QA review notes for the audit team to address before signoff.

Return JSON format:
{
  "compliance_score": 92,
  "summary": "Process file exhibits strong documentation with minor PBC evidence references to finalize.",
  "review_notes": [
    {
      "checklist_item": "Control Testing",
      "target_entity": "control",
      "target_code": "C-03",
      "note": "Verify sample size justification for manual telephone callback verification control.",
      "status": "open"
    }
  ]
}"""

def run(state: FieldAIState) -> Dict[str, Any]:
    """
    QA Review Agent (Option 17):
    Checks work papers against IIA Standards 2024 and methodology checklist, generating review notes.
    """
    process_id = state.get("process_id", 1)
    model = get_process_master_model(process_id)
    tests = db.fetch_all("SELECT test_code, control_code, sample_size, result FROM tests WHERE process_id = %s;", (process_id,))

    file_inventory = {
        "steps_count": len(model.get("steps", [])),
        "risks_count": len(model.get("risks", [])),
        "controls_count": len(model.get("controls", [])),
        "tests_count": len(tests),
        "tests": tests
    }

    res = llm.generate_json(
        prompt=f"Perform QA review on this audit file inventory:\n{json.dumps(file_inventory, indent=2, ensure_ascii=False)}",
        system_prompt=PROMPT_QA_CHECKLIST
    )

    notes = res.get("review_notes", [])
    for n in notes:
        db.execute_insert(
            """
            INSERT INTO review_notes (process_id, target_entity, note, status)
            VALUES (%s, %s, %s, 'open');
            """,
            (process_id, n.get("target_entity", "process"), n.get("note", ""))
        )

    return {"qa_review": res}
