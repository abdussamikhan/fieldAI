import json
from typing import Dict, Any, List
from graphs.state import FieldAIState
from core.db import db
from core.llm import llm
from core.schemas import Finding

PROMPT_FINDINGS_SYSTEM = """You are FieldAI, an expert Chief Audit Executive (CAE) writing formal internal audit findings following the 5 Cs format:
1. Condition: Clear statement of the factual deficiency or exception identified.
2. Criteria: The specific standard, policy requirement, or benchmark (e.g. SOP §3.2, Delegation of Authority).
3. Cause: The underlying root cause (e.g. lack of system enforcement, informal practice, staff turnover).
4. Effect: The measurable risk, financial exposure, or regulatory impact.
5. Recommendation: Practical, cost-effective corrective action plan.

Also provide:
- finding_code: E.g., 'F-01', 'F-02'
- title: Executive headline
- rating: 'High', 'Medium', or 'Low'

Return JSON format:
{
  "findings": [
    {
      "finding_code": "F-01",
      "title": "Bypass of Goods Receipt Inspection Prior to Invoice Disbursement",
      "condition": "During walkthrough testing, 2 of 25 tested purchase transactions bypassed Goods Receipt Note (GRN) logging...",
      "criteria": "SOP-FIN-04 Section 4 mandates physical warehouse count and GRN entry within 24 hours of delivery...",
      "cause": "ERP tolerance setting allowed invoice matching without a mandatory positive GRN flag...",
      "effect": "Risk of making disbursements for damaged, defective, or unreceived physical inventory...",
      "recommendation": "Configure a hard-stop validation rule in SAP preventing AP invoice processing without a validated GRN reference.",
      "rating": "High",
      "linked_controls": ["C-02"],
      "linked_tests": ["T-02"]
    }
  ]
}"""

def run(state: FieldAIState) -> Dict[str, Any]:
    """
    Findings Agent (Option 15):
    Drafts comprehensive 5 Cs audit findings from test exceptions, gaps, and reconciliation items.
    """
    process_id = state.get("process_id", 1)
    
    # Check for exceptions in test_runs
    exceptions = db.fetch_all(
        """
        SELECT tr.result_summary, tr.exceptions_count, t.test_code, t.control_code 
        FROM test_runs tr
        JOIN tests t ON tr.test_id = t.id
        WHERE tr.exceptions_count > 0;
        """
    )
    
    # Check for reconciliation gaps
    recon_gaps = db.fetch_all(
        "SELECT * FROM recon_items WHERE process_id = %s AND category IN ('Conflicting detail', 'Documented-not-described');",
        (process_id,)
    )

    context = {
        "exceptions": exceptions,
        "reconciliation_gaps": recon_gaps
    }

    res = llm.generate_json(
        prompt=f"Draft 5 Cs internal audit findings from these fieldwork results:\n{json.dumps(context, indent=2, ensure_ascii=False)}",
        system_prompt=PROMPT_FINDINGS_SYSTEM
    )

    findings = res.get("findings", [])

    # Save to findings table in database
    for f in findings:
        db.execute_insert(
            """
            INSERT INTO findings (process_id, finding_code, title, condition_text, criteria_text, cause_text, effect_text, recommendation_text, rating, linked_tests, linked_controls, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'draft');
            """,
            (
                process_id,
                f.get("finding_code", "F-01"),
                f.get("title", "Audit Finding"),
                f.get("condition", ""),
                f.get("criteria", ""),
                f.get("cause", ""),
                f.get("effect", ""),
                f.get("recommendation", ""),
                f.get("rating", "Medium"),
                ", ".join(f.get("linked_tests", [])),
                ", ".join(f.get("linked_controls", []))
            )
        )

    return {"findings": findings}
