import json
from typing import Dict, Any, List, Optional
from core.db import db
from core.audit_log import log_audit

def ensure_question_packs_table():
    """Defensively ensures the question_packs table exists in the active database."""
    query = """
    CREATE TABLE IF NOT EXISTS question_packs (
        id SERIAL PRIMARY KEY,
        process_id INTEGER NOT NULL REFERENCES processes(id) ON DELETE CASCADE,
        title VARCHAR(255) NOT NULL,
        scoping_json TEXT,
        questions_json TEXT NOT NULL,
        version VARCHAR(50) DEFAULT 'v1.0',
        created_by INTEGER REFERENCES users(id),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    try:
        db.execute(query)
    except Exception as e:
        print(f"[PrepRepo] Table ensure error: {e}")

def save_question_pack(
    process_id: int,
    title: str,
    scoping: Dict[str, Any],
    questions: List[Dict[str, Any]],
    version: str = "v1.0",
    user_id: Optional[int] = None
) -> int:
    """Saves a generated question pack and scoping recommendation to the database."""
    ensure_question_packs_table()
    scoping_str = json.dumps(scoping or {}, ensure_ascii=False, default=str)
    questions_str = json.dumps(questions or [], ensure_ascii=False, default=str)

    pack_id = db.execute_insert(
        """
        INSERT INTO question_packs (process_id, title, scoping_json, questions_json, version, created_by)
        VALUES (%s, %s, %s, %s, %s, %s);
        """,
        (process_id, title, scoping_str, questions_str, version, user_id)
    )

    log_audit(
        user_id=user_id or 1,
        action="save_question_pack",
        entity="question_packs",
        entity_id=pack_id,
        details={
            "process_id": process_id,
            "title": title,
            "version": version,
            "question_count": len(questions)
        }
    )

    # Archive physical copy into centralized data storage folder
    try:
        from core.storage import save_file
        pack_payload = {
            "pack_id": pack_id,
            "title": title,
            "version": version,
            "process_id": process_id,
            "scoping": scoping,
            "question_pack": questions
        }
        pack_bytes = json.dumps(pack_payload, indent=2, ensure_ascii=False, default=str).encode("utf-8")
        save_file(
            filename=f"question_pack_p{process_id}_{version}.json",
            mime_type="application/json",
            data=pack_bytes,
            category="question_packs",
            process_id=process_id,
            created_by=user_id
        )
    except Exception as e:
        print(f"[PrepRepo] Storage archive error: {e}")

    return pack_id

def list_question_packs(process_id: int) -> List[Dict[str, Any]]:
    """Retrieves all saved question packs for a process from centralized database storage."""
    ensure_question_packs_table()
    rows = db.fetch_all(
        """
        SELECT qp.id, qp.process_id, qp.title, qp.scoping_json, qp.questions_json,
               qp.version, qp.created_by, qp.created_at, u.username as creator_name
        FROM question_packs qp
        LEFT JOIN users u ON qp.created_by = u.id
        WHERE qp.process_id = %s
        ORDER BY qp.id DESC;
        """,
        (process_id,)
    )

    for r in rows:
        try:
            r["scoping"] = json.loads(r["scoping_json"]) if r.get("scoping_json") else {}
        except Exception:
            r["scoping"] = {}
        try:
            r["questions"] = json.loads(r["questions_json"]) if r.get("questions_json") else []
        except Exception:
            r["questions"] = []
    return rows

def get_question_pack(pack_id: int) -> Optional[Dict[str, Any]]:
    """Retrieves a single question pack by ID."""
    ensure_question_packs_table()
    r = db.fetch_one(
        """
        SELECT qp.id, qp.process_id, qp.title, qp.scoping_json, qp.questions_json,
               qp.version, qp.created_by, qp.created_at, u.username as creator_name
        FROM question_packs qp
        LEFT JOIN users u ON qp.created_by = u.id
        WHERE qp.id = %s;
        """,
        (pack_id,)
    )
    if not r:
        return None
    try:
        r["scoping"] = json.loads(r["scoping_json"]) if r.get("scoping_json") else {}
    except Exception:
        r["scoping"] = {}
    try:
        r["questions"] = json.loads(r["questions_json"]) if r.get("questions_json") else []
    except Exception:
        r["questions"] = []
    return r

def delete_question_pack(pack_id: int, user_id: Optional[int] = None) -> bool:
    """Deletes a question pack from database storage."""
    ensure_question_packs_table()
    count = db.execute("DELETE FROM question_packs WHERE id = %s;", (pack_id,))
    if count > 0:
        log_audit(
            user_id=user_id or 1,
            action="delete_question_pack",
            entity="question_packs",
            entity_id=pack_id,
            details={"pack_id": pack_id}
        )
        return True
    return False
