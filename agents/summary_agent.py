from typing import Dict, Any, List
from graphs.state import FieldAIState
from core.db import db
from core.llm import llm
from core.schemas import MeetingSummary
from core.audit_log import log_audit

PROMPT_SUMMARY_SYSTEM = """You are FieldAI, an expert internal auditor analyzing a meeting walkthrough transcript.
Generate a concise summary (200 words or less), key audit discussion points, open follow-up questions for management, and requested PBC (Provided By Client) evidence items.
Your output must be JSON matching this format:
{
  "summary": "Concise summary...",
  "key_points": ["point 1", "point 2"],
  "open_questions": ["question 1", "question 2"],
  "pbc_requests": [
    {"item": "Document / extract name", "owner": "Role / Person", "due_hint": "Due date / timing", "timestamp": "00:04:12"}
  ],
  "bookmarks": [
    {"timestamp": "00:02:15", "topic": "Key topic discussed"}
  ]
}"""

def run(state: FieldAIState) -> Dict[str, Any]:
    """
    Summary Agent (FR-1.10):
    Produces executive summary, open items, PBC evidence requests, and timestamps.
    """
    transcript = state.get("transcript", [])
    source_id = state.get("source_id")
    process_id = state.get("process_id")

    if not transcript and source_id:
        transcript = db.fetch_all(
            "SELECT speaker_label, speaker_name, start_s, end_s, text FROM transcript_segments WHERE source_id = %s ORDER BY start_s ASC;",
            (source_id,)
        )

    # Format transcript text
    transcript_text = ""
    for seg in transcript:
        spk = seg.get("speaker_name") or seg.get("speaker_label", "Speaker")
        transcript_text += f"[{int(seg.get('start_s', 0))}s] {spk}: {seg.get('text', '')}\n"

    user_prompt = f"Analyze the following internal audit walkthrough transcript:\n\n{transcript_text[:12000]}"
    
    summary_data = llm.generate_json(
        prompt=user_prompt,
        system_prompt=PROMPT_SUMMARY_SYSTEM,
        schema=MeetingSummary
    )

    # Save open questions into database open_items
    if process_id and summary_data.get("open_questions"):
        for q in summary_data["open_questions"]:
            db.execute_insert(
                """
                INSERT INTO open_items (process_id, question, origin, status, raised_in_source)
                VALUES (%s, %s, 'Meeting Walkthrough', 'open', %s);
                """,
                (process_id, q, source_id)
            )

    # Save PBC requests into database pbc_requests
    if process_id and summary_data.get("pbc_requests"):
        for pbc in summary_data["pbc_requests"]:
            db.execute_insert(
                """
                INSERT INTO pbc_requests (process_id, item, owner, due_date, status)
                VALUES (%s, %s, %s, %s, 'requested');
                """,
                (process_id, pbc.get("item", ""), pbc.get("owner", ""), pbc.get("due_hint", ""))
            )

    log_audit(state.get("user_id"), "generate_summary", "source", source_id, {"pbc_count": len(summary_data.get("pbc_requests", []))})

    return {"summary": summary_data}
