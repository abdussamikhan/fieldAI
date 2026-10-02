from typing import Optional, Dict, Any
import bcrypt
from core.db import db

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception:
        return False

def hash_password(plain_password: str) -> str:
    return bcrypt.hashpw(plain_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

def authenticate_user(username: str, password: str) -> Optional[Dict[str, Any]]:
    user = db.fetch_one("SELECT * FROM users WHERE username = %s AND active = TRUE;", (username,))
    if not user:
        return None
    if verify_password(password, user["password_hash"]):
        return {
            "id": user["id"],
            "username": user["username"],
            "role": user["role"]
        }
    return None

def create_user(username: str, password: str, role: str = "Auditor") -> int:
    pw_hash = hash_password(password)
    return db.execute_insert(
        "INSERT INTO users (username, password_hash, role, active) VALUES (%s, %s, %s, TRUE);",
        (username, pw_hash, role)
    )

def check_permission(user_role: str, required_role: str) -> bool:
    role_hierarchy = {
        "Auditee": 1,
        "Auditor": 2,
        "Manager": 3,
        "Admin": 4
    }
    return role_hierarchy.get(user_role, 0) >= role_hierarchy.get(required_role, 99)
