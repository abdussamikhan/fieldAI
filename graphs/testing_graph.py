from langgraph.graph import StateGraph, START, END
from graphs.state import FieldAIState
from agents import (
    analytics_agent,
    sod_agent,
    process_mining_agent,
    evidence_agent,
    monitoring_agent
)

def test_router(state: FieldAIState) -> str:
    test_req = state.get("test_request", {})
    t_type = test_req.get("test_type", "analytics")
    if t_type == "sod":
        return "sod"
    elif t_type == "process_mining":
        return "process_mining"
    elif t_type == "evidence":
        return "evidence"
    return "analytics"

def check_recurring(state: FieldAIState) -> str:
    if state.get("test_request", {}).get("make_recurring"):
        return "monitoring"
    return END

def build_testing_graph():
    builder = StateGraph(FieldAIState)

    builder.add_node("analytics", analytics_agent.run)
    builder.add_node("sod", sod_agent.run)
    builder.add_node("process_mining", process_mining_agent.run)
    builder.add_node("evidence", evidence_agent.run)
    builder.add_node("monitoring", monitoring_agent.run)

    builder.add_conditional_edges(
        START,
        test_router,
        {
            "analytics": "analytics",
            "sod": "sod",
            "process_mining": "process_mining",
            "evidence": "evidence"
        }
    )

    builder.add_conditional_edges("analytics", check_recurring, {"monitoring": "monitoring", END: END})
    builder.add_edge("sod", END)
    builder.add_edge("process_mining", END)
    builder.add_edge("evidence", END)
    builder.add_edge("monitoring", END)

    return builder.compile()

testing_graph = build_testing_graph()
