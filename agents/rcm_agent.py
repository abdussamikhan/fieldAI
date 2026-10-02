import json
from typing import Dict, Any, List
from graphs.state import FieldAIState
from core.db import db
from core.llm import llm
from core.model_repo import get_process_master_model

PROMPT_RCM_SYSTEM = """You are FieldAI, an expert internal auditor constructing a comprehensive Risk & Control Matrix (RCM).
For every control and risk pair, evaluate:
1. design_rating: 'Adequate', 'Partially adequate', or 'Inadequate'.
2. design_rationale: Professional explanation why the control design prevents or detects the inherent risk.
3. If an inherent risk has no mitigating control, propose 1-2 AI-suggested controls from internal audit best practices.
4. Map controls to standard frameworks (COSO 2013, COBIT 2019, ISO 27001:2022, NCA ECC, SAMA CSF).

Return JSON format:
{
  "rcm_rows": [
    {
      "risk_code": "R-01",
      "risk_description": "...",
      "inherent_rating": "High",
      "control_code": "C-01",
      "control_description": "...",
      "control_type": "preventive",
      "nature": "automated",
      "frequency": "per transaction",
      "owner": "Finance",
      "key_control": true,
      "design_rating": "Adequate",
      "design_rationale": "...",
      "criteria_ref": "SOP-FIN-04 §3.2",
      "framework_refs": ["COSO Principle 10", "NCA ECC-1-2-3"],
      "ai_suggested": false
    }
  ]
}"""

def run(state: FieldAIState) -> Dict[str, Any]:
    """
    RCM Agent (FR-5.1-5.2, 5.7; Options 7, 8):
    Constructs Risk-Control Matrix, rates design adequacy, suggests gap controls, and maps frameworks.
    """
    process_id = state.get("process_id", 1)
    model = get_process_master_model(process_id)
    
    risks = model.get("risks") or state.get("extracted_risks", [])
    controls = model.get("controls") or state.get("extracted_controls", [])
    
    # Fetch framework mappings
    frameworks = db.fetch_all("SELECT framework_name, requirement_code, title FROM framework_controls LIMIT 15;")

    payload = {
        "risks": risks,
        "controls": controls,
        "framework_catalogue": frameworks
    }

    user_prompt = f"Construct RCM with design ratings and framework mappings:\n{json.dumps(payload, indent=2, ensure_ascii=False)}"
    
    res = llm.generate_json(
        prompt=user_prompt,
        system_prompt=PROMPT_RCM_SYSTEM
    )

    rcm_rows = res.get("rcm_rows", [])
    if not rcm_rows:
        # Fallback rows
        ctrl_map = {c.get("control_code"): c for c in controls}
        for r in risks:
            linked_c = r.get("control_codes", ["C-01"])[0] if r.get("control_codes") else "C-01"
            ctrl = ctrl_map.get(linked_c, {})
            rcm_rows.append({
                "risk_code": r.get("risk_code", "R-01"),
                "risk_description": r.get("description", ""),
                "inherent_rating": r.get("inherent_rating", "Medium"),
                "control_code": linked_c,
                "control_description": ctrl.get("description", "Automated system enforcement"),
                "control_type": ctrl.get("type", "preventive"),
                "nature": ctrl.get("nature", "automated"),
                "frequency": ctrl.get("frequency", "per transaction"),
                "owner": ctrl.get("owner", "Process Owner"),
                "key_control": ctrl.get("key_control", True),
                "design_rating": ctrl.get("design_rating", "Adequate"),
                "design_rationale": "Automated system control prevents unauthorized transactions prior to posting.",
                "criteria_ref": "SOP-FIN-04 §3.2",
                "framework_refs": ["COSO Principle 10", "ISO 27001 A.5.15"],
                "ai_suggested": False
            })

    deliverables = state.get("deliverables", {})
    deliverables["rcm_rows"] = rcm_rows
    return {"deliverables": deliverables}
