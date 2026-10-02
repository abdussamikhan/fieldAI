import streamlit as st
from core.db import db
from core.storage import save_file
from core.jobs import enqueue_job
from core.audit_log import log_audit
from graphs.orchestrator import run_task

st.set_page_config(page_title="Meeting Capture · FieldAI", page_icon="🎙️", layout="wide")

if not st.session_state.get("user"):
    st.warning("Please sign in from the main page.")
    st.stop()

user = st.session_state.user
process_id = st.session_state.get("current_process_id", 1)
proc = db.fetch_one("SELECT * FROM processes WHERE id = %s;", (process_id,))

st.title("🎙️ Walkthrough Meeting Capture")
st.caption(f"Capture, transcribe, and extract audit workflows for **{proc['name'] if proc else 'Process'}** ({proc['current_version'] if proc else 'v1.0'})")

tab1, tab2, tab3 = st.tabs(["📁 Full Meeting Recording", "⚡ Near-Live Co-Pilot (Chunks)", "📝 Transcript & Speaker Mapping"])

with tab1:
    col1, col2 = st.columns([1.2, 1.8])

    with col1:
        st.subheader("1. Meeting Details & Consent")
        title = st.text_input("Meeting Title", value=f"Walkthrough Interview – {proc['name'] if proc else 'P2P'}")
        participants = st.text_area("Participants List", value="Sarah Jenkins (Operations), Tariq Mansoor (Procurement), Lead Auditor")
        lang = st.selectbox("Meeting Language", options=["auto", "en", "ar", "mixed"], index=0)

        st.markdown("#### 🔒 Legal & Audit Consent (FR-1.4)")
        st.info("Script to auditee: *'This walkthrough session is being recorded for the sole purpose of internal audit documentation. Do all participants grant consent?'*")
        consent = st.checkbox("✅ Explicit participant consent has been recorded and confirmed", value=True)

        if not consent:
            st.error("⚠️ Consent is mandatory per audit ethics policy. Transcription cannot proceed without consent.")

    with col2:
        st.subheader("2. Audio Input (Record or Upload)")
        rec_mode = st.radio("Capture Method", ["Upload Audio/Video File", "Record in Browser (st.audio_input)"], horizontal=True)

        audio_bytes = None
        filename = "meeting.wav"

        if rec_mode == "Upload Audio/Video File":
            uploaded_file = st.file_uploader("Upload audio/video recording (MP3, WAV, M4A, MP4)", type=["mp3", "wav", "m4a", "mp4", "ogg"])
            if uploaded_file:
                audio_bytes = uploaded_file.read()
                filename = uploaded_file.name
        else:
            rec_audio = st.audio_input("Record Walkthrough Interview")
            if rec_audio:
                audio_bytes = rec_audio.read()
                filename = "browser_recording.wav"

        # Option to load sample procure-to-pay recording if no file supplied
        if st.checkbox("Or load built-in sample Procure-to-Pay walkthrough audio"):
            sample_path = "sample_data/p2p_walkthrough_transcript.txt"
            audio_bytes = b"SAMPLE_AUDIO_DUMMY_FOR_STT"
            filename = "sample_p2p_walkthrough.wav"
            st.success("Sample audio buffer ready for transcription.")

        st.divider()

        can_start = bool(audio_bytes) and consent
        if st.button("🚀 Transcribe & Process Walkthrough", disabled=not can_start, type="primary", use_container_width=True):
            with st.spinner("Saving recording and running FieldAI Meeting Graph..."):
                # 1. Store audio file in centralized data storage and files table
                file_id = save_file(filename, "audio/wav", audio_bytes or b"", category="recordings", process_id=process_id, created_by=user["id"])
                
                # 2. Register source record
                source_id = db.execute_insert(
                    """
                    INSERT INTO sources (process_id, kind, title, storage_path, language, consent_recorded, participants, created_by)
                    VALUES (%s, 'meeting', %s, %s, %s, %s, %s, %s);
                    """,
                    (process_id, title, f"file:{file_id}", lang, consent, participants, user["id"])
                )

                # 3. Execute LangGraph meeting pipeline
                initial_state = {
                    "task": "process_meeting",
                    "process_id": process_id,
                    "engagement_id": proc.get("engagement_id", 1) if proc else 1,
                    "source_id": source_id,
                    "user_id": user["id"],
                    "language": lang
                }
                
                result = run_task("process_meeting", initial_state)
                st.session_state.current_source_id = source_id

                st.success("🎉 Meeting successfully processed! Master model, flowchart, and RCM updated.")
                st.balloons()
                st.rerun()

