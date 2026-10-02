import json
from typing import Dict, Any, List
from graphs.state import FieldAIState
from core.db import db
from core.llm import llm

PROMPT_KNOWLEDGE_SYSTEM = """You are FieldAI Knowledge Agent.
Analyze historical internal audit models to identify reusable controls and detect Year-on-Year (YoY) changes between audit periods.
Compare previous year's controls and current practices, highlighting:
- Newly introduced systems (e.g. migration to cloud ERP)
- Changed approval thresholds
- Discontinued control activities
- Benchmark suggestions from approved historical processes

Return JSON format:
{
  "yoy_changes": [
    {"area": "System", "prior_year": "Oracle EBS", "current_year": "SAP S/4HANA Cloud", "impact": "Automated matching logic changed"},
    {"area": "Threshold", "prior_year": "$5,000 Dept Head limit", "current_year": "$10,000 limit", "impact": "Increased risk exposure"}
  ],
  "reusable_library_controls": [
    {"code": "C-BENCH-01", "name": "Automated duplicate payment check in batch runs", "rationale": "Successfully implemented in Manufacturing audit"}
  ]
}"""

def run(state: FieldAIState) -> Dict[str, Any]:
    """
    Knowledge Agent (Options 9, 19):
    Cross-engagement process reuse and Year-on-Year change detection.
    """
    process_id = state.get("process_id", 1)
    
    # Check prior approved versions in database
    versions = db.fetch_all(
        "SELECT version_label, change_log, snapshot_json FROM versions WHERE process_id = %s ORDER BY id DESC LIMIT 2;",
        (process_id,)
    )

    context = {
        "historical_versions": [
            {"version": v["version_label"], "change_log": v["change_log"]} for v in versions
        ]
    }

    res = llm.generate_json(
        prompt=f"Perform knowledge reuse and YoY change analysis:\n{json.dumps(context, indent=2, ensure_ascii=False)}",
        system_prompt=PROMPT_KNOWLEDGE_SYSTEM
    )

    return {"knowledge_insights": res}
