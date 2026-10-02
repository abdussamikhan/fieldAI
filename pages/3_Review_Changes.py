import streamlit as st
import json
from core.db import db
from core.model_repo import apply_change_set, get_process
from core.agent_registry import render_deliverable_attribution
from graphs.orchestrator import run_task

st.set_page_config(page_title="Review Changes · FieldAI", page_icon="⚖️", layout="wide")

if not st.session_state.get("user"):
    st.warning("Please sign in from the main page.")
    st.stop()

user = st.session_state.user
process_id = st.session_state.get("current_process_id", 1)
proc = get_process(process_id)

st.title("⚖️ Change Set & Conflict Review")
st.caption(f"Review and resolve proposed changes to master model for **{proc['name'] if proc else 'Process'}** ({proc['current_version'] if proc else 'v1.0'})")
render_deliverable_attribution("change_set_agent", "Proposed Model Change Set & Entity Resolution")

# Retrieve latest change sets
change_sets = db.fetch_all(
    "SELECT * FROM change_sets WHERE process_id = %s ORDER BY id DESC;",
    (process_id,)
)

if not change_sets:
    st.info("No change sets recorded yet. Record or upload a walkthrough meeting in the Capture tab.")
    st.stop()

cs_options = {cs["id"]: f"Change Set #{cs['id']} ({cs['status'].upper()}) – {cs['created_at']}" for cs in change_sets}
selected_cs_id = st.selectbox("Select Change Set", options=list(cs_options.keys()), format_func=lambda x: cs_options[x])

items = db.fetch_all(
    "SELECT * FROM change_items WHERE change_set_id = %s ORDER BY id ASC;",
    (selected_cs_id,)
)

if not items:
    st.info("No change items in this change set.")
    st.stop()

col_act, col_info = st.columns([1.5, 1])
with col_act:
    st.subheader(f"Tracked Changes ({len(items)} Items)")
with col_info:
    # Summary of actions
    actions_count = {}
    for it in items:
        act = it.get("action", "Added")
        actions_count[act] = actions_count.get(act, 0) + 1
    st.write(" **Breakdown:** " + " | ".join([f"`{k}: {v}`" for k, v in actions_count.items()]))

st.divider()

for item in items:
    action = item.get("action", "Added")
    entity = item.get("entity", "step")
    target_code = item.get("target_code", "")
    decision = item.get("decision", "pending")

    color_map = {
        "Added": "#10b981",
        "Changed": "#f59e0b",
        "Contradicted": "#ef4444",
        "Confirmed": "#0284c7",
        "Removed": "#64748b"
    }
    badge_color = color_map.get(action, "#94a3b8")

    after_data = json.loads(item["after_json"]) if item.get("after_json") else {}
    before_data = json.loads(item["before_json"]) if item.get("before_json") else {}
    evidence_list = json.loads(item["evidence_json"]) if item.get("evidence_json") else []

    with st.container():
        st.markdown(
            f"""
            <div style="border-left: 5px solid {badge_color}; background-color: #1e293b; padding: 12px 18px; border-radius: 6px; margin-bottom: 12px;">
                <span style="background-color: {badge_color}; color: white; padding: 2px 8px; border-radius: 4px; font-weight: bold; font-size: 0.8rem;">{action.upper()}</span>
                <span style="color: #38bdf8; font-weight: bold; margin-left: 8px;">{entity.upper()} {target_code}</span>
                <span style="color: #94a3b8; font-size: 0.85rem; margin-left: 12px;">Status: <b>{decision.upper()}</b></span>
            </div>
            """,
            unsafe_allow_html=True
        )

        col1, col2 = st.columns([3, 1.2])
        with col1:
            if action in ("Changed", "Contradicted"):
                c_bef, c_aft = st.columns(2)
                with c_bef:
                    st.caption("🔴 **Prior Master Model:**")
                    st.json(before_data or {"info": "Prior state recorded"})
                with c_aft:
                    st.caption("🟢 **Walkthrough Statement:**")
                    st.json(after_data or {"info": "New statement recorded"})
                
                if item.get("conflict_with"):
                    st.error(f"⚠️ **Conflict:** {item['conflict_with']}")
            else:
                st.write(f"**Description:** {after_data.get('description', '')}")
                if entity == "step":
                    st.caption(f"Role: `{after_data.get('responsible_role', '')}` | Department: `{after_data.get('department', '')}` | System: `{after_data.get('system', '')}`")
                elif entity == "control":
                    st.caption(f"Type: `{after_data.get('type', '')}` | Nature: `{after_data.get('nature', '')}` | Frequency: `{after_data.get('frequency', '')}`")

            if evidence_list:
                st.caption(f"📌 Evidence / Citations: {', '.join(evidence_list)}")

        with col2:
            new_decision = st.selectbox(
                "Decision",
                options=["pending", "accepted", "rejected", "edited"],
                index=["pending", "accepted", "rejected", "edited"].index(decision) if decision in ["pending", "accepted", "rejected", "edited"] else 0,
                key=f"dec_{item['id']}"
            )
            note = st.text_input("Auditor Note / Resolution", value=item.get("resolution_note") or "", key=f"note_{item['id']}")

            if new_decision != decision or note != (item.get("resolution_note") or ""):
                db.execute(
                    "UPDATE change_items SET decision = %s, resolution_note = %s WHERE id = %s;",
                    (new_decision, note, item["id"])
                )

st.divider()

# Apply Accepted Changes Action
c_apply1, c_apply2 = st.columns([1, 1.5])
with c_apply1:
    if st.button("✅ Apply Accepted Changes to Master Model", type="primary", use_container_width=True):
        with st.spinner("Applying changes, updating version snapshot, and rebuilding deliverables..."):
            new_ver = apply_change_set(selected_cs_id, user_id=user["id"])
            # Rebuild deliverables
            run_task("rebuild_deliverables", {
                "process_id": process_id,
                "user_id": user["id"]
            })
            st.success(f"🎉 Master Model updated to version {new_ver}!")
            st.rerun()

with c_apply2:
    st.info("💡 Applying will merge accepted items into the active process table, create a new immutable version snapshot (v1.0 → v1.1), and regenerate flowcharts and RCM.")
