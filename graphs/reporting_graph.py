from langgraph.graph import StateGraph, START, END
from graphs.state import FieldAIState
from agents import findings_agent, qa_review_agent

def build_reporting_graph():
    builder = StateGraph(FieldAIState)

    builder.add_node("findings", findings_agent.run)
    builder.add_node("qa_review", qa_review_agent.run)

    builder.add_edge(START, "findings")
    builder.add_edge("findings", "qa_review")
    builder.add_edge("qa_review", END)

    return builder.compile()

reporting_graph = build_reporting_graph()
