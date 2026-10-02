from langgraph.graph import StateGraph, START, END
from graphs.state import FieldAIState
from agents import (
    transcription_agent,
    summary_agent,
    process_extraction_agent,
    risk_control_agent,
    change_set_agent,
    flowchart_agent,
    rcm_agent,
    audit_program_agent
)
from core.model_repo import apply_change_set
from core.db import db

def node_transcription(state: FieldAIState) -> dict:
    return transcription_agent.run(state)

def node_summary(state: FieldAIState) -> dict:
    return summary_agent.run(state)

def node_process_extraction(state: FieldAIState) -> dict:
    return process_extraction_agent.run(state)

def node_risk_control(state: FieldAIState) -> dict:
    return risk_control_agent.run(state)

def node_change_set(state: FieldAIState) -> dict:
    return change_set_agent.run(state)

def node_apply_changes(state: FieldAIState) -> dict:
    # If change items exist and are auto-accepted (or initial meeting), apply to master model
    process_id = state.get("process_id", 1)
    # Check if there is an active draft change set
    cs = db.fetch_one("SELECT id FROM change_sets WHERE process_id = %s ORDER BY id DESC LIMIT 1;", (process_id,))
    if cs:
        apply_change_set(cs["id"], user_id=state.get("user_id"))
    return {}

def node_flowchart(state: FieldAIState) -> dict:
    return flowchart_agent.run(state)

def node_rcm(state: FieldAIState) -> dict:
    return rcm_agent.run(state)

def node_audit_program(state: FieldAIState) -> dict:
    return audit_program_agent.run(state)

def build_meeting_graph():
    builder = StateGraph(FieldAIState)

    builder.add_node("transcription", node_transcription)
    builder.add_node("summary", node_summary)
    builder.add_node("process_extraction", node_process_extraction)
    builder.add_node("risk_control", node_risk_control)
    builder.add_node("change_set", node_change_set)
    builder.add_node("apply_changes", node_apply_changes)
    builder.add_node("flowchart", node_flowchart)
    builder.add_node("rcm", node_rcm)
    builder.add_node("audit_program", node_audit_program)

    builder.add_edge(START, "transcription")
    builder.add_edge("transcription", "summary")
    builder.add_edge("summary", "process_extraction")
    builder.add_edge("process_extraction", "risk_control")
    builder.add_edge("risk_control", "change_set")
    builder.add_edge("change_set", "apply_changes")
    builder.add_edge("apply_changes", "flowchart")
    builder.add_edge("flowchart", "rcm")
    builder.add_edge("rcm", "audit_program")
    builder.add_edge("audit_program", END)

    return builder.compile()

meeting_graph = build_meeting_graph()
