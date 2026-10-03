import io
import json
import csv
import streamlit as st
import pandas as pd
from core.db import db
from core.model_repo import get_process
from core.prep_repo import (
    save_question_pack,
    list_question_packs,
    get_question_pack,
    delete_question_pack
)
from core.agent_registry import render_active_agent_pill, render_deliverable_attribution
from core.ui import apply_inter_theme
from graphs.orchestrator import run_task

st.set_page_config(page_title="Preparation & Scoping · FieldAI", page_icon="📋", layout="wide")
apply_inter_theme()

if not st.session_state.get("user"):
    st.warning("Please sign in from the main page.")
    st.stop()

user = st.session_state.user
process_id = st.session_state.get("current_process_id", 1)
proc = get_process(process_id)
proc_name = proc["name"] if proc else "Process"
proc_ver = proc["current_version"] if proc else "v1.0"

st.title("📋 Walkthrough Preparation & Scoping")
st.caption(f"Pre-meeting question pack and risk-based scoping for **{proc_name}** ({proc_ver})")

tab_gen, tab_storage = st.tabs([
    "⚡ Walkthrough Scoping & Question Pack Generator",
    "🗄️ Centralized Database Storage & Saved Packs"
])

with tab_gen:
    col_btn1, col_btn2 = st.columns([1, 1.5])
    with col_btn1:
        if st.button("⚡ Generate Bilingual Walkthrough Question Pack", type="primary", use_container_width=True):
            status_box = st.status("🤖 Active Agent: prep_agent executing...", expanded=True)
            with status_box:
                st.write("📋 **Active Agent: prep_agent** — Analyzing open items, risk library, and formulating bilingual questions...")
                prep_res = run_task("prep_meeting", {
                    "process_id": process_id,
                    "user_id": user["id"]
                })
                pack = prep_res.get("prep_package", {})
                st.session_state.prep_res = pack
                st.session_state.last_saved_pack_id = None
                status_box.update(label="✅ prep_agent Completed Successfully!", state="complete", expanded=False)
            st.success("✅ Bilingual Question Pack generated successfully!")

    prep_data = st.session_state.get("prep_res")

    if prep_data and (prep_data.get("question_pack") or prep_data.get("scoping")):
        scoping = prep_data.get("scoping", {})
        questions = prep_data.get("question_pack", [])

        st.divider()
        render_deliverable_attribution("prep_agent", "Bilingual Walkthrough Question Pack & Risk Scoping", version=proc_ver)
        st.subheader("📊 Risk-Based Scoping Recommendation")
        s1, s2, s3 = st.columns(3)
        with s1:
            st.metric("Inherent Process Risk", scoping.get("inherent_risk_score", "High"))
        with s2:
            st.metric("Indicative Fieldwork Hours", f"{scoping.get('indicative_hours', 80)} hrs")
        with s3:
            st.metric("Focus Areas Count", len(scoping.get("recommended_scope_areas", [])))

        focus_areas = scoping.get("recommended_scope_areas", [])
        if focus_areas:
            st.markdown("#### 🎯 Recommended Audit Focus Areas:")
            for a in focus_areas:
                st.markdown(f"- **{a}**")

        st.divider()
        st.subheader(f"🌐 Bilingual Walkthrough Question Pack ({len(questions)} Questions)")

        for idx, q in enumerate(questions, 1):
            phase = q.get("phase", "General Walkthrough")
            q_en = q.get("question_en", "")
            with st.expander(f"Q{idx} [{phase}]: {q_en}"):
                col_en, col_ar = st.columns(2)
                with col_en:
                    st.markdown(f"**English:** {q_en}")
                    st.caption(f"🎯 **Audit Objective:** {q.get('objective', '')}")
                with col_ar:
                    q_ar = q.get("question_ar", "")
                    st.markdown(f"<div style='text-align: right; direction: rtl;'><b>العربية:</b> {q_ar}</div>", unsafe_allow_html=True)
                    st.caption(f"📁 **Expected Evidence / PBC:** {q.get('expected_evidence', '')}")

        # Centralized Storage Save Card
        st.divider()
        with st.container(border=True):
            st.markdown("### 💾 Save to Centralized Database Storage")
            st.caption("Store this Question Pack permanently in the central database for this audit process.")

            c_title, c_ver = st.columns([3, 1])
            with c_title:
                default_title = f"{proc_name} Walkthrough Question Pack ({proc_ver})"
                save_title = st.text_input("Question Pack Title", value=default_title, key="input_save_title")
            with c_ver:
                save_version = st.text_input("Version Tag", value=proc_ver, key="input_save_version")

            if st.button("💾 Save Pack to Centralized Database", type="secondary", use_container_width=True):
                saved_id = save_question_pack(
                    process_id=process_id,
                    title=save_title.strip() or default_title,
                    scoping=scoping,
                    questions=questions,
                    version=save_version.strip() or "v1.0",
                    user_id=user["id"]
                )
                st.session_state.last_saved_pack_id = saved_id
                st.success(f"✅ Successfully saved to Centralized Database Storage as Pack **#{saved_id}**! Accessible anytime in the 'Centralized Database Storage' tab.")

        # Download / Export Section
        st.markdown("#### 📥 Export Question Pack")
        c_exp1, c_exp2 = st.columns(2)
        with c_exp1:
            json_str = json.dumps(prep_data, indent=2, ensure_ascii=False)
            st.download_button(
                "📥 Download Pack as JSON",
                data=json_str,
                file_name=f"question_pack_p{process_id}_{proc_ver}.json",
                mime="application/json",
                use_container_width=True
            )
        with c_exp2:
            # Prepare CSV
            csv_buffer = io.StringIO()
            writer = csv.writer(csv_buffer)
            writer.writerow(["#", "Phase", "Question (EN)", "Question (AR)", "Audit Objective", "Expected Evidence"])
            for idx, q in enumerate(questions, 1):
                writer.writerow([
                    idx,
                    q.get("phase", ""),
                    q.get("question_en", ""),
                    q.get("question_ar", ""),
                    q.get("objective", ""),
                    q.get("expected_evidence", "")
                ])
            st.download_button(
                "📥 Download Pack as CSV",
                data=csv_buffer.getvalue().encode("utf-8-sig"),
                file_name=f"question_pack_p{process_id}_{proc_ver}.csv",
                mime="text/csv",
                use_container_width=True
            )

    else:
        st.info("Click the button above to generate a tailored walkthrough question pack based on process risks and open items.")

