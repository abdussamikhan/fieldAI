import json
from typing import Dict, Any, List
from graphs.state import FieldAIState
from core.llm import llm

PROMPT_EVIDENCE_SYSTEM = """You are FieldAI Evidence Reader.
Examine the extracted text from an uploaded audit sample evidence file (invoice, PO, approval screenshot, or ERP log).
Evaluate each required audit test attribute.
For each attribute, determine:
- status: 'Pass', 'Fail', or 'Unclear'
- quoted_evidence: The exact text, number, date, or signature line that proves the attribute
- finding_note: Explanation if 'Fail' or 'Unclear'

Return JSON format:
{
  "sample_id": "SAMPLE-01",
  "attributes_evaluated": [
    {
      "attribute": "Approved by authorized approver prior to order release",
      "status": "Pass",
      "quoted_evidence": "Electronic Signature: John Doe, Operations VP, Timestamp: 2026-02-14 09:12 UTC",
      "finding_note": ""
    },
    {
      "attribute": "Invoice amount matches purchase order total within tolerance",
      "status": "Fail",
      "quoted_evidence": "Invoice Total: $54,200 vs PO Total: $48,000",
      "finding_note": "Invoice exceeds PO by $6,200 (+12.9%) exceeding allowable 0% tolerance without amendment."
    }
  ]
}"""

def run(state: FieldAIState) -> Dict[str, Any]:
    """
    Evidence Agent (Option 12):
    OCRs evidence documents and evaluates test attributes with quoted support.
    """
    evidence_text = state.get("task_input") or (
        "PURCHASE ORDER: PO-9921\n"
        "Vendor: TechSupplies Ltd | Date: 2026-02-14\n"
        "Total PO Amount: $48,000.00\n"
        "Approval: Approved by John Doe (Operations VP) on 2026-02-14 09:12 UTC\n"
        "INVOICE: INV-1002\n"
        "Billed To: Alpha Corp | Total Amount: $54,200.00\n"
        "Payment Terms: Net 30"
    )

    test_attributes = [
        "Approved by authorized approver prior to order release",
        "Invoice amount matches purchase order total within tolerance",
        "Vendor name matches approved master vendor directory"
    ]

    prompt_payload = {
        "evidence_document_text": evidence_text,
        "test_attributes": test_attributes
    }

    res = llm.generate_json(
        prompt=f"Evaluate evidence against test attributes:\n{json.dumps(prompt_payload, indent=2, ensure_ascii=False)}",
        system_prompt=PROMPT_EVIDENCE_SYSTEM
    )

    return {"evidence_evaluation": res}
