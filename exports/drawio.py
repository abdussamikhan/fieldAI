from typing import List, Dict, Any
import xml.etree.ElementTree as ET

def export_drawio_xml(
    process_name: str,
    steps: List[Dict[str, Any]],
    lane_attribute: str = "responsible_role"
) -> str:
    """
    Generates standard draw.io / diagrams.net XML with swim lane headers,
    step boxes, decision diamonds, and sequential arrows.
    """
    mxfile = ET.Element("mxfile", {"host": "app.diagrams.net", "type": "device"})
    diagram = ET.SubElement(mxfile, "diagram", {"name": process_name, "id": "fieldai_flow"})
    model = ET.SubElement(diagram, "mxGraphModel", {
        "dx": "1200", "dy": "800", "grid": "1", "gridSize": "10", "guides": "1",
        "tooltips": "1", "connect": "1", "arrows": "1", "page": "1", "pageScale": "1"
    })
    root = ET.SubElement(model, "root")
    
    # Layer 0 and Layer 1
    ET.SubElement(root, "mxCell", {"id": "0"})
    ET.SubElement(root, "mxCell", {"id": "1", "parent": "0"})

    # Group steps by lane
    lanes = {}
    for s in steps:
        l = s.get(lane_attribute) or "General"
        if l not in lanes:
            lanes[l] = []
        lanes[l].append(s)

    current_y = 40
    cell_id_counter = 10
    prev_cell_id = None

    for lane_name, lane_steps in lanes.items():
        # Swimlane Header
        lane_cell_id = str(cell_id_counter)
        cell_id_counter += 1
        lane_height = max(len(lane_steps) * 110 + 40, 140)

        ET.SubElement(root, "mxCell", {
            "id": lane_cell_id,
            "value": lane_name,
            "style": "swimlane;fontFamily=Inter;fontStyle=0;align=center;verticalAlign=top;childLayout=stackLayout;horizontal=1;startSize=30;horizontalFlip=0;fillColor=#1e293b;fontColor=#ffffff;strokeColor=#334155;",
            "vertex": "1",
            "parent": "1"
        })
        ET.SubElement(root.find(f"./mxCell[@id='{lane_cell_id}']"), "mxGeometry", {
            "x": "40", "y": str(current_y), "width": "900", "height": str(lane_height), "as": "geometry"
        })

        step_y = current_y + 40
        for s in lane_steps:
            step_id = str(cell_id_counter)
            cell_id_counter += 1
            code = s.get("step_code", "")
            desc = s.get("description", "")
            label = f"[{code}]<br/>{desc}"
            
            is_decision = s.get("is_decision", False)
            shape_style = "rhombus;whiteSpace=wrap;html=1;fontFamily=Inter;fontStyle=0;fillColor=#fef3c7;strokeColor=#d97706;fontColor=#78350f;" if is_decision else "rounded=1;whiteSpace=wrap;html=1;fontFamily=Inter;fontStyle=0;fillColor=#f8fafc;strokeColor=#64748b;fontColor=#0f172a;"

            ET.SubElement(root, "mxCell", {
                "id": step_id,
                "value": label,
                "style": shape_style,
                "vertex": "1",
                "parent": "1"
            })
            ET.SubElement(root.find(f"./mxCell[@id='{step_id}']"), "mxGeometry", {
                "x": "260", "y": str(step_y), "width": "240", "height": "70", "as": "geometry"
            })

            # Add connecting edge from previous step
            if prev_cell_id:
                edge_id = str(cell_id_counter)
                cell_id_counter += 1
                edge = ET.SubElement(root, "mxCell", {
                    "id": edge_id,
                    "edge": "1",
                    "parent": "1",
                    "source": prev_cell_id,
                    "target": step_id,
                    "style": "edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;strokeColor=#0284c7;strokeWidth=2;"
                })
                ET.SubElement(edge, "mxGeometry", {"relative": "1", "as": "geometry"})

            prev_cell_id = step_id
            step_y += 100

        current_y += lane_height + 20

    return ET.tostring(mxfile, encoding="utf-8", xml_declaration=True).decode("utf-8")
