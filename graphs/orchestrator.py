from typing import Dict, Any
from graphs.state import FieldAIState
from graphs.meeting_graph import meeting_graph
from graphs.document_graph import document_graph
from graphs.deliverables_graph import deliverables_graph
from graphs.prep_graph import prep_graph
from graphs.testing_graph import testing_graph
from graphs.reporting_graph import reporting_graph
from agents import doc_qa_agent
from core.llm import llm

def route_free_text_query(query: str) -> str:
    """Classifies free-text user input from 'Ask FieldAI' box into a target workflow."""
    q_lower = query.lower()
    if any(k in q_lower for k in ["prep", "question", "agenda", "scoping"]):
        return "prep"
    elif any(k in q_lower for k in ["test", "duplicate", "sod", "mining", "exception"]):
        return "testing"
    elif any(k in q_lower for k in ["finding", "qa", "standard", "report"]):
        return "reporting"
    elif any(k in q_lower for k in ["flowchart", "diagram", "rcm", "program", "deliverable"]):
        return "deliverables"
    return "doc_qa"

def run_task(task_name: str, state: FieldAIState) -> Dict[str, Any]:
    """
    Orchestrator: Routes UI tasks deterministically or free-text questions via classification.
    """
    state["task"] = task_name

    if task_name == "process_meeting":
        return meeting_graph.invoke(state)
    elif task_name == "ingest_document":
        return document_graph.invoke(state)
    elif task_name in ("rebuild_deliverables", "table_edit"):
        return deliverables_graph.invoke(state)
    elif task_name in ("prep_meeting", "copilot_chunk"):
        return prep_graph.invoke(state)
    elif task_name == "run_test":
        return testing_graph.invoke(state)
    elif task_name in ("draft_findings", "qa_review"):
        return reporting_graph.invoke(state)
    elif task_name == "ask":
        query = state.get("task_input", "")
        route = route_free_text_query(query)
        if route == "doc_qa":
            return doc_qa_agent.run(state)
        elif route == "prep":
            return prep_graph.invoke(state)
        elif route == "testing":
            return testing_graph.invoke(state)
        elif route == "reporting":
            return reporting_graph.invoke(state)
        else:
            return deliverables_graph.invoke(state)

    # Default fallback: answer via doc_qa
    return doc_qa_agent.run(state)