with tab2:
    st.subheader("⚡ Near-Live Walkthrough Co-Pilot (Options 3 & 4)")
    st.markdown("Record 2–5 minute chunks during live interviews to receive instant follow-up prompts and capture PBC evidence on the fly.")

    col_cp1, col_cp2 = st.columns([1.2, 1.8])
    with col_cp1:
        chunk_audio = st.audio_input("Record Live Interview Chunk")
        chunk_notes = st.text_area("Or type client verbal statement directly", placeholder="e.g. Auditee said: When SAP is down, we use manual paper slips...")
        submit_chunk = st.button("Analyze Chunk with Co-Pilot", type="primary")

    with col_cp2:
        if submit_chunk:
            with st.spinner("Co-Pilot analyzing live chunk..."):
                cp_res = run_task("copilot_chunk", {
                    "task": "copilot_chunk",
                    "process_id": process_id,
                    "user_id": user["id"],
                    "task_input": chunk_notes or "Auditee: When system is down, we use manual slips."
                })
                prompts = cp_res.get("copilot_prompts", [])
                pbc = cp_res.get("copilot_pbc", [])

                st.markdown("#### 💡 Immediate Follow-Up Questions:")
                for p in prompts:
                    st.warning(f"👉 **{p}**")

                if pbc:
                    st.markdown("#### 📋 Newly Identified Evidence to Request:")
                    for item in pbc:
                        st.info(f"📁 **{item.get('item')}** (Owner: {item.get('owner')}) – {item.get('reason')}")

with tab3:
    st.subheader("📝 Transcript Segments & Speaker Mapping")
    sources = db.fetch_all("SELECT * FROM sources WHERE process_id = %s AND kind = 'meeting' ORDER BY id DESC;", (process_id,))
    
    if sources:
        src_map = {s["id"]: f"{s['title']} ({s['created_at']})" for s in sources}
        active_src_id = st.selectbox("Select Meeting Recording", options=list(src_map.keys()), format_func=lambda x: src_map[x])
        
        segments = db.fetch_all("SELECT * FROM transcript_segments WHERE source_id = %s ORDER BY start_s ASC;", (active_src_id,))
        
        if segments:
            st.markdown(f"**Total Segments:** {len(segments)}")
            for seg in segments:
                col_s1, col_s2, col_s3 = st.columns([1.5, 3.5, 0.8])
                with col_s1:
                    speaker = seg.get("speaker_name") or seg.get("speaker_label", "Speaker")
                    min_t = int(seg.get("start_s", 0) // 60)
                    sec_t = int(seg.get("start_s", 0) % 60)
                    st.markdown(f"**{speaker}** `[{min_t:02d}:{sec_t:02d}]`")
                with col_s2:
                    st.write(seg["text"])
                with col_s3:
                    if st.button("Redact", key=f"red_{seg['id']}"):
                        db.execute("UPDATE transcript_segments SET text = '[REDACTED CONFIDENTIAL INFO]', redacted = TRUE WHERE id = %s;", (seg["id"],))
                        st.rerun()
        else:
            st.info("No transcript segments found for this meeting.")
    else:
        st.info("No recorded meetings uploaded yet.")
