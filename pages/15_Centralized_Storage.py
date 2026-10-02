import streamlit as st
import os
import io
from pathlib import Path
from core.db import db
from core.model_repo import get_process
from core.storage import (
    get_storage_root,
    get_storage_stats,
    list_storage_files,
    get_file,
    save_file,
    delete_file,
    compute_sha256,
    seed_sample_storage_files,
    CATEGORIES
)
from core.ui import apply_inter_theme

st.set_page_config(page_title="Centralized Storage · FieldAI", page_icon="🗄️", layout="wide")
apply_inter_theme()
seed_sample_storage_files()

if not st.session_state.get("user"):
    st.warning("Please sign in from the main page.")
    st.stop()

user = st.session_state.user
process_id = st.session_state.get("current_process_id", 1)
proc = get_process(process_id)
proc_name = proc["name"] if proc else "Audit Process"

st.title("🗄️ Centralized Data Storage")
st.caption("Permanent unified storage repository preserving all copies of audio/video recordings, auditee source documents, generated deliverables, and scoping question packs.")

stats = get_storage_stats()

# Storage Configuration Banner
with st.container(border=True):
    c_hdr1, c_hdr2 = st.columns([3, 1])
    with c_hdr1:
        st.markdown(f"**Centralized Storage Directory:** `{stats['root_path']}`")
        st.caption("Configured via `STORAGE_DIR` environment variable. Automatically persists across runs and mounts to persistent disk on deployment.")
    with c_hdr2:
        st.markdown("<span style='color: #10b981; font-weight: bold;'>● Online & Synchronized</span>", unsafe_allow_html=True)
        st.caption("Tamper-evident SHA-256 tracking active.")

# Overview Metrics
m1, m2, m3, m4, m5 = st.columns(5)
with m1:
    st.metric("Total Files Stored", stats["total_files"])
with m2:
    st.metric("Storage Consumed", f"{stats['total_mb']} MB")
with m3:
    st.metric("🎙️ Recordings", stats["category_counts"].get("recordings", 0))
with m4:
    st.metric("📄 Source Documents", stats["category_counts"].get("source_documents", 0))
with m5:
    st.metric("📊 Generated & Packs", stats["category_counts"].get("generated_documents", 0) + stats["category_counts"].get("question_packs", 0))

st.divider()

# Navigation Tabs
tab_browse, tab_upload, tab_config = st.tabs([
    "📂 Centralized File Explorer",
    "📤 Upload Directly to Storage",
    "⚙️ Storage Settings & Architecture"
])

with tab_browse:
    c_f1, c_f2, c_f3 = st.columns([1.5, 1.5, 2])
    with c_f1:
        cat_filter = st.selectbox(
            "Filter by Category:",
            ["all", "recordings", "source_documents", "generated_documents", "question_packs"],
            format_func=lambda x: {
                "all": "All Categories (Unified)",
                "recordings": "🎙️ Recordings (Walkthrough Audio/Video)",
                "source_documents": "📄 Source Documents (SOPs, Policies)",
                "generated_documents": "📊 Generated Documents (Reports & Deliverables)",
                "question_packs": "📋 Question Packs (Bilingual Scope Packs)"
            }.get(x, x)
        )
    with c_f2:
        proc_filter = st.selectbox(
            "Filter by Process:",
            [0, process_id],
            format_func=lambda x: "All Processes" if x == 0 else f"Current: {proc_name}"
        )
    with c_f3:
        search_kw = st.text_input("Search files by name or hash:", placeholder="e.g. SOP, recording, .xlsx, .pdf")

    # Fetch matching files
    files = list_storage_files(
        category=cat_filter if cat_filter != "all" else None,
        process_id=proc_filter if proc_filter != 0 else None
    )

    if search_kw:
        kw = search_kw.lower()
        files = [f for f in files if kw in f["filename"].lower() or kw in f.get("sha256", "").lower()]

    if not files:
        st.info("No files found in the centralized storage matching your selected filter. Upload a recording, ingest a document, or generate deliverables to populate storage.")
    else:
        st.write(f"Displaying **{len(files)}** stored file(s):")

        for f in files:
            cat_icon = {
                "recordings": "🎙️",
                "source_documents": "📄",
                "generated_documents": "📊",
                "question_packs": "📋"
            }.get(f.get("category"), "📁")

            size_kb = round(f.get("size_bytes", 0) / 1024, 1)
            date_str = str(f.get("created_at", ""))[:16]

            with st.expander(f"{cat_icon} [{f.get('category', 'general').upper()}] {f['filename']} ({size_kb} KB) – {date_str}"):
                c_d1, c_d2 = st.columns([2.5, 1.5])
                with c_d1:
                    st.write(f"**Path in Central Storage:** `{f.get('storage_path') or 'N/A'}`")
                    st.write(f"**Process:** {f.get('process_name') or 'General / Cross-Process'}")
                    st.write(f"**Uploader / Creator:** `{f.get('creator_name') or 'System'}`")
                    st.write(f"**MIME Type:** `{f.get('mime_type')}` | **Size:** {f.get('size_bytes', 0):,} bytes")
                    st.caption(f"🔒 **SHA-256 Integrity Checksum:** `{f.get('sha256')}`")

                with c_d2:
                    # Download button
                    file_obj = get_file(f["id"])
                    if file_obj and file_obj.get("data"):
                        st.download_button(
                            label=f"📥 Download {f['filename']}",
                            data=file_obj["data"],
                            file_name=f["filename"],
                            mime=f.get("mime_type", "application/octet-stream"),
                            key=f"dl_file_{f['id']}",
                            use_container_width=True
                        )

                        # Delete button
                        if st.button("🗑️ Delete from Storage", key=f"del_file_{f['id']}", use_container_width=True):
                            delete_file(f["id"])
                            st.warning(f"File {f['filename']} removed from centralized storage.")
                            st.rerun()

                # In-browser preview
                st.divider()
                st.markdown("**Preview & Inspection:**")
                if file_obj and file_obj.get("data"):
                    m_type = f.get("mime_type", "").lower()
                    data_bytes = file_obj["data"]

                    if "audio" in m_type or f["filename"].endswith((".wav", ".mp3", ".ogg", ".m4a")):
                        st.audio(data_bytes)
                    elif "text" in m_type or f["filename"].endswith((".txt", ".md", ".json", ".csv", ".xml", ".bpmn")):
                        try:
                            preview_text = data_bytes.decode("utf-8", errors="replace")
                            st.code(preview_text[:2000], language="json" if ".json" in f["filename"] else "markdown")
                        except Exception:
                            st.caption("Binary preview not available.")
                    else:
                        st.caption(f"Binary file ({m_type}). Click 'Download' above to inspect locally.")

