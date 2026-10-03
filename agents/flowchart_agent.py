import textwrap
from typing import Dict, Any, List, Optional
from datetime import datetime
from graphs.state import FieldAIState
from core.db import db
from core.model_repo import get_process, get_process_master_model

def clean_step_summary(desc: str, density: str = "compact") -> str:
    """
    Extracts an executive-level action summary for compact diagram rendering.
    """
    if not desc:
        return ""
    if density == "full":
        return desc
    first_clause = desc.split(".")[0].split(";")[0].strip()
    words = first_clause.split()
    max_words = 5 if density == "micro" else 8
    if len(words) > max_words:
        return " ".join(words[:max_words])
    return first_clause

def generate_dot(
    process_name: str,
    version: str,
    steps: List[Dict[str, Any]],
    risks: List[Dict[str, Any]],
    controls: List[Dict[str, Any]],
    lane_by: str = "role", # "role", "department", "system"
    orientation: str = "TB", # "TB" or "LR"
    diff_mode: bool = False,
    spline_type: str = "spline", # "spline", "polyline", "ortho"
    compact: bool = True,
    density: str = "compact"
) -> str:
    """
    Deterministic Graphviz DOT generator for audit flowcharts and swim lanes.
    Includes compact geometry, small Inter typography, tight margins, and non-overlapping edges.
    """
    # Map lane key
    lane_keys = {
        "role": "responsible_role",
        "department": "department",
        "system": "system"
    }
    lane_attr = lane_keys.get(lane_by, "responsible_role")

    nodesep = 0.18 if density == "micro" else (0.24 if density == "compact" else 0.45)
    ranksep = 0.26 if density == "micro" else (0.32 if density == "compact" else 0.55)
    swim_margin = 8 if density != "full" else 14
    swim_fontsize = 8.0 if density == "micro" else (8.5 if density == "compact" else 9.5)

    dot_lines = [
        "digraph ProcessFlow {",
        f"  rankdir={orientation};",
        "  fontname=\"Inter,sans-serif\";",
        "  compound=true;",
        "  newrank=true;",
        f"  splines={spline_type};",
        f"  nodesep={nodesep};",
        f"  ranksep={ranksep};",
        "  pad=0.15;",
        "  node [fontname=\"Inter,sans-serif\"];",
        "  edge [fontname=\"Inter,sans-serif\", fontsize=7.5, color=\"#475569\", penwidth=1.1];",
        ""
    ]

    # Group steps by lane
    lanes = {}
    for s in steps:
        lane_val = s.get(lane_attr) or "General"
        if lane_val not in lanes:
            lanes[lane_val] = []
        lanes[lane_val].append(s)

    # Start Node (Compact Pill)
    start_fs = 7.5 if density == "micro" else 8.0
    dot_lines.append(f'  start_node [shape=oval, style=filled, fillcolor="#10b981", color="#059669", fontcolor="white", fontsize={start_fs}, margin="0.05,0.025", label="Start"];')

    # Render Clusters (Swim lanes)
    for idx, (lane_name, lane_steps) in enumerate(lanes.items(), 1):
        clean_lane_id = f"lane_{idx}"
        dot_lines.append(f"  subgraph cluster_{clean_lane_id} {{")
        dot_lines.append(f"    label=\"{lane_name.upper()}\";")
        dot_lines.append("    labelloc=\"t\";")
        dot_lines.append("    labeljust=\"l\";")
        dot_lines.append(f"    margin={swim_margin};")
        dot_lines.append("    style=\"rounded,filled\";")
        dot_lines.append("    color=\"#cbd5e1\";")
        dot_lines.append("    fillcolor=\"#f8fafc\";")
        dot_lines.append("    fontname=\"Inter,sans-serif\";")
        dot_lines.append(f"    fontsize={swim_fontsize};")
        dot_lines.append("    fontcolor=\"#334155\";")

        for s in lane_steps:
            code = s.get("step_code", "")
            node_id = f"node_{code.replace('-', '_')}"
            desc = s.get("description", "").strip()
            is_decision = s.get("is_decision", False)

            summary = clean_step_summary(desc, density=density)
            if density == "micro":
                wrap_w = 16 if is_decision else 18
                step_fs = 7.0 if is_decision else 7.5
                step_margin = "0.04,0.02" if is_decision else "0.05,0.025"
            elif density == "compact":
                wrap_w = 18 if is_decision else 22
                step_fs = 7.5 if is_decision else 8.0
                step_margin = "0.05,0.025" if is_decision else "0.06,0.03"
            else:
                wrap_w = 22 if is_decision else 28
                step_fs = 8.5 if is_decision else 9.0
                step_margin = "0.08,0.04" if is_decision else "0.10,0.06"

            wrapped_desc = "\\n".join(textwrap.wrap(summary, width=wrap_w, break_long_words=False))

            # Style attributes
            if diff_mode and s.get("status") == "withdrawn":
                fillcolor = "#f1f5f9"
                stcolor = "#94a3b8"
                fontcolor = "#64748b"
                shape = "box"
                wrapped_desc = f"[WITHDRAWN]\\n{wrapped_desc}"
            elif is_decision:
                shape = "diamond"
                fillcolor = "#fffbeb"
                stcolor = "#d97706"
                fontcolor = "#78350f"
            else:
                shape = "box"
                fillcolor = "#ffffff"
                stcolor = "#475569"
                fontcolor = "#0f172a"

            label = f"[{code}]\\n{wrapped_desc}"

            if is_decision:
                dot_lines.append(f'    {node_id} [shape={shape}, style="filled", fillcolor="{fillcolor}", color="{stcolor}", fontcolor="{fontcolor}", fontsize={step_fs}, margin="{step_margin}", label="{label}"];')
            else:
                dot_lines.append(f'    {node_id} [shape={shape}, style="filled,rounded", fillcolor="{fillcolor}", color="{stcolor}", fontcolor="{fontcolor}", fontsize={step_fs}, margin="{step_margin}", label="{label}"];')

            # Risk badges attached to step
            matched_risks = [r for r in risks if code in r.get("step_codes", [])]
            for r in matched_risks:
                r_code = r.get("risk_code")
                r_node_id = f"risk_{node_id}_{r_code.replace('-', '_')}"
                has_ctrl = bool(r.get("control_codes"))
                r_border = "dashed" if not has_ctrl else "solid"
                dot_lines.append(f'    {r_node_id} [shape=box, style="filled,{r_border}", fillcolor="#fee2e2", color="#ef4444", fontcolor="#991b1b", fontsize=7, margin="0.04,0.02", label="{r_code}: Risk"];')
                dot_lines.append(f'    {r_node_id} -> {node_id} [style=dotted, color="#ef4444", arrowhead=none, weight=1];')

            # Control badges attached to step
            matched_ctrls = [c for c in controls if code in c.get("step_codes", [])]
            for c in matched_ctrls:
                c_code = c.get("control_code")
                c_node_id = f"ctrl_{node_id}_{c_code.replace('-', '_')}"
                dot_lines.append(f'    {c_node_id} [shape=box, style=filled, fillcolor="#dcfce7", color="#22c55e", fontcolor="#166534", fontsize=7, margin="0.04,0.02", label="{c_code}: Control"];')
                dot_lines.append(f'    {node_id} -> {c_node_id} [style=dotted, color="#22c55e", arrowhead=none, weight=1];')

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

    # End Node (Compact Pill)
    end_fs = 7.5 if density == "micro" else 8.0
    dot_lines.append(f'  end_node [shape=oval, style=filled, fillcolor="#ef4444", color="#dc2626", fontcolor="white", fontsize={end_fs}, margin="0.05,0.025", label="End"];')
    dot_lines.append(f"  {curr_node} -> end_node;")
    dot_lines.append("}")

    return "\n".join(dot_lines)

