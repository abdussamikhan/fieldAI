import os
import hashlib
import time
import re
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
from core.config import config
from core.db import db
from core.audit_log import log_audit

CATEGORIES = [
    "recordings",
    "source_documents",
    "generated_documents",
    "question_packs"
]

def get_storage_root() -> Path:
    """Returns the root directory for centralized data storage and ensures required folders exist."""
    root = Path(config.STORAGE_DIR).resolve()
    root.mkdir(parents=True, exist_ok=True)
    for cat in CATEGORIES:
        (root / cat).mkdir(parents=True, exist_ok=True)
    return root

def ensure_files_columns():
    """Defensively ensures process_id, category, and storage_path columns exist in files table."""
    conn = db.get_connection()
    try:
        cur = conn.cursor()
        cols_to_add = [
            ("process_id", "INTEGER"),
            ("category", "VARCHAR(100) DEFAULT 'general'"),
            ("storage_path", "VARCHAR(500)")
        ]
        for col_name, col_type in cols_to_add:
            try:
                if db.is_pg:
                    cur.execute(f"ALTER TABLE files ADD COLUMN IF NOT EXISTS {col_name} {col_type};")
                else:
                    cur.execute(f"ALTER TABLE files ADD COLUMN {col_name} {col_type};")
            except Exception:
                pass # Column already exists
        conn.commit()
        cur.close()
    except Exception as e:
        print(f"[Storage] ensure_files_columns error: {e}")
    finally:
        db.release_connection(conn)

def compute_sha256(data: bytes) -> str:
    """Computes SHA-256 hash for tamper-evident audit evidence verification."""
    return hashlib.sha256(data).hexdigest()

def clean_filename(filename: str) -> str:
    """Sanitizes filename for safe cross-platform filesystem storage."""
    base = os.path.basename(filename)
    safe = re.sub(r'[^a-zA-Z0-9_\-\.]', '_', base)
    return safe or "unnamed_file"

def save_file(
    filename: str,
    mime_type: str,
    data: bytes,
    category: str = "general",
    process_id: Optional[int] = None,
    created_by: Optional[int] = None
) -> int:
    """
    Saves a binary file to BOTH the centralized data storage folder and the database files table.
    
    Folder structure:
      <STORAGE_DIR>/<category>/process_<id>/<timestamp>_<filename>
    """
    ensure_files_columns()
    root = get_storage_root()
    cat_folder = root / (category if category in CATEGORIES else "general")
    
    proc_folder = cat_folder / (f"process_{process_id}" if process_id else "general")
    proc_folder.mkdir(parents=True, exist_ok=True)

    timestamp_prefix = time.strftime("%Y%m%d_%H%M%S")
    safe_name = f"{timestamp_prefix}_{clean_filename(filename)}"
    dest_path = proc_folder / safe_name

    sha256_hash = compute_sha256(data)
    size_bytes = len(data)

    # Deduplicate: if an identical file for this process, filename, and content already exists on disk, reuse it
    existing = db.fetch_one(
        """
        SELECT id, storage_path FROM files 
        WHERE filename = %s AND category = %s AND (process_id = %s OR (process_id IS NULL AND %s IS NULL)) AND sha256 = %s
        ORDER BY id DESC;
        """,
        (filename, category, process_id, process_id, sha256_hash)
    )
    if existing and existing.get("storage_path"):
        if (root / existing["storage_path"]).exists():
            return existing["id"]

    # Write file to centralized filesystem storage
    with open(dest_path, "wb") as f:
        f.write(data)

    rel_path = str(dest_path.relative_to(root))

    # Record in database registry
    file_id = db.execute_insert(
        """
        INSERT INTO files (process_id, category, filename, storage_path, mime_type, size_bytes, data, sha256, created_by)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);
        """,
        (process_id, category, filename, rel_path, mime_type, size_bytes, data, sha256_hash, created_by)
    )

    log_audit(
        user_id=created_by or 1,
        action="save_file",
        entity="files",
        entity_id=file_id,
        details={
            "filename": filename,
            "category": category,
            "process_id": process_id,
            "storage_path": rel_path,
            "size_bytes": size_bytes,
            "sha256": sha256_hash
        }
    )

    return file_id

