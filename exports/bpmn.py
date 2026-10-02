from typing import List, Dict, Any
import xml.etree.ElementTree as ET

def export_bpmn_xml(
    process_name: str,
    steps: List[Dict[str, Any]],
    lane_attribute: str = "responsible_role"
) -> str:
    """
    Generates standard BPMN 2.0 XML with swim lanes corresponding to the given lane_attribute.
    """
    definitions = ET.Element("bpmn:definitions", {
        "xmlns:bpmn": "http://www.omg.org/spec/BPMN/20100524/MODEL",
        "xmlns:bpmndi": "http://www.omg.org/spec/BPMN/20100524/DI",
        "xmlns:dc": "http://www.omg.org/spec/DD/20100524/DC",
        "xmlns:di": "http://www.omg.org/spec/DD/20100524/DI",
        "id": "Definitions_1",
        "targetNamespace": "http://bpmn.io/schema/bpmn"
    })

    collaboration = ET.SubElement(definitions, "bpmn:collaboration", {"id": "Collaboration_1"})
    participant = ET.SubElement(collaboration, "bpmn:participant", {
        "id": "Participant_1",
        "name": process_name,
        "processRef": "Process_1"
    })

    process = ET.SubElement(definitions, "bpmn:process", {"id": "Process_1", "isExecutable": "false"})
    lane_set = ET.SubElement(process, "bpmn:laneSet", {"id": "LaneSet_1"})

    # Extract distinct lanes
    lanes_dict = {}
    for s in steps:
        lane_name = s.get(lane_attribute) or "General"
        if lane_name not in lanes_dict:
            lanes_dict[lane_name] = []
        lanes_dict[lane_name].append(s)

    # Start Event
    start_event = ET.SubElement(process, "bpmn:startEvent", {"id": "StartEvent_1", "name": "Start"})

    prev_node_id = "StartEvent_1"
    sequence_flows = []

    # Create lanes and tasks
    for lane_idx, (lane_name, lane_steps) in enumerate(lanes_dict.items(), 1):
        lane_id = f"Lane_{lane_idx}"
        lane_elem = ET.SubElement(lane_set, "bpmn:lane", {"id": lane_id, "name": lane_name})
        
        for s in lane_steps:
            code = s.get("step_code", f"Step_{s.get('order_num', 1)}")
            node_id = f"Task_{code.replace('-', '_')}"
            desc = s.get("description", "")
            
            flow_node_ref = ET.SubElement(lane_elem, "bpmn:flowNodeRef")
            flow_node_ref.text = node_id

            if s.get("is_decision"):
                task_elem = ET.SubElement(process, "bpmn:exclusiveGateway", {
                    "id": node_id,
                    "name": f"[{code}] {desc}"
                })
            else:
                task_elem = ET.SubElement(process, "bpmn:task", {
                    "id": node_id,
                    "name": f"[{code}] {desc}"
                })

            # Sequence Flow from prev to current
            flow_id = f"Flow_{prev_node_id}_{node_id}"
            sequence_flows.append((flow_id, prev_node_id, node_id))
            prev_node_id = node_id

    # End Event
    end_event = ET.SubElement(process, "bpmn:endEvent", {"id": "EndEvent_1", "name": "End"})
    flow_id = f"Flow_{prev_node_id}_EndEvent_1"
    sequence_flows.append((flow_id, prev_node_id, "EndEvent_1"))

    # Append Sequence Flows
    for flow_id, source_id, target_id in sequence_flows:
        ET.SubElement(process, "bpmn:sequenceFlow", {
            "id": flow_id,
            "sourceRef": source_id,
            "targetRef": target_id
        })

    return ET.tostring(definitions, encoding="utf-8", xml_declaration=True).decode("utf-8")