with tab_storage:
    st.subheader(f"🗄️ Centralized Database Storage for **{proc_name}**")
    st.caption("Browse, inspect, reload, or export question packs stored in the centralized database.")

    saved_packs = list_question_packs(process_id)

    if not saved_packs:
        st.info("No saved question packs found in the centralized database for this process. Generate a pack and click 'Save to Centralized Database Storage' to store it here.")
    else:
        m1, m2, m3 = st.columns(3)
        with m1:
            st.metric("Total Saved Packs", len(saved_packs))
        with m2:
            st.metric("Latest Pack Version", saved_packs[0].get("version", "v1.0"))
        with m3:
            st.metric("Most Recent Save", str(saved_packs[0].get("created_at", "N/A"))[:16])

        st.divider()

        # Selection of pack
        pack_options = {
            f"Pack #{p['id']}: {p['title']} ({p.get('version', 'v1.0')}) - Saved {str(p.get('created_at', ''))[:16]}": p["id"]
            for p in saved_packs
        }
        selected_label = st.selectbox("Select a Saved Question Pack to View / Load:", options=list(pack_options.keys()))
        selected_pack_id = pack_options[selected_label]
        selected_pack = next((p for p in saved_packs if p["id"] == selected_pack_id), None)

        if selected_pack:
            with st.container(border=True):
                c_info1, c_info2 = st.columns([2, 1])
                with c_info1:
                    st.markdown(f"### 📦 {selected_pack['title']}")
                    st.caption(f"Version: `{selected_pack.get('version', 'v1.0')}` | Author: `{selected_pack.get('creator_name') or 'Auditor'}` | Saved: `{selected_pack.get('created_at')}`")
                with c_info2:
                    c_act1, c_act2 = st.columns(2)
                    with c_act1:
                        if st.button("🔄 Load Active", key=f"load_{selected_pack['id']}", use_container_width=True):
                            st.session_state.prep_res = {
                                "scoping": selected_pack.get("scoping", {}),
                                "question_pack": selected_pack.get("questions", [])
                            }
                            st.success("Loaded into active session! Switch to the Generator tab to inspect or edit.")
                    with c_act2:
                        if st.button("🗑️ Delete", key=f"del_{selected_pack['id']}", use_container_width=True):
                            delete_question_pack(selected_pack["id"], user["id"])
                            st.warning(f"Deleted Pack #{selected_pack['id']}.")
                            st.rerun()

                scoping_saved = selected_pack.get("scoping", {})
                questions_saved = selected_pack.get("questions", [])

                if scoping_saved:
                    st.markdown("#### Scoping Overview")
                    sk1, sk2 = st.columns(2)
                    with sk1:
                        st.write(f"**Inherent Risk:** {scoping_saved.get('inherent_risk_score', 'High')}")
                        st.write(f"**Fieldwork Hours:** {scoping_saved.get('indicative_hours', 80)} hrs")
                    with sk2:
                        st.write("**Recommended Scope Areas:**")
                        for area in scoping_saved.get("recommended_scope_areas", []):
                            st.write(f"- {area}")

                st.markdown(f"#### Questions ({len(questions_saved)} total)")
                for idx, q in enumerate(questions_saved, 1):
                    with st.expander(f"Q{idx} [{q.get('phase', 'General')}]: {q.get('question_en', '')}"):
                        col_en, col_ar = st.columns(2)
                        with col_en:
                            st.markdown(f"**English:** {q.get('question_en', '')}")
                            st.caption(f"🎯 **Objective:** {q.get('objective', '')}")
                        with col_ar:
                            st.markdown(f"<div style='text-align: right; direction: rtl;'><b>العربية:</b> {q.get('question_ar', '')}</div>", unsafe_allow_html=True)
                            st.caption(f"📁 **Expected Evidence:** {q.get('expected_evidence', '')}")

                # Download Buttons for saved pack
                st.divider()
                cd1, cd2 = st.columns(2)
                with cd1:
                    json_data = json.dumps({
                        "id": selected_pack["id"],
                        "title": selected_pack["title"],
                        "version": selected_pack.get("version"),
                        "scoping": scoping_saved,
                        "question_pack": questions_saved
                    }, indent=2, ensure_ascii=False)
                    st.download_button(
                        f"📥 Download Pack #{selected_pack['id']} (JSON)",
                        data=json_data,
                        file_name=f"saved_question_pack_{selected_pack['id']}.json",
                        mime="application/json",
                        key=f"dl_json_{selected_pack['id']}",
                        use_container_width=True
                    )
                with cd2:
                    csv_buf = io.StringIO()
                    w = csv.writer(csv_buf)
                    w.writerow(["#", "Phase", "Question (EN)", "Question (AR)", "Audit Objective", "Expected Evidence"])
                    for idx, q in enumerate(questions_saved, 1):
                        w.writerow([
                            idx,
                            q.get("phase", ""),
                            q.get("question_en", ""),
                            q.get("question_ar", ""),
                            q.get("objective", ""),
                            q.get("expected_evidence", "")
                        ])
                    st.download_button(
                        f"📥 Download Pack #{selected_pack['id']} (CSV)",
                        data=csv_buf.getvalue().encode("utf-8-sig"),
                        file_name=f"saved_question_pack_{selected_pack['id']}.csv",
                        mime="text/csv",
                        key=f"dl_csv_{selected_pack['id']}",
                        use_container_width=True
                    )
