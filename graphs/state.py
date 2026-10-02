from typing import TypedDict, List, Dict, Any, Optional

class FieldAIState(TypedDict, total=False):
    task: str                    # e.g. "process_meeting", "ingest_document", "build_program", "run_test", "ask"
    task_input: str
    engagement_id: int
    process_id: int
    source_id: int               # meeting or document being processed
    user_id: int
    language: str                # "ar", "en", "mixed"
    transcript: List[Dict[str, Any]]       # [{speaker_label, speaker_name, start_s, end_s, text}]
    summary: Dict[str, Any]                # summary, key_points, open_questions, pbc_requests, bookmarks
    extracted_steps: List[Dict[str, Any]]  # ProcessStep objects
    extracted_risks: List[Dict[str, Any]]  # Risk objects
    extracted_controls: List[Dict[str, Any]] # Control objects
    change_set: List[Dict[str, Any]]       # ChangeItem objects
    review_decisions: Dict[str, Any]       # from human review interrupt
    document_extract: Dict[str, Any]       # doc metadata, chunks, extracted items
    reconciliation: List[Dict[str, Any]]   # ReconItem objects
    deliverables: Dict[str, Any]           # dot, rcm rows, program rows, file paths
    test_request: Dict[str, Any]
    test_result: Dict[str, Any]
    process_mining: Dict[str, Any]
    sod_conflicts: List[Dict[str, Any]]
    active_recurring_tests: List[Dict[str, Any]]
    monitoring_status: str
    findings: List[Dict[str, Any]]
    qa_review: Dict[str, Any]
    prep_package: Dict[str, Any]
    copilot_hints: List[Dict[str, Any]]
    doc_qa_result: Dict[str, Any]
    evidence_evaluation: Dict[str, Any]
    knowledge_insights: Dict[str, Any]
    messages: List[Dict[str, Any]]         # for Ask FieldAI / co-pilot
    errors: List[str]
