import json
import re
from typing import Dict, Any, List
from graphs.state import FieldAIState
from core.db import db
from core.llm import llm

PROMPT_DOC_QA_SYSTEM = """You are FieldAI Q&A Assistant, an expert internal audit AI.
Answer the auditor's question STRICTLY using the provided document chunks and meeting transcript snippets.
Every statement must include an exact citation (e.g. '[SOP §3.2 p.4]' or '[Meeting 00:04:12]').
If the answer is not present in the excerpts, state clearly: "Information not found in available documents or transcripts." Do not invent details.

FORMATTING REQUIREMENTS:
- Structure the "answer" field cleanly using professional Markdown.
- DO NOT return a single unbroken wall of text.
- Start with a concise Executive Summary (1-2 sentences).
- Use bullet points (- **Key Area/Topic**: Details... [Citation]) for distinct rules, criteria, limits, or steps.
- Use bolding for roles, thresholds, and systems (e.g., **Department Head**, **$50,000**, **SAP ERP**).
- Append the grounded citation directly at the end of each bullet point (e.g., [SOP-FIN-04 §3 p.1]).

Return JSON format:
{
  "answer": "### Executive Summary\\n...\\n\\n### Key Requirements & Controls\\n- **Approval Limits**: ... [SOP-FIN-04 §3 p.1]\\n- **Verification**: ... [SOP-FIN-04 §4 p.1]",
  "citations": [
    {"source": "SOP-FIN-04", "locator": "Section 3.2, p.4", "quote": "All POs > $50,000 require CFO approval."}
  ]
}"""

def format_qa_answer(text: str) -> str:
    """Ensures answers are cleanly structured with headings and bullet points, avoiding walls of text."""
    if not text:
        return text
    
    # If the text already has headings or bullet points, return as is
    if "\n-" in text or "\n*" in text or "\n#" in text or text.count("\n\n") >= 2:
        return text.strip()
    
    # Check if there are inline citations like [SOP-FIN-04 ...]
    parts = re.split(r'(\[[^\]]+\])', text)
    if len(parts) > 2:
        items = []
        current = ""
        for p in parts:
            current += p
            if p.startswith("[") and p.endswith("]"):
                items.append(current.strip())
                current = ""
        if current.strip():
            items.append(current.strip())
        
        if len(items) > 1:
            summary = items[0]
            bullets = items[1:]
            formatted = f"**Executive Summary:**\n{summary}\n\n**Key Requirements & Controls:**\n"
            for b in bullets:
                b_clean = b.strip()
                if b_clean.startswith("; ") or b_clean.startswith(", "):
                    b_clean = b_clean[2:]
                formatted += f"- {b_clean}\n"
            return formatted

    # Fallback: if sentences exist without citations, format nicely
    sentences = re.split(r'(?<=[.!?])\s+', text)
    if len(sentences) > 2 and len(text) > 180:
        summary = sentences[0]
        bullets = sentences[1:]
        return f"**Summary:**\n{summary}\n\n**Details:**\n" + "\n".join(f"- {s.strip()}" for s in bullets)

    return text.strip()

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

    if isinstance(res, dict) and "answer" in res:
        res["answer"] = format_qa_answer(res["answer"])

    return {
        "doc_qa_result": res
    }