def generate_mermaid(
    process_name: str,
    version: str,
    steps: List[Dict[str, Any]],
    risks: List[Dict[str, Any]],
    controls: List[Dict[str, Any]],
    lane_by: str = "role", # "role", "department", "system"
    orientation: str = "TB", # "TB" or "LR"
    compact: bool = False
) -> str:
    """
    Generates a modern, responsive Mermaid.js flowchart with multi-lane swimlanes,
    decision gateways, risk pills, control pills, and sleek typography.
    """
    lane_keys = {
        "role": "responsible_role",
        "department": "department",
        "system": "system"
    }
    lane_attr = lane_keys.get(lane_by, "responsible_role")
    lane_icons = {
        "role": "👤",
        "department": "🏢",
        "system": "⚙️"
    }
    icon = lane_icons.get(lane_by, "📋")

    lines = [
        f"flowchart {orientation}",
        "  %% Styling theme definitions",
        "  classDef startEnd fill:#10b981,stroke:#059669,stroke-width:1.5px,color:#ffffff,font-weight:500;",
        "  classDef endNode fill:#ef4444,stroke:#dc2626,stroke-width:1.5px,color:#ffffff,font-weight:500;",
        "  classDef processStep fill:#ffffff,stroke:#64748b,stroke-width:1.5px,color:#0f172a,rx:8px,ry:8px;",
        "  classDef decisionStep fill:#fffbeb,stroke:#d97706,stroke-width:1.5px,color:#92400e;",
        "  classDef riskBadge fill:#fee2e2,stroke:#ef4444,stroke-width:1px,color:#991b1b,font-size:10px;",
        "  classDef unmitigatedRisk fill:#fee2e2,stroke:#ef4444,stroke-width:1.5px,stroke-dasharray:3 3,color:#991b1b,font-size:10px;",
        "  classDef controlBadge fill:#dcfce7,stroke:#22c55e,stroke-width:1px,color:#166534,font-size:10px;",
        "",
        "  startNode([Start]):::startEnd"
    ]

    # Group steps by lane
    lanes = {}
    for s in steps:
        lane_val = s.get(lane_attr) or "General"
        if lane_val not in lanes:
            lanes[lane_val] = []
        lanes[lane_val].append(s)

    for idx, (lane_name, lane_steps) in enumerate(lanes.items(), 1):
        clean_lane_id = f"lane_{idx}"
        safe_lane_title = lane_name.replace('"', '&quot;')
        lines.append(f'  subgraph {clean_lane_id} ["{icon} {safe_lane_title}"]')

        for s in lane_steps:
            code = s.get("step_code", "")
            node_id = f"m_{code.replace('-', '_')}"
            desc = s.get("description", "").strip()
            is_decision = s.get("is_decision", False)

            if compact:
                summary = desc.split(".")[0].strip() if "." in desc else desc
                wrap_w = 26 if is_decision else 32
                wrapped_desc = "<br/>".join(textwrap.wrap(summary, width=wrap_w, break_long_words=False))
            else:
                wrap_w = 26 if is_decision else 34
                wrapped_desc = "<br/>".join(textwrap.wrap(desc, width=wrap_w, break_long_words=False))

            # Sanitize text
            safe_desc = wrapped_desc.replace('"', '&quot;').replace('[', '&#91;').replace(']', '&#93;')
            safe_code = code.replace('"', '&quot;')

            if is_decision:
                lines.append(f'    {node_id}{{"<b>[{safe_code}]</b><br/>{safe_desc}"}}:::decisionStep')
            else:
                lines.append(f'    {node_id}["<b>[{safe_code}]</b><br/>{safe_desc}"]:::processStep')

            # Risk badges
            matched_risks = [r for r in risks if code in r.get("step_codes", [])]
            for r in matched_risks:
                r_code = r.get("risk_code")
                r_node_id = f"r_{node_id}_{r_code.replace('-', '_')}"
                has_ctrl = bool(r.get("control_codes"))
                r_cls = "riskBadge" if has_ctrl else "unmitigatedRisk"
                lines.append(f'    {r_node_id}["⚠️ {r_code}: Risk"]:::{r_cls}')
                lines.append(f'    {node_id} -.- {r_node_id}')

            # Control badges
            matched_ctrls = [c for c in controls if code in c.get("step_codes", [])]
            for c in matched_ctrls:
                c_code = c.get("control_code")
                c_node_id = f"c_{node_id}_{c_code.replace('-', '_')}"
                lines.append(f'    {c_node_id}["🛡️ {c_code}: Control"]:::controlBadge')
                lines.append(f'    {node_id} -.- {c_node_id}')

        lines.append("  end")
        lines.append("")

    # Connect sequence
    sorted_steps = sorted(steps, key=lambda x: x.get("order_num", 1))
    curr_node = "startNode"
    for s in sorted_steps:
        code = s.get("step_code", "")
        nxt_node = f"m_{code.replace('-', '_')}"
        lines.append(f"  {curr_node} --> {nxt_node}")
        curr_node = nxt_node

    lines.append(f"  {curr_node} --> endNode([End]):::endNode")
    return "\n".join(lines)

