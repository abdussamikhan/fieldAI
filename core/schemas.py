from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class SourceRef(BaseModel):
    source_id: Optional[int] = None
    kind: str = "meeting" # "meeting" or "document"
    locator: str = ""     # e.g., "00:04:12" or "SOP v3 §3.2 p.4"

class ProcessStep(BaseModel):
    step_code: str
    order: int = 1
    description: str
    responsible_role: str = ""
    responsible_person: Optional[str] = ""
    department: str = ""
    system: str = ""
    inputs: str = ""
    outputs: str = ""
    frequency: str = "per transaction"
    documents: str = ""
    is_decision: bool = False
    sources: List[SourceRef] = Field(default_factory=list)
    confidence: float = 1.0

class Risk(BaseModel):
    risk_code: str
    description: str
    step_codes: List[str] = Field(default_factory=list)
    inherent_rating: str = "Medium" # High, Medium, Low
    ai_suggested: bool = False
    library_ref: Optional[str] = None
    sources: List[SourceRef] = Field(default_factory=list)
    confidence: float = 1.0

class Control(BaseModel):
    control_code: str
    description: str
    step_codes: List[str] = Field(default_factory=list)
    risk_codes: List[str] = Field(default_factory=list)
    type: str = "preventive" # preventive, detective
    nature: str = "automated" # manual, automated, IT-dependent
    frequency: str = "per transaction"
    owner: str = ""
    key_control: bool = True
    design_rating: str = "Adequate" # Adequate, Partially adequate, Inadequate
    framework_refs: List[str] = Field(default_factory=list)
    criteria_ref: Optional[str] = None
    ai_suggested: bool = False
    sources: List[SourceRef] = Field(default_factory=list)

class ChangeItem(BaseModel):
    entity: str # step, risk, control, link
    action: str # Added, Changed, Confirmed, Contradicted, Removed
    target_code: Optional[str] = None
    before: Optional[Dict[str, Any]] = None
    after: Optional[Dict[str, Any]] = None
    evidence: List[str] = Field(default_factory=list)
    conflict_with: Optional[str] = None

class ReconItem(BaseModel):
    category: str # Matches, Documented-not-described, Described-not-documented, Conflicting detail, Outdated document
    item_code: Optional[str] = None
    doc_ref: Optional[str] = ""
    meeting_ref: Optional[str] = ""
    note: str = ""
    suggested_action: str = ""

class TestStep(BaseModel):
    test_code: str
    control_code: str
    objective: str
    test_type: str = "ToE" # ToD, ToE, analytics
    procedure: str
    sample_size: int = 25
    sample_basis: str = "Frequency-based sampling table"
    evidence_pbc: List[str] = Field(default_factory=list)
    attributes: List[str] = Field(default_factory=list)
    performer: Optional[str] = "Auditor"
    reviewer: Optional[str] = "Audit Manager"
    wp_ref: Optional[str] = ""
    result: str = "Untested" # Untested, Pass, Exception, Inconclusive
    exception: Optional[str] = None

class Finding(BaseModel):
    finding_code: str
    title: str
    condition: str
    criteria: str
    cause: str
    effect: str
    recommendation: str
    rating: str = "Medium" # High, Medium, Low
    linked_tests: List[str] = Field(default_factory=list)
    linked_controls: List[str] = Field(default_factory=list)

class MeetingSummary(BaseModel):
    summary: str
    key_points: List[str] = Field(default_factory=list)
    open_questions: List[str] = Field(default_factory=list)
    pbc_requests: List[Dict[str, Any]] = Field(default_factory=list)
    bookmarks: List[Dict[str, Any]] = Field(default_factory=list)

class ExtractionOutput(BaseModel):
    steps: List[ProcessStep] = Field(default_factory=list)
    risks: List[Risk] = Field(default_factory=list)
    controls: List[Control] = Field(default_factory=list)
