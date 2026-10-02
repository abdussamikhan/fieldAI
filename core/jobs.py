import json
from datetime import datetime
from typing import Optional, Dict, Any, List
from core.db import db

def enqueue_job(
    job_type: str,
    payload: Dict[str, Any],
    thread_id: Optional[str] = None,
    created_by: Optional[int] = None
) -> int:
    """Queues a new background task."""
    payload_str = json.dumps(payload, ensure_ascii=False, default=str)
    return db.execute_insert(
        """
        INSERT INTO jobs (job_type, payload_json, status, progress, message, thread_id, created_by)
        VALUES (%s, %s, 'queued', 0, 'Job queued', %s, %s);
        """,
        (job_type, payload_str, thread_id, created_by)
    )

def get_job(job_id: int) -> Optional[Dict[str, Any]]:
    """Gets job status and progress by ID."""
    row = db.fetch_one("SELECT * FROM jobs WHERE id = %s;", (job_id,))
    if row and row.get("payload_json"):
        try:
            row["payload"] = json.loads(row["payload_json"])
        except Exception:
            row["payload"] = {}
    return row

def update_job(
    job_id: int,
    status: str,
    progress: int,
    message: Optional[str] = None
) -> None:
    """Updates job progress, status, and completion timestamp."""
    extra = ""
    params = [status, progress, message]
    if status == 'running':
        extra = ", started_at = COALESCE(started_at, CURRENT_TIMESTAMP)"
    elif status in ('done', 'failed', 'waiting_review'):
        extra = ", finished_at = CURRENT_TIMESTAMP"
    
    params.append(job_id)
    db.execute(
        f"""
        UPDATE jobs 
        SET status = %s, progress = %s, message = %s {extra}
        WHERE id = %s;
        """,
        tuple(params)
    )

def claim_next_job() -> Optional[Dict[str, Any]]:
    """Claims the oldest queued job atomically."""
    # Find next queued job
    job = db.fetch_one(
        "SELECT * FROM jobs WHERE status = 'queued' ORDER BY id ASC LIMIT 1;"
    )
    if not job:
        return None
    
    # Try updating to running
    updated = db.execute(
        "UPDATE jobs SET status = 'running', started_at = CURRENT_TIMESTAMP, message = 'Processing...' WHERE id = %s AND status = 'queued';",
        (job["id"],)
    )
    if updated > 0:
        return get_job(job["id"])
    return None

def list_jobs(limit: int = 50) -> List[Dict[str, Any]]:
    """Lists recent jobs."""
    return db.fetch_all("SELECT * FROM jobs ORDER BY id DESC LIMIT %s;", (limit,))
