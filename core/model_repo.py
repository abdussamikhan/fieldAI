import json
from typing import List, Dict, Any, Optional
from core.db import db
from core.audit_log import log_audit

def get_process(process_id: int) -> Optional[Dict[str, Any]]:
    return db.fetch_one("SELECT * FROM processes WHERE id = %s;", (process_id,))

def list_engagements() -> List[Dict[str, Any]]:
    """Returns all audit engagements ordered by ID."""
    return db.fetch_all("SELECT * FROM engagements ORDER BY id ASC;")

def get_next_code(process_id: int, entity_type: str, prefix: str = "") -> str:
    """
    Allocates next sequential code per process and type without renumbering (BRD FR-6.2).
    E.g., P2P-01, R-01, C-01, T-01.
    """
    proc = get_process(process_id)
    code_prefix = proc.get("code_prefix", "P2P") if proc else "P2P"

    if entity_type == "step":
        res = db.fetch_all("SELECT step_code FROM steps WHERE process_id = %s;", (process_id,))
        count = len(res) + 1
        return f"{code_prefix}-{count:02d}"
    elif entity_type == "risk":
        res = db.fetch_all("SELECT risk_code FROM risks WHERE process_id = %s;", (process_id,))
        count = len(res) + 1
        return f"R-{count:02d}"
    elif entity_type == "control":
        res = db.fetch_all("SELECT control_code FROM controls WHERE process_id = %s;", (process_id,))
        count = len(res) + 1
        return f"C-{count:02d}"
    elif entity_type == "test":
        res = db.fetch_all("SELECT test_code FROM tests WHERE process_id = %s;", (process_id,))
        count = len(res) + 1
        return f"T-{count:02d}"
    return f"{prefix}-{1:02d}"

def get_active_steps(process_id: int) -> List[Dict[str, Any]]:
    return db.fetch_all(
        "SELECT * FROM steps WHERE process_id = %s AND status = 'active' ORDER BY order_num ASC;",
        (process_id,)
    )

def get_active_risks(process_id: int) -> List[Dict[str, Any]]:
    return db.fetch_all(
        "SELECT * FROM risks WHERE process_id = %s AND status = 'active' ORDER BY id ASC;",
        (process_id,)
    )

def get_active_controls(process_id: int) -> List[Dict[str, Any]]:
    return db.fetch_all(
        "SELECT * FROM controls WHERE process_id = %s AND status = 'active' ORDER BY id ASC;",
        (process_id,)
    )

def get_process_master_model(process_id: int) -> Dict[str, Any]:
    """Returns the complete linked master model for a process."""
    steps = get_active_steps(process_id)
    risks = get_active_risks(process_id)
    controls = get_active_controls(process_id)
    
    # Fetch risk-control links
    rc_links = db.fetch_all(
        """
        SELECT r.risk_code, c.control_code 
        FROM risk_control_links l
        JOIN risks r ON l.risk_id = r.id
        JOIN controls c ON l.control_id = c.id
        WHERE r.process_id = %s;
        """,
        (process_id,)
    )
    
    # Map links
    for r in risks:
        r["control_codes"] = [link["control_code"] for link in rc_links if link["risk_code"] == r["risk_code"]]
    for c in controls:
        c["risk_codes"] = [link["risk_code"] for link in rc_links if link["control_code"] == c["control_code"]]

    return {
        "process_id": process_id,
        "steps": steps,
        "risks": risks,
        "controls": controls
    }

def create_version_snapshot(
    process_id: int,
    version_label: str,
    change_log: str,
    approved_by: Optional[int] = None
) -> int:
    """Takes an immutable JSON snapshot of the current master model."""
    model = get_process_master_model(process_id)
    snapshot_json = json.dumps(model, ensure_ascii=False, default=str)
    
    version_id = db.execute_insert(
        """
        INSERT INTO versions (process_id, version_label, snapshot_json, change_log, approved_by, approved_at, locked)
        VALUES (%s, %s, %s, %s, %s, CURRENT_TIMESTAMP, TRUE);
        """,
        (process_id, version_label, snapshot_json, change_log, approved_by)
    )
    # Update current_version on process
    db.execute(
        "UPDATE processes SET current_version = %s WHERE id = %s;",
        (version_label, process_id)
    )
    log_audit(approved_by, "create_version", "process", process_id, {"version": version_label})
    return version_id

