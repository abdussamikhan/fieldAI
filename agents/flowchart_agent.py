from typing import Dict, Any, List
from datetime import datetime
from graphs.state import FieldAIState
from core.db import db
from core.model_repo import get_process, get_process_master_model

def generate_dot(
    process_name: str,
    version: str,
    steps: List[Dict[str, Any]],
    risks: List[Dict[str, Any]],
    controls: List[Dict[str, Any]],
    lane_by: str = "role", # "role", "department", "system"
    orientation: str = "TB", # "TB" or "LR"
    diff_mode: bool = False
) -> str:
    """
    Deterministic Graphviz DOT generator for audit flowcharts and swim lanes.
    Includes risk badges (R-xx), control badges (C-xx), decision diamonds,
    unmitigated risk dashed borders, and audit title block.
    """
    date_str = datetime.now().strftime("%d %b %Y")
    
    # Map lane key
    lane_keys = {
        "role": "responsible_role",
        "department": "department",
        "system": "system"
    }
    lane_attr = lane_keys.get(lane_by, "responsible_role")

    dot_lines = [
        "digraph ProcessFlow {",
        f"  rankdir={orientation};",
        "  fontname=\"Helvetica,Arial,sans-serif\";",
        "  node [fontname=\"Helvetica,Arial,sans-serif\", fontsize=10];",
        "  edge [fontname=\"Helvetica,Arial,sans-serif\", fontsize=9, color=\"#64748b\"];",
        "  compound=true;",
        "  splines=ortho;",
        "  pad=0.4;",
        "  nodesep=0.5;",
        "  ranksep=0.6;",
        "",
        "  // Audit Title Block (FR-3.6)",
        "  subgraph cluster_header {",
        "    style=filled;",
        "    color=\"#f1f5f9\";",
        "    fillcolor=\"#f8fafc\";",
        "    node [shape=plaintext, fontsize=11];",
        f"    title_node [label=\"FieldAI Master Process Model\\nProcess: {process_name} | Version: {version} | Date: {date_str}\", fontcolor=\"#0f172a\", fontname=\"Helvetica-Bold\"];",
        "  }",
        ""
    ]

    # Group steps by lane
    lanes = {}
    for s in steps:
        lane_val = s.get(lane_attr) or "General"
        if lane_val not in lanes:
            lanes[lane_val] = []
        lanes[lane_val].append(s)

    # Control and Risk lookup dicts
    risks_by_code = {r.get("risk_code"): r for r in risks}
    controls_by_code = {c.get("control_code"): c for c in controls}

    # Start Node
    dot_lines.append("  start_node [shape=oval, style=filled, fillcolor=\"#10b981\", fontcolor=\"white\", label=\"Start\"];")
    prev_step_id = "start_node"

    # Render Clusters (Swim lanes)
    for idx, (lane_name, lane_steps) in enumerate(lanes.items(), 1):
        clean_lane_id = f"lane_{idx}"
        dot_lines.append(f"  subgraph cluster_{clean_lane_id} {{")
        dot_lines.append(f"    label=\"{lane_name.upper()}\";")
        dot_lines.append("    style=rounded;")
        dot_lines.append("    color=\"#cbd5e1\";")
        dot_lines.append("    bgcolor=\"#f8fafc\";")
        dot_lines.append("    fontname=\"Helvetica-Bold\";")
        dot_lines.append("    fontsize=11;")
        dot_lines.append("    fontcolor=\"#1e293b\";")

        for s in lane_steps:
            code = s.get("step_code", "")
            node_id = f"node_{code.replace('-', '_')}"
            desc = s.get("description", "")
            # Truncate long descriptions for graph clarity
            wrapped_desc = "\\n".join([desc[i:i+32] for i in range(0, min(len(desc), 96), 32)])
            
            is_decision = s.get("is_decision", False)
            shape = "diamond" if is_decision else "box"
            fillcolor = "#fef3c7" if is_decision else "#ffffff"
            stcolor = "#d97706" if is_decision else "#475569"

            # Check status for diff mode
            if diff_mode and s.get("status") == "withdrawn":
                fillcolor = "#e2e8f0"
                stcolor = "#94a3b8"
                wrapped_desc = f"[WITHDRAWN] {wrapped_desc}"

            label = f"[{code}]\\n{wrapped_desc}"
            dot_lines.append(f"    {node_id} [shape={shape}, style=\"filled,rounded\", fillcolor=\"{fillcolor}\", color=\"{stcolor}\", label=\"{label}\"];")

            # Risk badges attached to step
            # Find risks matching this step
            matched_risks = [r for r in risks if code in r.get("step_codes", [])]
            for r in matched_risks:
                r_code = r.get("risk_code")
                r_node_id = f"risk_{node_id}_{r_code.replace('-', '_')}"
                # If risk has no linked control: draw dashed red (FR-3.4)
                has_ctrl = bool(r.get("control_codes"))
                r_border = "dashed" if not has_ctrl else "solid"
                dot_lines.append(f"    {r_node_id} [shape=box, style=\"filled,{r_border}\", fillcolor=\"#fee2e2\", color=\"#ef4444\", fontcolor=\"#991b1b\", fontsize=8, label=\"{r_code}: Risk\"];")
                dot_lines.append(f"    {r_node_id} -> {node_id} [style=dotted, color=\"#ef4444\", arrowhead=none];")

            # Control badges attached to step
            matched_ctrls = [c for c in controls if code in c.get("step_codes", [])]
            for c in matched_ctrls:
                c_code = c.get("control_code")
                c_node_id = f"ctrl_{node_id}_{c_code.replace('-', '_')}"
                is_key = c.get("key_control", True)
                font_weight = "Helvetica-Bold" if is_key else "Helvetica"
                dot_lines.append(f"    {c_node_id} [shape=box, style=filled, fillcolor=\"#dcfce7\", color=\"#22c55e\", fontcolor=\"#166534\", fontsize=8, fontname=\"{font_weight}\", label=\"{c_code}: Control\"];")
                dot_lines.append(f"    {node_id} -> {c_node_id} [style=dotted, color=\"#22c55e\", arrowhead=none];")

        dot_lines.append("  }")
        dot_lines.append("")

    # Connect sequence flows between chronological steps
    sorted_steps = sorted(steps, key=lambda x: x.get("order_num", 1))
    curr_node = "start_node"
    for s in sorted_steps:
        code = s.get("step_code", "")
        nxt_node = f"node_{code.replace('-', '_')}"
        dot_lines.append(f"  {curr_node} -> {nxt_node};")
        curr_node = nxt_node

    # End Node
    dot_lines.append("  end_node [shape=oval, style=filled, fillcolor=\"#ef4444\", fontcolor=\"white\", label=\"End\"];")
    dot_lines.append(f"  {curr_node} -> end_node;")
    dot_lines.append("}")

    return "\n".join(dot_lines)

def run(state: FieldAIState) -> Dict[str, Any]:
    """
    Flowchart Agent (FR-3.x, 4.x):
    Generates Graphviz DOT representation of master process flow with lanes, badges, and controls.
    """
    process_id = state.get("process_id", 1)
    proc = get_process(process_id)
    p_name = proc.get("name", "Audit Process") if proc else "Audit Process"
    p_ver = proc.get("current_version", "v1.0") if proc else "v1.0"

    model = get_process_master_model(process_id)
    steps = model.get("steps") or state.get("extracted_steps", [])
    risks = model.get("risks") or state.get("extracted_risks", [])
    controls = model.get("controls") or state.get("extracted_controls", [])

    dot_code = generate_dot(
        process_name=p_name,
        version=p_ver,
        steps=steps,
        risks=risks,
        controls=controls,
        lane_by="role",
        orientation="TB"
    )

    deliverables = state.get("deliverables", {})
    deliverables["flowchart_dot"] = dot_code
    return {"deliverables": deliverables}
