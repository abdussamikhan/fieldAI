import streamlit as st
import pandas as pd
from core.db import db
from core.storage import save_file
from core.model_repo import get_process
from graphs.orchestrator import run_task

st.set_page_config(page_title="Documents & Reconciliation · FieldAI", page_icon="📄", layout="wide")

if not st.session_state.get("user"):
    st.warning("Please sign in from the main page.")
    st.stop()

user = st.session_state.user
process_id = st.session_state.get("current_process_id", 1)
proc = get_process(process_id)

st.title("📄 Auditee Documents & Policy Reconciliation")
st.caption(f"Reconcile written SOPs and policies against walkthrough statements for **{proc['name'] if proc else 'Process'}**")

tab1, tab2, tab3 = st.tabs(["📤 Upload & Document Register", "⚖️ Said vs Documented Reconciliation", "🔍 In-Document Search & Q&A"])

with tab1:
    col1, col2 = st.columns([1.2, 1.8])

    with col1:
        st.subheader("Upload Auditee Document")
        doc_file = st.file_uploader("Upload SOP, Policy, Manual, or Org Chart", type=["pdf", "docx", "xlsx", "txt", "md"])
        doc_title = st.text_input("Document Title", value="Procurement Standard Operating Procedure")
        doc_type = st.selectbox("Document Classification", ["SOP", "Policy", "Manual", "Org Chart", "RCM Excel"])

        if st.checkbox("Or load built-in sample P2P Procurement SOP"):
            with open("sample_data/p2p_sop_procurement.txt", "rb") as f:
                doc_bytes = f.read()
            doc_file = True
            doc_title = "SOP-FIN-04 Procure to Pay v3.0"
        else:
            doc_bytes = doc_file.read() if doc_file else None

        if st.button("Parse Document & Run Reconciliation", type="primary", disabled=not bool(doc_bytes)):
            with st.spinner("Parsing document chunks, registering metadata, and performing reconciliation..."):
                file_id = save_file(doc_title, "text/plain", doc_bytes, created_by=user["id"])
                
                source_id = db.execute_insert(
                    """
                    INSERT INTO sources (process_id, kind, title, storage_path, language, consent_recorded, created_by)
                    VALUES (%s, 'document', %s, %s, 'en', TRUE, %s);
                    """,
                    (process_id, doc_title, f"file:{file_id}", user["id"])
                )

                run_task("ingest_document", {
                    "task": "ingest_document",
                    "process_id": process_id,
                    "source_id": source_id,
                    "user_id": user["id"]
                })
                st.success("Document parsed and 5-category reconciliation report generated!")
                st.rerun()

    with col2:
        st.subheader("Document Register")
        docs = db.fetch_all(
            """
            SELECT d.*, s.title, s.created_at as uploaded_at 
            FROM documents d
            JOIN sources s ON d.source_id = s.id
            WHERE s.process_id = %s
            ORDER BY d.id DESC;
            """,
            (process_id,)
        )
        if docs:
            df_docs = pd.DataFrame(docs)[["title", "doc_type", "owner", "version", "effective_date", "approval_status", "uploaded_at"]]
            st.dataframe(df_docs, use_container_width=True)
        else:
            st.info("No documents registered for this process yet.")

with tab2:
    st.subheader("⚖️ 5-Category Reconciliation Gap Report (FR-7.4)")
    st.markdown("Compares what was verbally described during the walkthrough with formal requirements written in auditee documents:")

    recons = db.fetch_all("SELECT * FROM recon_items WHERE process_id = %s ORDER BY id DESC;", (process_id,))
    if recons:
        for r in recons:
            cat = r.get("category", "Matches")
            color_map = {
                "Matches": "#10b981",
                "Documented-not-described": "#f59e0b",
                "Described-not-documented": "#8b5cf6",
                "Conflicting detail": "#ef4444",
                "Outdated document": "#64748b"
            }
            cat_color = color_map.get(cat, "#38bdf8")

            st.markdown(
                f"""
                <div style="border-left: 4px solid {cat_color}; background-color: #1e293b; padding: 12px; border-radius: 6px; margin-bottom: 10px;">
                    <span style="background-color: {cat_color}; color: white; padding: 2px 6px; border-radius: 4px; font-weight: bold; font-size: 0.75rem;">{cat.upper()}</span>
                    <b style="color: #f8fafc; margin-left: 8px;">{r.get('item_code', '')}</b>
                    <div style="margin-top: 6px; color: #cbd5e1;">{r.get('note', '')}</div>
                    <div style="margin-top: 4px; font-size: 0.85rem; color: #94a3b8;">
                        📌 <b>Document:</b> {r.get('doc_ref', '')} | 🎙️ <b>Walkthrough:</b> {r.get('meeting_ref', '')}
                    </div>
                    <div style="margin-top: 4px; font-size: 0.85rem; color: #38bdf8;">
                        👉 <b>Recommended Audit Action:</b> {r.get('suggested_action', '')}
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
    else:
        st.info("No reconciliation items generated yet. Ingest an SOP document above.")

with tab3:
    st.subheader("🔍 In-Document Search & Q&A with Grounded Citations")
    q = st.text_input("Search or ask a question regarding uploaded documents:", placeholder="e.g. What is the policy requirement for competitive vendor quotations?")
    if q:
        with st.spinner("Searching document chunks..."):
            qa_res = run_task("ask", {
                "task_input": q,
                "process_id": process_id,
                "user_id": user["id"]
            })
            res_obj = qa_res.get("doc_qa_result", {})
            st.info(f"**Answer:** {res_obj.get('answer', '')}")
            if res_obj.get("citations"):
                st.markdown("#### Citations:")
                for c in res_obj["citations"]:
                    st.caption(f"- **{c.get('source')} ({c.get('locator')}):** \"{c.get('quote')}\"")