def save_generated_document(
    filename: str,
    mime_type: str,
    data: bytes,
    process_id: Optional[int] = None,
    created_by: Optional[int] = None
) -> int:
    """Helper to save generated deliverables and audit reports to centralized storage."""
    return save_file(
        filename=filename,
        mime_type=mime_type,
        data=data,
        category="generated_documents",
        process_id=process_id,
        created_by=created_by
    )

def get_file(file_id: int) -> Optional[Dict[str, Any]]:
    """Retrieves file metadata and binary content by file_id from disk or database."""
    ensure_files_columns()
    row = db.fetch_one(
        """
        SELECT f.id, f.process_id, f.category, f.filename, f.storage_path, f.mime_type,
               f.size_bytes, f.data, f.sha256, f.created_at, u.username as creator_name
        FROM files f
        LEFT JOIN users u ON f.created_by = u.id
        WHERE f.id = %s;
        """,
        (file_id,)
    )
    if not row:
        return None

    # Prefer reading from centralized storage folder on disk
    if row.get("storage_path"):
        full_path = get_storage_root() / row["storage_path"]
        if full_path.exists():
            try:
                with open(full_path, "rb") as f:
                    row["data"] = f.read()
            except Exception as e:
                print(f"[Storage] Could not read from disk {full_path}: {e}")

    return row

def list_storage_files(
    category: Optional[str] = None,
    process_id: Optional[int] = None
) -> List[Dict[str, Any]]:
    """Lists files stored in centralized data storage with process association and disk status."""
    ensure_files_columns()
    query = """
    SELECT f.id, f.process_id, f.category, f.filename, f.storage_path, f.mime_type,
           f.size_bytes, f.sha256, f.created_at, p.name as process_name, u.username as creator_name
    FROM files f
    LEFT JOIN processes p ON f.process_id = p.id
    LEFT JOIN users u ON f.created_by = u.id
    WHERE 1=1
    """
    params = []
    if category and category != "all":
        query += " AND f.category = %s"
        params.append(category)
    if process_id:
        query += " AND f.process_id = %s"
        params.append(process_id)

    query += " ORDER BY f.id DESC;"
    rows = db.fetch_all(query, tuple(params))

    root = get_storage_root()
    for r in rows:
        if r.get("storage_path"):
            full_path = root / r["storage_path"]
            r["disk_exists"] = full_path.exists()
            r["full_disk_path"] = str(full_path)
        else:
            r["disk_exists"] = False
            r["full_disk_path"] = "DB Blob only"

    return rows

def get_storage_stats() -> Dict[str, Any]:
    """Calculates storage folder usage statistics across categories."""
    root = get_storage_root()
    total_bytes = 0
    cat_counts = {cat: 0 for cat in CATEGORIES}
    cat_bytes = {cat: 0 for cat in CATEGORIES}

    # Count from disk
    for cat in CATEGORIES:
        cat_dir = root / cat
        if cat_dir.exists():
            for p in cat_dir.rglob("*"):
                if p.is_file():
                    size = p.stat().st_size
                    total_bytes += size
                    cat_counts[cat] += 1
                    cat_bytes[cat] += size

    # Also count from DB
    ensure_files_columns()
    db_total = db.fetch_one("SELECT COUNT(*) as c, COALESCE(SUM(size_bytes), 0) as s FROM files;")

    return {
        "root_path": str(root),
        "total_files": sum(cat_counts.values()),
        "total_bytes": total_bytes,
        "total_mb": round(total_bytes / (1024 * 1024), 2),
        "category_counts": cat_counts,
        "category_bytes": cat_bytes,
        "db_record_count": db_total["c"] if db_total else 0
    }

def delete_file(file_id: int) -> bool:
    """Deletes a file from both the centralized storage folder and database."""
    ensure_files_columns()
    row = db.fetch_one("SELECT storage_path FROM files WHERE id = %s;", (file_id,))
    if row and row.get("storage_path"):
        full_path = get_storage_root() / row["storage_path"]
        if full_path.exists():
            try:
                full_path.unlink()
            except Exception as e:
                print(f"[Storage] Could not unlink {full_path}: {e}")

    count = db.execute("DELETE FROM files WHERE id = %s;", (file_id,))
    return count > 0
