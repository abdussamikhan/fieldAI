import json
from typing import Optional, Dict, Any, List
from core.db import db

def log_audit(
    user_id: Optional[int],
    action: str,
    entity: str,
    entity_id: Optional[int] = None,
    details: Optional[Dict[str, Any]] = None
) -> int:
    """Writes an append-only audit trail record."""
    details_str = json.dumps(details or {}, ensure_ascii=False)
    return db.execute_insert(
        """
        INSERT INTO audit_log (user_id, action, entity, entity_id, details_json)
        VALUES (%s, %s, %s, %s, %s);
        """,
        (user_id, action, entity, entity_id, details_str)
    )

def get_audit_logs(limit: int = 100, entity: Optional[str] = None) -> List[Dict[str, Any]]:
    """Retrieves recent audit log events."""
    if entity:
        return db.fetch_all(
            """
            SELECT a.*, u.username 
            FROM audit_log a 
            LEFT JOIN users u ON a.user_id = u.id 
            WHERE a.entity = %s 
            ORDER BY a.created_at DESC 
            LIMIT %s;
            """,
            (entity, limit)
        )
    return db.fetch_all(
        """
        SELECT a.*, u.username 
        FROM audit_log a 
        LEFT JOIN users u ON a.user_id = u.id 
        ORDER BY a.created_at DESC 
        LIMIT %s;
        """,
        (limit,)
    )
