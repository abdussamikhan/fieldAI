import json
from typing import Dict, Any, List
from graphs.state import FieldAIState
from core.db import db
from core.llm import llm

PROMPT_COPILOT_SYSTEM = """You are FieldAI Co-Pilot, an active near-live interview assistant whispering actionable prompts to the auditor during a walkthrough.
Analyze this short recording chunk from the ongoing interview.
Identify:
1. Missing control inquiries or ambiguous statements (e.g. 'Who has authority to override this?', 'What happens during system downtime?', 'How are emergency purchases handled?').
2. Any new evidence items or reports the auditee referenced that should immediately be requested (PBC requests).

Return JSON format:
{
  "follow_up_prompts": [
    "Ask Tariq what happens if the vendor price changes between PO and invoice.",
    "Clarify who approves exceptions when the department head is on leave."
  ],
  "captured_pbc": [
    {"item": "Sample of emergency PO approval form", "owner": "Sarah", "reason": "Mentioned as manual workaround"}
  ]
}"""

def run(state: FieldAIState) -> Dict[str, Any]:
    """
    Co-pilot Agent (Options 3, 4):
    Near-live walkthrough co-pilot suggesting instant follow-up questions and capturing PBC evidence.
    """
    process_id = state.get("process_id", 1)
    chunk_text = state.get("task_input", "") or "Auditee: Sometimes when the system is offline, we fill out a manual paper slip and process it later."
    
    # Retrieve existing open items to prevent redundant questions
    open_items = db.fetch_all("SELECT question FROM open_items WHERE process_id = %s;", (process_id,))
    
    context = {
        "audio_chunk_transcript": chunk_text,
        "existing_open_questions": [o["question"] for o in open_items]
    }

    res = llm.generate_json(
        prompt=f"Generate real-time auditor co-pilot recommendations:\n{json.dumps(context, indent=2, ensure_ascii=False)}",
        system_prompt=PROMPT_COPILOT_SYSTEM
    )

    prompts = res.get("follow_up_prompts", [])
    pbc_items = res.get("captured_pbc", [])

    return {
        "copilot_prompts": prompts,
        "copilot_pbc": pbc_items
    }
