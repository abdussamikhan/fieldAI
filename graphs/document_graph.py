from langgraph.graph import StateGraph, START, END
from graphs.state import FieldAIState
from agents import (
    document_agent,
    reconciliation_agent,
    flowchart_agent,
    rcm_agent,
    audit_program_agent
)

def build_document_graph():
    builder = StateGraph(FieldAIState)

    builder.add_node("document", document_agent.run)
    builder.add_node("reconciliation", reconciliation_agent.run)
    builder.add_node("flowchart", flowchart_agent.run)
    builder.add_node("rcm", rcm_agent.run)
    builder.add_node("audit_program", audit_program_agent.run)

    builder.add_edge(START, "document")
    builder.add_edge("document", "reconciliation")
    builder.add_edge("reconciliation", "flowchart")
    builder.add_edge("flowchart", "rcm")
    builder.add_edge("rcm", "audit_program")
    builder.add_edge("audit_program", END)

    return builder.compile()

document_graph = build_document_graph()
