import json
from typing import Dict, Any, List
from graphs.state import FieldAIState
from core.db import db
from core.llm import llm
from core.schemas import Risk, Control, ExtractionOutput

PROMPT_RISK_CONTROL_SYSTEM = """You are FieldAI, an expert internal audit fieldwork specialist.
Based on the extracted process steps and interview transcript, identify all stated risks and internal controls.
Additionally, compare against standard internal audit risks/controls and suggest any missing controls to address unmitigated risks.

For each risk:
- risk_code: R-01, R-02...
- description: Inherent risk statement
- step_codes: Associated step codes (e.g. ['P2P-02'])
- inherent_rating: 'High', 'Medium', or 'Low'
- ai_suggested: false if stated by client in transcript, true if inferred/suggested
- confidence: 0.0 to 1.0

For each control:
- control_code: C-01, C-02...
- description: Precise internal control activity description
- step_codes: Associated step codes
- risk_codes: Associated risk codes it mitigates
- type: 'preventive' or 'detective'
- nature: 'automated', 'manual', or 'IT-dependent'
- frequency: 'per transaction', 'daily', 'weekly', 'monthly', 'quarterly', 'annual'
- owner: Job role responsible
- key_control: boolean true if critical
- design_rating: 'Adequate', 'Partially adequate', or 'Inadequate'
- framework_refs: e.g. ['COSO Principle 10', 'NCA ECC-1-2-3']
- ai_suggested: false if explicitly stated, true if recommended from library

Return JSON format:
{
  "risks": [...],
  "controls": [...]
}"""

def run(state: FieldAIState) -> Dict[str, Any]:
    """
    Risk & Control Agent (FR-2.3-2.6):
    Identifies client-stated and AI-suggested risks and controls, links them to steps,
    and flags segregation of duties conflicts.
    """
    steps = state.get("extracted_steps", [])
    process_id = state.get("process_id", 1)
    
    # Fetch risk and control library references
    risk_lib = db.fetch_all("SELECT risk_code, name, description FROM risk_library LIMIT 10;")
    ctrl_lib = db.fetch_all("SELECT control_code, name, description FROM control_library LIMIT 10;")
    
    context = {
        "steps": steps,
        "risk_library": risk_lib,
        "control_library": ctrl_lib
    }
    
    user_prompt = f"Analyze these process steps and map risks and controls:\n{json.dumps(context, indent=2, ensure_ascii=False)}"
    
    res = llm.generate_json(
        prompt=user_prompt,
        system_prompt=PROMPT_RISK_CONTROL_SYSTEM,
        schema=ExtractionOutput
    )

    risks = res.get("risks", [])
    controls = res.get("controls", [])

    # Format sequential codes
    for idx, r in enumerate(risks, 1):
        if not r.get("risk_code"):
            r["risk_code"] = f"R-{idx:02d}"
    for idx, c in enumerate(controls, 1):
        if not c.get("control_code"):
            c["control_code"] = f"C-{idx:02d}"

    return {
        "extracted_risks": risks,
        "extracted_controls": controls
    }
