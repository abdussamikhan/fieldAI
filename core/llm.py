import os
import json
import re
from typing import Type, TypeVar, Optional, Dict, Any, List
from pydantic import BaseModel
from openai import OpenAI

from core.config import config
from core.audit_log import log_audit

T = TypeVar("T", bound=BaseModel)

class LLMClient:
    def __init__(self):
        self.api_key = config.DEEPSEEK_API_KEY
        self.base_url = config.DEEPSEEK_BASE_URL
        self.model = config.DEEPSEEK_MODEL
        self._client = None
        if self.api_key:
            self._client = OpenAI(api_key=self.api_key, base_url=self.base_url)

    def generate_json(
        self,
        prompt: str,
        system_prompt: str,
        schema: Optional[Type[T]] = None,
        temperature: float = 0.2
    ) -> Dict[str, Any]:
        """
        Calls DeepSeek API with JSON mode and automatic retry on invalid JSON.
        If no API key is configured, provides a deterministic structured mock response.
        """
        if not self._client:
            return self._mock_fallback(prompt, schema)

        messages = [
            {"role": "system", "content": system_prompt + "\nReturn ONLY valid JSON matching the requested structure. No markdown formatting around the JSON."},
            {"role": "user", "content": prompt}
        ]

        # First attempt
        for attempt in range(2):
            try:
                response = self._client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=temperature,
                    response_format={"type": "json_object"}
                )
                raw_text = response.choices[0].message.content or "{}"
                # Strip markdown code blocks if present
                clean_text = re.sub(r"^```(?:json)?\s*", "", raw_text.strip(), flags=re.MULTILINE)
                clean_text = re.sub(r"\s*```$", "", clean_text.strip(), flags=re.MULTILINE)
                
                parsed = json.loads(clean_text)
                
                # If schema provided, validate against Pydantic model
                if schema:
                    validated = schema.model_validate(parsed)
                    return validated.model_dump()
                return parsed

            except Exception as e:
                if attempt == 0:
                    messages.append({"role": "user", "content": f"Your previous response had a JSON parsing/validation error: {e}. Please fix and output strictly valid JSON."})
                    continue
                else:
                    print(f"[LLM] Error calling DeepSeek: {e}. Falling back to default generation.")
                    return self._mock_fallback(prompt, schema)

        return self._mock_fallback(prompt, schema)

    def generate_text(self, prompt: str, system_prompt: str = "You are FieldAI, an expert internal audit assistant.") -> str:
        """Standard text generation (for Q&A, Ask FieldAI, etc.)"""
        if not self._client:
            return f"[FieldAI Assistant Response]\nRegarding your inquiry: Based on internal audit standards and walkthrough records, standard controls require dual approval, segregation of duties, and documented evidence."
        
        try:
            response = self._client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            return f"Error communicating with AI model: {e}"

    def _mock_fallback(self, prompt: str, schema: Optional[Type[T]]) -> Dict[str, Any]:
        """Provides structured mock responses when offline or testing."""
        prompt_lower = prompt.lower()
        
        if "summary" in prompt_lower:
            return {
                "summary": "Walkthrough conducted with Procurement and Finance teams regarding end-to-end purchase-to-pay workflow, ERP approval thresholds, and receiving controls.",
                "key_points": [
                    "Purchase requisitions above $10,000 require Department Head approval.",
                    "3-way matching is automatically enforced in SAP for standard POs.",
                    "Discrepancies exceeding 5% require Finance Director manual override."
                ],
                "open_questions": [
                    "What is the formal protocol when emergency goods are received after hours?",
                    "How are vendor master bank detail changes verified prior to disbursement?"
                ],
                "pbc_requests": [
                    {"item": "Procurement Policy & Delegation of Authority Matrix v2.4", "owner": "Procurement Manager", "due_hint": "Next Friday"},
                    {"item": "Sample of 25 matched PO, GRN, and Invoice vouchers", "owner": "Finance Team Lead", "due_hint": "In 2 weeks"}
                ],
                "bookmarks": [{"timestamp": "00:04:15", "topic": "Approval Thresholds"}]
            }
            
        elif "process" in prompt_lower or "step" in prompt_lower:
            return {
                "steps": [
                    {
                        "step_code": "P2P-01",
                        "order": 1,
                        "description": "User creates Purchase Requisition in ERP system specifying item, quantity, and budget code.",
                        "responsible_role": "Requisitioner",
                        "responsible_person": "Business User",
                        "department": "Operations",
                        "system": "SAP ERP",
                        "inputs": "Purchase Need",
                        "outputs": "Purchase Requisition (PR)",
                        "frequency": "per transaction",
                        "is_decision": False,
                        "confidence": 0.95,
                        "sources": [{"kind": "meeting", "locator": "00:01:15"}]
                    },
                    {
                        "step_code": "P2P-02",
                        "order": 2,
                        "description": "System checks budget availability and routes PR to Department Head for approval.",
                        "responsible_role": "Department Head",
                        "responsible_person": "Sarah Jenkins",
                        "department": "Operations",
                        "system": "SAP ERP",
                        "inputs": "Purchase Requisition",
                        "outputs": "Approved PR",
                        "frequency": "per transaction",
                        "is_decision": True,
                        "confidence": 0.92,
                        "sources": [{"kind": "meeting", "locator": "00:03:40"}]
                    },
                    {
                        "step_code": "P2P-03",
                        "order": 3,
                        "description": "Procurement Buyer receives approved PR, selects approved vendor from master file, and issues PO.",
                        "responsible_role": "Procurement Buyer",
                        "responsible_person": "Tariq Al-Mansoor",
                        "department": "Procurement",
                        "system": "SAP ERP",
                        "inputs": "Approved PR",
                        "outputs": "Purchase Order (PO)",
                        "frequency": "per transaction",
                        "is_decision": False,
                        "confidence": 0.94,
                        "sources": [{"kind": "meeting", "locator": "00:07:22"}]
                    },
                    {
                        "step_code": "P2P-04",
                        "order": 4,
                        "description": "Warehouse receives physical shipment, inspects condition, and records Goods Receipt Note (GRN) in ERP.",
                        "responsible_role": "Warehouse Officer",
                        "responsible_person": "Ali Hassan",
                        "department": "Logistics",
                        "system": "SAP ERP",
                        "inputs": "Physical Goods & Delivery Note",
                        "outputs": "Goods Receipt Note (GRN)",
                        "frequency": "per transaction",
                        "is_decision": False,
                        "confidence": 0.91,
                        "sources": [{"kind": "meeting", "locator": "00:12:05"}]
                    },
                    {
                        "step_code": "P2P-05",
                        "order": 5,
                        "description": "Accounts Payable logs vendor invoice; ERP automatically performs 3-way match against PO and GRN.",
                        "responsible_role": "AP Clerk",
                        "responsible_person": "Fatima Zahra",
                        "department": "Finance",
                        "system": "SAP ERP",
                        "inputs": "Vendor Invoice, PO, GRN",
                        "outputs": "Matched Voucher / Payment Proposal",
                        "frequency": "per transaction",
                        "is_decision": True,
                        "confidence": 0.96,
                        "sources": [{"kind": "meeting", "locator": "00:16:30"}]
                    }
                ],
                "risks": [
                    {
                        "risk_code": "R-01",
                        "description": "Unauthorized purchases made outside delegation of authority matrix.",
                        "step_codes": ["P2P-02"],
                        "inherent_rating": "High",
                        "ai_suggested": False,
                        "confidence": 0.90,
                        "sources": [{"kind": "meeting", "locator": "00:04:00"}]
                    },
                    {
                        "risk_code": "R-02",
                        "description": "Disbursement made for goods not actually received or defective.",
                        "step_codes": ["P2P-04", "P2P-05"],
                        "inherent_rating": "High",
                        "ai_suggested": False,
                        "confidence": 0.93,
                        "sources": [{"kind": "meeting", "locator": "00:13:10"}]
                    },
                    {
                        "risk_code": "R-03",
                        "description": "Fictitious vendor onboarding or unauthorized modification of supplier bank accounts.",
                        "step_codes": ["P2P-03"],
                        "inherent_rating": "High",
                        "ai_suggested": True,
                        "library_ref": "R-LIB-01",
                        "confidence": 0.88,
                        "sources": [{"kind": "meeting", "locator": "00:08:15"}]
                    }
                ],
                "controls": [
                    {
                        "control_code": "C-01",
                        "description": "Automated workflow approval limits configured in ERP based on official Delegation of Authority.",
                        "step_codes": ["P2P-02"],
                        "risk_codes": ["R-01"],
                        "type": "preventive",
                        "nature": "automated",
                        "frequency": "per transaction",
                        "owner": "Finance & IT",
                        "key_control": True,
                        "design_rating": "Adequate",
                        "framework_refs": ["COSO Principle 10", "NCA ECC-1-2-3"],
                        "ai_suggested": False,
                        "sources": [{"kind": "meeting", "locator": "00:04:30"}]
                    },
                    {
                        "control_code": "C-02",
                        "description": "Automated 3-way match in ERP blocking invoice payment unless price and quantity match PO and GRN.",
                        "step_codes": ["P2P-05"],
                        "risk_codes": ["R-02"],
                        "type": "preventive",
                        "nature": "automated",
                        "frequency": "per transaction",
                        "owner": "Accounts Payable Manager",
                        "key_control": True,
                        "design_rating": "Adequate",
                        "framework_refs": ["COSO Principle 10", "COBIT BAI03.05"],
                        "ai_suggested": False,
                        "sources": [{"kind": "meeting", "locator": "00:17:00"}]
                    },
                    {
                        "control_code": "C-03",
                        "description": "Dual review and independent telephone call-back verification for all supplier bank detail updates.",
                        "step_codes": ["P2P-03"],
                        "risk_codes": ["R-03"],
                        "type": "preventive",
                        "nature": "manual",
                        "frequency": "per transaction",
                        "owner": "Treasury Lead",
                        "key_control": True,
                        "design_rating": "Adequate",
                        "framework_refs": ["ISO 27001 A.5.15"],
                        "ai_suggested": True,
                        "sources": [{"kind": "meeting", "locator": "00:09:00"}]
                    }
                ]
            }

        return {}

llm = LLMClient()
