import json
from typing import Dict, Any, List
from graphs.state import FieldAIState
from core.db import db
from core.llm import llm

PROMPT_PREP_QUESTION_PACK = """You are FieldAI, an expert internal auditor preparing for an upcoming walkthrough interview.
Generate a structured, bilingual (English and Arabic) question pack tailored to the process, prior open items, and relevant risks.

Group questions by process phase:
1. Initiation & Requisitioning
2. Authorization & Approvals
3. Goods Receipt & Quality Verification
4. Invoicing, Matching & Disbursement
5. System Access & Exception Handling

For each question provide:
- question_en: English wording
- question_ar: Arabic wording (الترجمة واللغة المهنية الدقيقة للتدقيق)
- objective: What the auditor is trying to confirm
- expected_evidence: Evidence or reports to request during interview

Also compute a risk-based scoping recommendation:
- inherent_risk_score: High / Medium / Low
- recommended_scope_areas: List of 3-4 key focus areas
- indicative_hours: Estimated audit fieldwork hours

Return JSON format:
{
  "scoping": {
    "inherent_risk_score": "High",
    "recommended_scope_areas": ["3-way matching controls", "Delegation of authority override risks"],
    "indicative_hours": 80
  },
  "question_pack": [
    {
      "phase": "Initiation",
      "question_en": "How does the system enforce budget availability prior to requisition submission?",
      "question_ar": "كيف يتحقق النظام تلقائياً من توفر الميزانية قبل تقديم طلب الشراء؟",
      "objective": "Verify automated budget check control",
      "expected_evidence": "SAP system configuration screenshot showing hard-budget block"
    }
  ]
}"""

def run(state: FieldAIState) -> Dict[str, Any]:
    """
    Prep Agent (FR-6.7; Options 1, 2):
    Generates bilingual question packs, follow-up meeting agendas, and risk-based scoping.
    """
    process_id = state.get("process_id", 1)
    open_items = db.fetch_all("SELECT question FROM open_items WHERE process_id = %s AND status = 'open';", (process_id,))
    risks = db.fetch_all("SELECT risk_code, description FROM risks WHERE process_id = %s;", (process_id,))

    context = {
        "open_items": [item["question"] for item in open_items],
        "identified_risks": risks
    }

    user_prompt = f"Prepare meeting question pack and scoping for process:\n{json.dumps(context, indent=2, ensure_ascii=False)}"
    
    res = llm.generate_json(
        prompt=user_prompt,
        system_prompt=PROMPT_PREP_QUESTION_PACK
    )

    return {"prep_package": res}
