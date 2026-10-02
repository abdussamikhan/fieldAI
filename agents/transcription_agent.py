import json
from typing import Dict, Any
from graphs.state import FieldAIState
from core.db import db
from core.storage import get_file
from core.stt import stt_client
from core.audit_log import log_audit

PROMPT_TRANSCRIPTION_REVIEW = """You are a senior audit assistant. Ensure speaker diarization and audio transcriptions are cleanly aligned with internal audit terminology."""

def run(state: FieldAIState) -> Dict[str, Any]:
    """
    Transcription Agent (FR-1.1-1.9):
    Transcribes audio meeting recording with speaker labels and timestamps.
    Blocks execution if participant consent is not recorded.
    """
    source_id = state.get("source_id")
    if not source_id:
        return {"errors": ["No source_id provided for transcription"]}

    source = db.fetch_one("SELECT * FROM sources WHERE id = %s;", (source_id,))
    if not source:
        return {"errors": [f"Source {source_id} not found in database"]}

    # FR-1.4: Refuse to run if consent_recorded is false
    if not source.get("consent_recorded"):
        return {"errors": ["Participant consent not recorded. Transcription blocked per audit policy."]}

    # Retrieve audio file
    storage_path = source.get("storage_path")
    file_id = None
    if storage_path and storage_path.startswith("file:"):
        try:
            file_id = int(storage_path.replace("file:", ""))
        except Exception:
            file_id = None

    audio_bytes = b""
    if file_id:
        f_record = get_file(file_id)
        if f_record and f_record.get("data"):
            audio_bytes = f_record["data"]

    lang_hint = source.get("language") or "auto"
    stt_res = stt_client.transcribe_audio(audio_bytes, filename=source.get("title", "meeting.wav"), language_hint=lang_hint)
    
    segments = stt_res.get("segments", [])
    detected_lang = stt_res.get("language", "en")

    # Clear previous segments if any
    db.execute("DELETE FROM transcript_segments WHERE source_id = %s;", (source_id,))

    # Insert into database
    for seg in segments:
        db.execute_insert(
            """
            INSERT INTO transcript_segments (source_id, speaker_label, speaker_name, start_s, end_s, text, redacted)
            VALUES (%s, %s, %s, %s, %s, %s, FALSE);
            """,
            (source_id, seg.get("speaker_label", "Speaker 1"), seg.get("speaker_name", ""), seg.get("start_s", 0.0), seg.get("end_s", 0.0), seg.get("text", ""))
        )

    # Update source language
    db.execute("UPDATE sources SET language = %s WHERE id = %s;", (detected_lang, source_id))
    log_audit(state.get("user_id"), "transcribe_meeting", "source", source_id, {"segments_count": len(segments)})

    return {
        "transcript": segments,
        "language": detected_lang
    }
