import json
from typing import Dict, Any, List
from graphs.state import FieldAIState
from core.db import db
from core.llm import llm
from core.schemas import ChangeItem
from core.model_repo import get_process_master_model

PROMPT_CHANGE_SET_SYSTEM = """You are FieldAI, an expert internal auditor performing entity resolution and change detection between a prior master process model and a new walkthrough meeting.
Compare the new extracted items against the current master model.
Classify each item as:
- 'Added': New step/risk/control not present in prior model.
- 'Changed': Existing step modified (e.g. system changed, new role responsible, threshold changed).
- 'Confirmed': Re-verified to be identical to current model.
- 'Contradicted': New statement directly contradicts prior documentation (e.g. prior says dual approval required, auditee states only single approval is done). Provide conflict_with details.
- 'Removed': Step or control mentioned as discontinued.

Return JSON format:
{
  "change_items": [
    {
      "entity": "step" | "risk" | "control",
      "action": "Added" | "Changed" | "Confirmed" | "Contradicted" | "Removed",
      "target_code": "P2P-02",
      "before": {...},
      "after": {...},
      "evidence": ["00:04:15 - Auditee statement..."],
      "conflict_with": "Prior model states General Manager approval required over $10k, but interviewee states $25k threshold."
    }
  ]
}"""

def run(state: FieldAIState) -> Dict[str, Any]:
    """
    Change Set Agent (FR-6.1-6.6, 6.9):
    Performs entity resolution and diffs new walkthrough against master model.
    """
    process_id = state.get("process_id", 1)
    source_id = state.get("source_id")
    
    current_model = get_process_master_model(process_id)
    new_steps = state.get("extracted_steps", [])
    new_risks = state.get("extracted_risks", [])
    new_controls = state.get("extracted_controls", [])

    is_initial_run = len(current_model["steps"]) == 0

    change_items = []

    if is_initial_run:
        # First meeting of a process: All items are 'Added'
        for s in new_steps:
            change_items.append({
                "entity": "step",
                "action": "Added",
                "target_code": s.get("step_code"),
                "before": None,
                "after": s,
                "evidence": [src.get("locator", "") for src in s.get("sources", [])],
                "conflict_with": None,
                "decision": "accepted"
            })
        for r in new_risks:
            change_items.append({
                "entity": "risk",
                "action": "Added",
                "target_code": r.get("risk_code"),
                "before": None,
                "after": r,
                "evidence": [src.get("locator", "") for src in r.get("sources", [])],
                "conflict_with": None,
                "decision": "accepted"
            })
        for c in new_controls:
            change_items.append({
                "entity": "control",
                "action": "Added",
                "target_code": c.get("control_code"),
                "before": None,
                "after": c,
                "evidence": [src.get("locator", "") for src in c.get("sources", [])],
                "conflict_with": None,
                "decision": "accepted"
            })
    else:
        # Diff against existing model using LLM entity resolution
        comparison_context = {
            "current_master_model": current_model,
            "new_extraction": {
                "steps": new_steps,
                "risks": new_risks,
                "controls": new_controls
            }
        }
        res = llm.generate_json(
            prompt=f"Perform entity resolution and diff:\n{json.dumps(comparison_context, indent=2, ensure_ascii=False, default=str)}",
            system_prompt=PROMPT_CHANGE_SET_SYSTEM
        )
        change_items = res.get("change_items", [])

    # Persist change set to database
    change_set_id = db.execute_insert(
        "INSERT INTO change_sets (process_id, source_id, status) VALUES (%s, %s, 'draft');",
        (process_id, source_id)
    )

    for item in change_items:
        db.execute_insert(
            """
            INSERT INTO change_items (change_set_id, entity, action, target_code, before_json, after_json, evidence_json, conflict_with, decision)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);
            """,
            (
                change_set_id,
                item.get("entity", "step"),
                item.get("action", "Added"),
                item.get("target_code", ""),
                json.dumps(item.get("before"), default=str) if item.get("before") else None,
                json.dumps(item.get("after"), default=str) if item.get("after") else None,
                json.dumps(item.get("evidence", []), default=str),
                item.get("conflict_with"),
                item.get("decision", "pending")
            )
        )

    return {"change_set": change_items}