def generate_cytoscape_elements(
    process_name: str,
    version: str,
    steps: List[Dict[str, Any]],
    risks: List[Dict[str, Any]],
    controls: List[Dict[str, Any]],
    lane_by: str = "role",
    compact: bool = True,
    density: str = "compact"
) -> List[Dict[str, Any]]:
    """
    Generates Cytoscape.js compatible graph elements with compact density scaling.
    """
    lane_keys = {
        "role": "responsible_role",
        "department": "department",
        "system": "system"
    }
    lane_attr = lane_keys.get(lane_by, "responsible_role")
    lane_icons = {
        "role": "👤",
        "department": "🏢",
        "system": "⚙️"
    }
    icon = lane_icons.get(lane_by, "📋")

    elements = []

    # Group steps by lane
    lanes = {}
    for s in steps:
        lane_val = s.get(lane_attr) or "General"
        if lane_val not in lanes:
            lanes[lane_val] = []
        lanes[lane_val].append(s)

    # 1. Swimlane parent compound nodes
    for idx, (lane_name, lane_steps) in enumerate(lanes.items(), 1):
        lane_id = f"lane_{idx}"
        elements.append({
            "data": {
                "id": lane_id,
                "label": f"{icon} {lane_name.upper()}",
                "is_lane": True
            },
            "classes": "swimlane"
        })

        for s in lane_steps:
            code = s.get("step_code", "")
            node_id = f"node_{code.replace('-', '_')}"
            desc = s.get("description", "").strip()
            is_decision = s.get("is_decision", False)

            summary = clean_step_summary(desc, density=density)
            if density == "micro":
                wrap_w = 14 if is_decision else 16
            elif density == "compact":
                wrap_w = 16 if is_decision else 20
            else:
                wrap_w = 20 if is_decision else 26

            wrapped_desc = "\n".join(textwrap.wrap(summary, width=wrap_w, break_long_words=False))
            node_label = f"[{code}]\n{wrapped_desc}"

            elements.append({
                "data": {
                    "id": node_id,
                    "parent": lane_id,
                    "label": node_label,
                    "step_code": code,
                    "description": desc,
                    "is_decision": is_decision,
                    "responsible_role": s.get("responsible_role", ""),
                    "department": s.get("department", ""),
                    "system": s.get("system", "")
                },
                "classes": "decisionStep" if is_decision else "processStep"
            })

            # Risk badges
            matched_risks = [r for r in risks if code in r.get("step_codes", [])]
            for r in matched_risks:
                r_code = r.get("risk_code")
                r_id = f"risk_{node_id}_{r_code.replace('-', '_')}"
                has_ctrl = bool(r.get("control_codes"))
                elements.append({
                    "data": {
                        "id": r_id,
                        "parent": lane_id,
                        "label": f"⚠️ {r_code}: Risk",
                        "risk_code": r_code,
                        "has_control": has_ctrl
                    },
                    "classes": "riskBadge" if has_ctrl else "unmitigatedRisk"
                })
                elements.append({
                    "data": {
                        "id": f"e_{r_id}",
                        "source": node_id,
                        "target": r_id
                    },
                    "classes": "badgeEdge"
                })

            # Control badges
            matched_ctrls = [c for c in controls if code in c.get("step_codes", [])]
            for c in matched_ctrls:
                c_code = c.get("control_code")
                c_id = f"ctrl_{node_id}_{c_code.replace('-', '_')}"
                elements.append({
                    "data": {
                        "id": c_id,
                        "parent": lane_id,
                        "label": f"🛡️ {c_code}: Control",
                        "control_code": c_code
                    },
                    "classes": "controlBadge"
                })
                elements.append({
                    "data": {
                        "id": f"e_{c_id}",
                        "source": node_id,
                        "target": c_id
                    },
                    "classes": "badgeEdge"
                })

    # Start and End Nodes
    first_lane_id = "lane_1" if lanes else None
    last_lane_id = f"lane_{len(lanes)}" if lanes else None

    start_data = {"id": "start_node", "label": "Start"}
    if first_lane_id:
        start_data["parent"] = first_lane_id
    elements.append({
        "data": start_data,
        "classes": "startEnd"
    })

    sorted_steps = sorted(steps, key=lambda x: x.get("order_num", 1))
    curr_node = "start_node"
    for s in sorted_steps:
        code = s.get("step_code", "")
        nxt_node = f"node_{code.replace('-', '_')}"
        elements.append({
            "data": {
                "id": f"flow_{curr_node}_{nxt_node}",
                "source": curr_node,
                "target": nxt_node
            },
            "classes": "sequenceEdge"
        })
        curr_node = nxt_node

    end_data = {"id": "end_node", "label": "End"}
    if last_lane_id:
        end_data["parent"] = last_lane_id
    elements.append({
        "data": end_data,
        "classes": "endNode"
    })
    elements.append({
        "data": {
            "id": f"flow_{curr_node}_end",
            "source": curr_node,
            "target": "end_node"
        },
        "classes": "sequenceEdge"
    })

    return elements

def run(state: FieldAIState) -> Dict[str, Any]:
    """
    Flowchart Agent (FR-3.x, 4.x):
    Generates Graphviz DOT, Mermaid, and Cytoscape representations of master process flow with lanes, badges, and controls.
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
        orientation="TB",
        spline_type="spline"
    )

    mermaid_code = generate_mermaid(
        process_name=p_name,
        version=p_ver,
        steps=steps,
        risks=risks,
        controls=controls,
        lane_by="role",
        orientation="TB"
    )

    cytoscape_elements = generate_cytoscape_elements(
        process_name=p_name,
        version=p_ver,
        steps=steps,
        risks=risks,
        controls=controls,
        lane_by="role"
    )

    deliverables = state.get("deliverables", {})
    deliverables["flowchart_dot"] = dot_code
    deliverables["flowchart_mermaid"] = mermaid_code
    deliverables["flowchart_cytoscape"] = cytoscape_elements
    return {"deliverables": deliverables}

