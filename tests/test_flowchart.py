import pytest
from core.model_repo import get_process_master_model
from agents.flowchart_agent import generate_dot, generate_mermaid, generate_cytoscape_elements, run

def test_generate_dot_enhancements():
    m = get_process_master_model(1)
    steps = m.get("steps", [])
    risks = m.get("risks", [])
    controls = m.get("controls", [])
    
    dot = generate_dot("Procure-to-Pay", "v1.0", steps, risks, controls, spline_type="spline", compact=True)
    
    # Assert spline routing is smooth (no overlap)
    assert "splines=spline;" in dot
    # Assert lane headers are top-left aligned so incoming edges don't hit them
    assert 'labelloc="t";' in dot
    assert 'labeljust="l";' in dot
    # Assert no arbitrary character slicing
    assert "Start" in dot
    assert "End" in dot
    assert "node_P2P_01" in dot

def test_generate_mermaid_structure():
    m = get_process_master_model(1)
    steps = m.get("steps", [])
    risks = m.get("risks", [])
    controls = m.get("controls", [])
    
    mmd = generate_mermaid("Procure-to-Pay", "v1.0", steps, risks, controls, lane_by="role", compact=True)
    
    assert mmd.startswith("flowchart TB")
    assert "startNode([Start])" in mmd
    assert "endNode([End])" in mmd
    assert "subgraph" in mmd
    assert "m_P2P_01" in mmd
    assert "classDef" in mmd

def test_generate_cytoscape_elements():
    m = get_process_master_model(1)
    steps = m.get("steps", [])
    risks = m.get("risks", [])
    controls = m.get("controls", [])
    
    elements = generate_cytoscape_elements("Procure-to-Pay", "v1.0", steps, risks, controls, lane_by="role", compact=True)
    
    assert isinstance(elements, list)
    assert len(elements) >= 5
    
    # Check swimlane, step, and edge definitions
    element_classes = [el.get("classes", "") for el in elements]
    assert any("swimlane" in c for c in element_classes)
    assert any("processStep" in c for c in element_classes)
    assert any("sequenceEdge" in c for c in element_classes)

def test_flowchart_agent_run():
    state = {"process_id": 1, "deliverables": {}}
    res = run(state)
    assert "deliverables" in res
    deliv = res["deliverables"]
    assert "flowchart_dot" in deliv
    assert "flowchart_mermaid" in deliv
    assert "flowchart_cytoscape" in deliv
    assert len(deliv["flowchart_dot"]) > 100
    assert len(deliv["flowchart_mermaid"]) > 100
    assert len(deliv["flowchart_cytoscape"]) >= 5
