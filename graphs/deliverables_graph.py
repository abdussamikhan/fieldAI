from langgraph.graph import StateGraph, START, END
from graphs.state import FieldAIState
from agents import (
    flowchart_agent,
    rcm_agent,
    audit_program_agent,
    knowledge_agent
)

def build_deliverables_graph():
    builder = StateGraph(FieldAIState)

    builder.add_node("flowchart", flowchart_agent.run)
    builder.add_node("rcm", rcm_agent.run)
    builder.add_node("audit_program", audit_program_agent.run)
    builder.add_node("knowledge", knowledge_agent.run)

    builder.add_edge(START, "flowchart")
    builder.add_edge("flowchart", "rcm")
    builder.add_edge("rcm", "audit_program")
    builder.add_edge("audit_program", "knowledge")
    builder.add_edge("knowledge", END)

    return builder.compile()

deliverables_graph = build_deliverables_graph()
