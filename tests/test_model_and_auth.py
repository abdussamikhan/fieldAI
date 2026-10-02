import pytest
from core.db import db
from core.auth import authenticate_user, check_permission, hash_password, verify_password
from core.model_repo import get_next_code, get_process_master_model, create_version_snapshot

def setup_module():
    db.init_db()

def test_auth_verification():
    pw = "secretAudit123"
    h = hash_password(pw)
    assert verify_password(pw, h) is True
    assert verify_password("wrongpw", h) is False

def test_role_hierarchy():
    assert check_permission("Admin", "Auditor") is True
    assert check_permission("Manager", "Auditor") is True
    assert check_permission("Auditor", "Manager") is False
    assert check_permission("Auditee", "Auditor") is False

def test_code_allocation():
    c_step = get_next_code(1, "step")
    assert c_step.startswith("P2P-")
    c_risk = get_next_code(1, "risk")
    assert c_risk.startswith("R-")
    c_ctrl = get_next_code(1, "control")
    assert c_ctrl.startswith("C-")

def test_version_snapshot():
    v_id = create_version_snapshot(1, "v1.0", "Initial baseline walkthrough approval")
    assert v_id > 0
    row = db.fetch_one("SELECT * FROM versions WHERE id = %s;", (v_id,))
    assert row["version_label"] == "v1.0"
    assert row["locked"] == 1 or row["locked"] is True
