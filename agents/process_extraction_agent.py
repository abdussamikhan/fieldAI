from typing import Dict, Any, List
from graphs.state import FieldAIState
from core.db import db
from core.llm import llm
from core.schemas import ProcessStep, ExtractionOutput
from core.model_repo import get_process

PROMPT_EXTRACTION_SYSTEM = """You are FieldAI, an expert internal audit fieldwork assistant.
Extract the sequential business process steps described in this walkthrough transcript.
For each step, determine:
- step_code: Sequential code matching process code prefix (e.g. P2P-01, P2P-02...)
- order: 1, 2, 3...
- description: Detailed, professional description of the procedure.
- responsible_role: Specific job title or role (e.g. 'Requisitioner', 'Procurement Buyer', 'Warehouse Officer').
- responsible_person: Name of person if stated.
- department: E.g., 'Operations', 'Procurement', 'Finance', 'Logistics'.
- system: Application or tool used (e.g., 'SAP ERP', 'Coupa', 'Oracle', 'Manual').
- inputs: Prior documents or trigger (e.g. 'PR', 'Delivery Note').
- outputs: Resulting artifact (e.g. 'PO', 'GRN', 'Payment Proposal').
- is_decision: Boolean true if this is an approval, validation, or conditional branch.
- sources: [{kind: 'meeting', locator: '00:03:15'}]
- confidence: 0.0 to 1.0 confidence score.

Return JSON in this format:
{
  "steps": [
    ...
  ]
}"""

def run(state: FieldAIState) -> Dict[str, Any]:
    """
    Process Extraction Agent (FR-2.1-2.2, 2.6-2.9):
    Extracts ordered process steps, systems, hand-offs, and decision gateways.
    """
    transcript = state.get("transcript", [])
    source_id = state.get("source_id")
    process_id = state.get("process_id", 1)

    proc = get_process(process_id)
    prefix = proc.get("code_prefix", "P2P") if proc else "P2P"

    if not transcript and source_id:
        transcript = db.fetch_all(
            "SELECT speaker_label, speaker_name, start_s, end_s, text FROM transcript_segments WHERE source_id = %s ORDER BY start_s ASC;",
            (source_id,)
        )

    transcript_text = ""
    for seg in transcript:
        m = int(seg.get('start_s', 0) // 60)
        s = int(seg.get('start_s', 0) % 60)
        time_tag = f"[{m:02d}:{s:02d}]"
        spk = seg.get("speaker_name") or seg.get("speaker_label", "Speaker")
        transcript_text += f"{time_tag} {spk}: {seg.get('text', '')}\n"

    user_prompt = f"Process prefix: '{prefix}'. Extract all steps from this walkthrough:\n\n{transcript_text[:14000]}"
    
    res = llm.generate_json(
        prompt=user_prompt,
        system_prompt=PROMPT_EXTRACTION_SYSTEM,
        schema=ExtractionOutput
    )

    steps = res.get("steps", [])
    # Ensure correct sequential code format
    for idx, step in enumerate(steps, 1):
        if not step.get("step_code") or not step.get("step_code").startswith(prefix):
            step["step_code"] = f"{prefix}-{idx:02d}"
        step["order"] = idx

    return {"extracted_steps": steps}
