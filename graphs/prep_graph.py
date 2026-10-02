from langgraph.graph import StateGraph, START, END
from graphs.state import FieldAIState
from agents import prep_agent, copilot_agent

def router_prep_or_copilot(state: FieldAIState) -> str:
    if state.get("task") == "copilot_chunk":
        return "copilot"
    return "prep"

def build_prep_graph():
    builder = StateGraph(FieldAIState)

    builder.add_node("prep", prep_agent.run)
    builder.add_node("copilot", copilot_agent.run)

    builder.add_conditional_edges(
        START,
        router_prep_or_copilot,
        {
            "prep": "prep",
            "copilot": "copilot"
        }
    )

    builder.add_edge("prep", END)
    builder.add_edge("copilot", END)

    return builder.compile()

prep_graph = build_prep_graph()
