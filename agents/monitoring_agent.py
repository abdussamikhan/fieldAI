import json
from datetime import datetime
from typing import Dict, Any, List
from graphs.state import FieldAIState
from core.db import db
from core.audit_log import log_audit

def run(state: FieldAIState) -> Dict[str, Any]:
    """
    Monitoring Agent (Option 14):
    Registers tests as recurring continuous monitoring controls and evaluates scheduled runs.
    """
    test_request = state.get("test_request", {})
    test_id = test_request.get("test_id")
    make_recurring = test_request.get("make_recurring", False)

    if test_id and make_recurring:
        # Mark test as recurring
        db.execute(
            "UPDATE test_runs SET recurring = TRUE WHERE test_id = %s;",
            (test_id,)
        )
        log_audit(state.get("user_id"), "register_continuous_monitoring", "test", test_id, {"status": "recurring"})
        return {
            "monitoring_status": f"Test {test_id} successfully scheduled for continuous automated monitoring."
        }

    # Fetch active recurring test summaries
    recurring_runs = db.fetch_all(
        """
        SELECT tr.*, t.test_code, t.control_code 
        FROM test_runs tr
        JOIN tests t ON tr.test_id = t.id
        WHERE tr.recurring = TRUE
        ORDER BY tr.run_at DESC;
        """
    )

    return {
        "active_recurring_tests": recurring_runs,
        "count": len(recurring_runs)
    }
