import hashlib
from typing import Optional, Dict, Any
from core.db import db

def compute_sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def save_file(filename: str, mime_type: str, data: bytes, created_by: Optional[int] = None) -> int:
    """Saves a binary file to the database files table."""
    sha256_hash = compute_sha256(data)
    size_bytes = len(data)
    
    file_id = db.execute_insert(
        """
        INSERT INTO files (filename, mime_type, size_bytes, data, sha256, created_by)
        VALUES (%s, %s, %s, %s, %s, %s);
        """,
        (filename, mime_type, size_bytes, data, sha256_hash, created_by)
    )
    return file_id

def get_file(file_id: int) -> Optional[Dict[str, Any]]:
    """Retrieves file metadata and binary content by file_id."""
    return db.fetch_one(
        "SELECT id, filename, mime_type, size_bytes, data, sha256, created_at FROM files WHERE id = %s;",
        (file_id,)
    )

def delete_file(file_id: int) -> bool:
    """Deletes a file by file_id."""
    count = db.execute("DELETE FROM files WHERE id = %s;", (file_id,))
    return count > 0