with tab_upload:
    st.subheader("📤 Direct Ingestion into Centralized Storage")
    st.caption("Upload files directly to archive them in the centralized repository under any category.")

    up_col1, up_col2 = st.columns([1, 1])
    with up_col1:
        direct_file = st.file_uploader("Select File to Store", type=["wav", "mp3", "m4a", "mp4", "pdf", "docx", "xlsx", "txt", "json", "csv", "xml", "bpmn"])
        up_category = st.selectbox(
            "Target Storage Category",
            ["recordings", "source_documents", "generated_documents", "question_packs"],
            format_func=lambda x: {
                "recordings": "🎙️ Recordings (Walkthrough Audio/Video)",
                "source_documents": "📄 Source Documents (SOPs, Policies)",
                "generated_documents": "📊 Generated Documents (Audit Reports & Models)",
                "question_packs": "📋 Question Packs (Scoping Packages)"
            }.get(x, x)
        )
        custom_name = st.text_input("Custom Filename (optional)", placeholder="Leave blank to use original filename")

    with up_col2:
        st.markdown("#### Destination Preview")
        target_name = custom_name.strip() if custom_name else (direct_file.name if direct_file else "filename")
        st.write(f"📁 **Root Folder:** `{stats['root_path']}`")
        st.write(f"📂 **Subfolder:** `{up_category}/process_{process_id}/`")
        st.write(f"📄 **Target File:** `{target_name}`")

        if direct_file and st.button("🚀 Upload & Archive into Centralized Storage", type="primary"):
            file_data = direct_file.read()
            final_name = custom_name.strip() or direct_file.name
            fid = save_file(
                filename=final_name,
                mime_type=direct_file.type or "application/octet-stream",
                data=file_data,
                category=up_category,
                process_id=process_id,
                created_by=user["id"]
            )
            st.success(f"✅ Successfully archived `{final_name}` into Centralized Data Storage (File ID #{fid})!")
            st.rerun()

with tab_config:
    st.subheader("⚙️ Centralized Storage Architecture & Render Configuration")
    st.markdown("""
    FieldAI features a unified storage architecture designed for both local developer environments and persistent cloud disks on Render.
    
    ### 📂 Folder Hierarchy
    ```text
    <STORAGE_DIR>/
    ├── recordings/                  # Audio & video walkthrough recordings
    │   └── process_<id>/            # Isolated per audit process
    │       └── 20261003_120000_sample_p2p_walkthrough.wav
    ├── source_documents/            # SOPs, policies, manuals, auditee files
    │   └── process_<id>/
    │       └── 20261003_120500_SOP-FIN-04_Procure_to_Pay.txt
    ├── generated_documents/         # Auto-generated deliverables, Excel RCM, Word memos, PDFs, BPMN
    │   └── process_<id>/
    │       └── 20261003_121000_P2P_RCM_v1.1.xlsx
    └── question_packs/              # Centralized bilingual question packs & scoping JSON/CSV
        └── process_<id>/
            └── 20261003_121500_question_pack_p1_v1.1.json
    ```

    ### 🚀 Deploying with Persistent Storage on Render
    To retain recordings and source documents permanently across container restarts on Render:
    1. Attach a **Render Persistent Disk** to the `fieldai-web` service (e.g., Mount Path: `/var/data/fieldai_storage`).
    2. Add the environment variable in your Render Dashboard:
       ```env
       STORAGE_DIR=/var/data/fieldai_storage
       ```
    3. FieldAI will automatically detect the mounted disk and initialize the subfolders.
    """)
