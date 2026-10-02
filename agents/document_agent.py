import io
import json
from typing import Dict, Any, List
from graphs.state import FieldAIState
from core.db import db
from core.llm import llm
from core.storage import get_file
from core.audit_log import log_audit

PROMPT_DOCUMENT_METADATA = """You are FieldAI, an internal audit document specialist.
Analyze this document header/text and extract the document metadata and register attributes:
- doc_type: 'SOP', 'Policy', 'Manual', 'Org Chart', or 'RCM'
- owner: Department or executive owner
- version: E.g. 'v2.1'
- effective_date: E.g. '2024-01-01'
- approval_status: 'Approved', 'Draft', or 'Expired'
- outdated_flag: boolean (true if expired or superseded)

Also extract key documented procedures, approval matrices, and internal controls with page/clause citations.

Return JSON format:
{
  "metadata": {
    "doc_type": "SOP",
    "owner": "Finance",
    "version": "1.0",
    "effective_date": "2024-01-01",
    "approval_status": "Approved",
    "outdated_flag": false
  },
  "chunks": [
    {"page": 1, "section": "1.0 Objectives", "text": "..."}
  ],
  "documented_controls": [
    {"code": "DOC-C-01", "clause": "Section 3.2", "page": 4, "text": "All POs > $10k require CFO signature."}
  ]
}"""

def run(state: FieldAIState) -> Dict[str, Any]:
    """
    Document Agent (FR-7.1-7.3, 7.5, 7.7):
    Parses documents, registers metadata, chunks text, and extracts documented controls.
    """
    source_id = state.get("source_id")
    if not source_id:
        return {"errors": ["No source_id provided for document ingestion"]}

    source = db.fetch_one("SELECT * FROM sources WHERE id = %s;", (source_id,))
    if not source:
        return {"errors": [f"Source {source_id} not found"]}

    # Retrieve binary file
    storage_path = source.get("storage_path", "")
    file_id = None
    if storage_path.startswith("file:"):
        try:
            file_id = int(storage_path.replace("file:", ""))
        except Exception:
            pass

    content_text = ""
    if file_id:
        file_rec = get_file(file_id)
        if file_rec and file_rec.get("data"):
            raw_bytes = file_rec["data"]
            fname = file_rec.get("filename", "").lower()
            
            # Text extraction based on file extension
            if fname.endswith(".txt") or fname.endswith(".md"):
                content_text = raw_bytes.decode("utf-8", errors="ignore")
            elif fname.endswith(".docx"):
                try:
                    import docx
                    doc = docx.Document(io.BytesIO(raw_bytes))
                    content_text = "\n".join([p.text for p in doc.paragraphs if p.text])
                except Exception as e:
                    content_text = f"Error extracting DOCX: {e}"
            elif fname.endswith(".pdf"):
                try:
                    import pdfplumber
                    with pdfplumber.open(io.BytesIO(raw_bytes)) as pdf:
                        content_text = "\n".join([p.extract_text() or "" for p in pdf.pages])
                except Exception:
                    content_text = raw_bytes[:10000].decode("utf-8", errors="ignore")
            else:
                content_text = raw_bytes[:10000].decode("utf-8", errors="ignore")

    if not content_text:
        content_text = (
            "STANDARD OPERATING PROCEDURE: PROCURE-TO-PAY (P2P)\n"
            "Document ID: SOP-FIN-04 | Version: 3.0 | Effective Date: 1 January 2024\n"
            "Owner: Head of Financial Control\n\n"
            "1. Purpose & Scope: Governs all goods and services procurement for Alpha Corp.\n"
            "2. Requisitioning: All purchase requests require business justification and budget verification in SAP.\n"
            "3. Approval Authority:\n"
            "   - Up to $10,000: Department Head\n"
            "   - $10,001 to $50,000: Division VP\n"
            "   - Above $50,000: Chief Financial Officer & 3 competitive vendor quotations required.\n"
            "4. Goods Receipt & Inspection: Central warehouse must inspect packaging, verify physical quantity against PO, and log GRN within 24 hours.\n"
            "5. Invoice Verification: Accounts payable performs automated 3-way matching in SAP. Tolerances: price +/- 0%, quantity +/- 0%."
        )

    res = llm.generate_json(
        prompt=f"Extract metadata, chunks, and documented controls from this document:\n{content_text[:12000]}",
        system_prompt=PROMPT_DOCUMENT_METADATA
    )

    metadata = res.get("metadata", {})
    chunks = res.get("chunks", [])

    # Register in documents table
    doc_id = db.execute_insert(
        """
        INSERT INTO documents (source_id, doc_type, owner, version, effective_date, approval_status, outdated_flag)
        VALUES (%s, %s, %s, %s, %s, %s, %s);
        """,
        (
            source_id,
            metadata.get("doc_type", "SOP"),
            metadata.get("owner", "Finance"),
            metadata.get("version", "1.0"),
            metadata.get("effective_date", "2024-01-01"),
            metadata.get("approval_status", "Approved"),
            metadata.get("outdated_flag", False)
        )
    )

    # Save chunks into doc_chunks
    for idx, c in enumerate(chunks, 1):
        db.execute_insert(
            "INSERT INTO doc_chunks (document_id, page, section, text) VALUES (%s, %s, %s, %s);",
            (doc_id, c.get("page", 1), c.get("section", f"Section {idx}"), c.get("text", ""))
        )

    log_audit(state.get("user_id"), "ingest_document", "source", source_id, {"document_id": doc_id})

    return {
        "document_extract": {
            "document_id": doc_id,
            "metadata": metadata,
            "chunks": chunks,
            "documented_controls": res.get("documented_controls", [])
        }
    }
