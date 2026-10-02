import json
from typing import Dict, Any, List
from graphs.state import FieldAIState
from core.db import db
from core.llm import llm

PROMPT_DOC_QA_SYSTEM = """You are FieldAI Q&A Assistant.
Answer the auditor's question STRICTLY using the provided document chunks and meeting transcript snippets.
Every statement must include an exact citation (e.g. '[SOP §3.2 p.4]' or '[Meeting 00:04:12]').
If the answer is not present in the excerpts, state clearly: "Information not found in available documents or transcripts." Do not invent details.

Return JSON format:
{
  "answer": "...",
  "citations": [
    {"source": "SOP-FIN-04", "locator": "Section 3.2, p.4", "quote": "All POs > $50,000 require CFO approval."}
  ]
}"""

def run(state: FieldAIState) -> Dict[str, Any]:
    """
    Doc Q&A Agent (FR-7.8):
    Keyword search and grounded question-answering with exact citations over documents and transcripts.
    """
    question = state.get("task_input") or "What are the approval thresholds for purchase orders?"
    process_id = state.get("process_id", 1)

    # Search doc_chunks
    search_term = f"%{question.split()[0]}%" if question.split() else "%approval%"
    chunks = db.fetch_all(
        """
        SELECT c.page, c.section, c.text, d.doc_type, s.title 
        FROM doc_chunks c
        JOIN documents d ON c.document_id = d.id
        JOIN sources s ON d.source_id = s.id
        WHERE s.process_id = %s
        LIMIT 5;
        """,
        (process_id,)
    )

    # Search transcript segments
    transcripts = db.fetch_all(
        """
        SELECT speaker_label, speaker_name, start_s, text 
        FROM transcript_segments ts
        JOIN sources s ON ts.source_id = s.id
        WHERE s.process_id = %s
        LIMIT 5;
        """,
        (process_id,)
    )

    evidence_context = []
    for c in chunks:
        evidence_context.append(f"Document [{c.get('title', 'SOP')} §{c.get('section', '')} p.{c.get('page', 1)}]: {c.get('text', '')}")

    for t in transcripts:
        spk = t.get("speaker_name") or t.get("speaker_label", "Speaker")
        min_t = int(t.get("start_s", 0) // 60)
        sec_t = int(t.get("start_s", 0) % 60)
        evidence_context.append(f"Meeting [{min_t:02d}:{sec_t:02d}] {spk}: {t.get('text', '')}")

    user_prompt = f"Question: {question}\n\nEvidence Context:\n" + "\n---\n".join(evidence_context[:8])

    res = llm.generate_json(
        prompt=user_prompt,
        system_prompt=PROMPT_DOC_QA_SYSTEM
    )

    return {
        "doc_qa_result": res
    }