def apply_change_set(change_set_id: int, user_id: Optional[int] = None) -> str:
    """
    Applies accepted change items to master model and increments version label (e.g. v1.0 -> v1.1).
    """
    change_set = db.fetch_one("SELECT * FROM change_sets WHERE id = %s;", (change_set_id,))
    if not change_set:
        return ""
    
    process_id = change_set["process_id"]
    proc = get_process(process_id)
    curr_ver = proc.get("current_version", "v1.0")
    
    # Determine new version
    try:
        ver_num = float(curr_ver.replace("v", ""))
        new_ver = f"v{ver_num + 0.1:.1f}"
    except Exception:
        new_ver = "v1.1"

    items = db.fetch_all(
        "SELECT * FROM change_items WHERE change_set_id = %s AND decision = 'accepted';",
        (change_set_id,)
    )

    change_log_entries = []

    for item in items:
        entity = item["entity"]
        action = item["action"]
        after = json.loads(item["after_json"]) if item["after_json"] else {}
        target_code = item["target_code"]

        if action == "Added":
            if entity == "step":
                code = get_next_code(process_id, "step")
                db.execute_insert(
                    """
                    INSERT INTO steps (process_id, step_code, order_num, description, responsible_role, department, system, inputs, outputs, frequency, is_decision, confidence, status)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'active');
                    """,
                    (
                        process_id, code, after.get("order", 1), after.get("description", ""),
                        after.get("responsible_role", ""), after.get("department", ""),
                        after.get("system", ""), after.get("inputs", ""), after.get("outputs", ""),
                        after.get("frequency", "per transaction"), after.get("is_decision", False),
                        after.get("confidence", 1.0)
                    )
                )
                change_log_entries.append(f"Added step {code}: {after.get('description', '')[:50]}")
            elif entity == "risk":
                code = get_next_code(process_id, "risk")
                db.execute_insert(
                    """
                    INSERT INTO risks (process_id, risk_code, description, inherent_rating, ai_suggested, library_ref, confidence, status)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, 'active');
                    """,
                    (
                        process_id, code, after.get("description", ""),
                        after.get("inherent_rating", "Medium"), after.get("ai_suggested", False),
                        after.get("library_ref"), after.get("confidence", 1.0)
                    )
                )
                change_log_entries.append(f"Added risk {code}: {after.get('description', '')[:50]}")
            elif entity == "control":
                code = get_next_code(process_id, "control")
                db.execute_insert(
                    """
                    INSERT INTO controls (process_id, control_code, description, control_type, nature, frequency, owner, key_control, design_rating, criteria_ref, ai_suggested, status)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'active');
                    """,
                    (
                        process_id, code, after.get("description", ""),
                        after.get("type", "preventive"), after.get("nature", "automated"),
                        after.get("frequency", "per transaction"), after.get("owner", ""),
                        after.get("key_control", True), after.get("design_rating", "Adequate"),
                        after.get("criteria_ref", ""), after.get("ai_suggested", False)
                    )
                )
                change_log_entries.append(f"Added control {code}: {after.get('description', '')[:50]}")

        elif action in ("Changed", "Contradicted"):
            note = item.get("resolution_note") or "Updated per walkthrough review"
            if entity == "step" and target_code:
                db.execute(
                    """
                    UPDATE steps SET description = %s, responsible_role = %s, department = %s, system = %s
                    WHERE process_id = %s AND step_code = %s;
                    """,
                    (after.get("description", ""), after.get("responsible_role", ""), after.get("department", ""), after.get("system", ""), process_id, target_code)
                )
                change_log_entries.append(f"Updated step {target_code} ({note})")
            elif entity == "control" and target_code:
                db.execute(
                    """
                    UPDATE controls SET description = %s, owner = %s, design_rating = %s
                    WHERE process_id = %s AND control_code = %s;
                    """,
                    (after.get("description", ""), after.get("owner", ""), after.get("design_rating", "Adequate"), process_id, target_code)
                )
                change_log_entries.append(f"Updated control {target_code} ({note})")

        elif action == "Removed":
            # Soft delete / withdraw
            if entity == "step" and target_code:
                db.execute("UPDATE steps SET status = 'withdrawn' WHERE process_id = %s AND step_code = %s;", (process_id, target_code))
                change_log_entries.append(f"Withdrawn step {target_code}")
            elif entity == "risk" and target_code:
                db.execute("UPDATE risks SET status = 'withdrawn' WHERE process_id = %s AND risk_code = %s;", (process_id, target_code))
                change_log_entries.append(f"Withdrawn risk {target_code}")
            elif entity == "control" and target_code:
                db.execute("UPDATE controls SET status = 'withdrawn' WHERE process_id = %s AND control_code = %s;", (process_id, target_code))
                change_log_entries.append(f"Withdrawn control {target_code}")

    # Mark change set applied
    db.execute("UPDATE change_sets SET status = 'applied' WHERE id = %s;", (change_set_id,))
    
    # Save new version snapshot
    log_summary = "; ".join(change_log_entries) if change_log_entries else "Model reconciled and confirmed."
    create_version_snapshot(process_id, new_ver, log_summary, user_id)
    return new_ver
