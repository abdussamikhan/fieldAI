# FieldAI: Multi-Agent Architecture, Active Agent Tracking & Centralized Storage Reference

This reference document outlines the complete implementation of the **21-Agent Architecture**, the **Live Active Agent Tracking Engine**, **Deliverable Attribution Badges**, and the **Centralized Data Storage System** in FieldAI.

---

## 1. Centralized 21-Agent Registry Catalog

All agents are registered in [`core/agent_registry.py`](file:///c:/projects/fieldai/core/agent_registry.py) with standardized identifiers, roles, frameworks, and deliverable responsibilities:

| # | Agent Identifier | Display Title | Specialized Audit Role | Framework / Model | Produced Deliverables |
| :-: | :--- | :--- | :--- | :--- | :--- |
| **01** | `transcription_agent` | **Transcription & Diarization Agent** | Audio ingestion, timestamping & speaker turn diarization | Faster-Whisper / STT Engine | Verbatim timestamped transcripts, speaker maps |
| **02** | `summary_agent` | **Walkthrough Synthesis Agent** | Dialogue summarization & actionable item extraction | DeepSeek Audit Synthesis | Executive walkthrough summary, decisions, initial PBCs |
| **03** | `process_extraction_agent` | **Process Extraction Agent** | Sequential process step & decision gateway extraction | Structural Process Grammar | Master process table, step codes, responsible roles |
| **04** | `risk_control_agent` | **Risk & Control Mapping Agent** | Inherent risk identification & mitigating control mapping | COSO 2013 / NCA ECC / ISO 27001 | Inherent risk catalog, control activities, COSO mapping |
| **05** | `change_set_agent` | **Entity Resolution & Diff Agent** | Reconciliation against master model & version diffing | Deterministic Diff Engine | Formal change sets (Added/Changed/Removed), diff logs |
| **06** | `flowchart_agent` | **Flowchart & Swimlane Agent** | Multi-lane swimlane diagram synthesis | Graphviz DOT & BPMN 2.0 Engine | Interactive swimlanes, BPMN 2.0 XML, draw.io XML |
| **07** | `rcm_agent` | **RCM Compilation Agent** | Risk-Control Matrix & design adequacy evaluation | IIA Standards / COSO Principle 10 | RCM Matrix (Excel/Table), control design ratings |
| **08** | `audit_program_agent` | **Audit Program & Testing Agent** | Fieldwork testing procedures & sample size formulation | Deterministic Sampling Engine | Fieldwork Audit Program (ToD & ToE), sample sizes |
| **09** | `knowledge_agent` | **Audit Knowledge & Standards Agent** | Framework citations & benchmark RAG retrieval | IIA GIAS / COSO / SAMA CSF | Standards citations, benchmark control guidance |
| **10** | `document_agent` | **Document Ingestion Agent** | Auditee document parsing & text chunking | Document Parser & Chunking | Document chunks, metadata, documented controls |
| **11** | `reconciliation_agent` | **Said vs Documented Agent** | 5-category interview vs document gap reconciliation | Reconciliation Heuristics Engine | 5-Category gap report, SOP divergence flags |
| **12** | `doc_qa_agent` | **In-Document Grounded Q&A Agent** | Grounded inquiry answering with exact source citations | Grounded Citation Engine | Grounded audit answers, exact page/section citations |
| **13** | `prep_agent` | **Walkthrough Scoping & Prep Agent** | Pre-meeting scoping & bilingual question packs | DeepSeek Bilingual Audit Model | Bilingual question pack (EN/AR), scoping metrics |
| **14** | `copilot_agent` | **Live Interview Co-Pilot Agent** | Near-live interview prompt & evidence suggestions | Real-Time Interview Prompt Engine | Follow-up prompts, missing control checklist |
| **15** | `analytics_agent` | **Audit Analytics & Logic Agent** | Deterministic full-population data analytics tests | Pandas & Python Audit Logic | Duplicate payments, split POs, Benford's law |
| **16** | `sod_agent` | **Segregation of Duties (SoD) Agent** | Incompatible ERP permission conflict detection | SoD Conflict Matrix Engine | SoD toxic pair violations, user conflict scores |
| **17** | `process_mining_agent` | **Process Mining Agent** | Event log path conformance & control bypass detection | Event Conformance Engine | Variant analysis, happy path deviation ratios |
| **18** | `evidence_agent` | **Evidence Reading Agent** | Sample voucher & document attribute validation | OCR Attribute Matcher | Sample voucher verification, sign-off validation |
| **19** | `findings_agent` | **Findings Formulation Agent** | Standard 5 Cs audit observations formulation | IIA 5 Cs Audit Standards | Structured 5 Cs findings, remediation advice |
| **20** | `qa_review_agent` | **Independent QA Review Agent** | Methodology quality assurance & completeness audit | IIA Quality Assessment Framework | Working paper review notes, compliance checklists |
| **21** | `monitoring_agent` | **CAE Monitoring Agent** | Executive heat maps & real-time audit telemetry | Executive Analytics Engine | CAE heat maps, continuous telemetry feeds |

---

## 2. Real-Time "Active Agent" Execution Feedback

Whenever multi-agent pipelines run, FieldAI displays real-time execution banners informing the user which agent is currently working on screen:

### Walkthrough Ingestion Pipeline ([`pages/2_Meeting_Capture.py`](file:///c:/projects/fieldai/pages/2_Meeting_Capture.py))
When **"🚀 Transcribe & Process Walkthrough"** is triggered, an expandable execution box displays the active agents in sequence:
1. `🎙️ Active Agent: transcription_agent` — Ingesting audio buffer and diarizing speaker turns
2. `📝 Active Agent: summary_agent` — Synthesizing walkthrough dialogue and extracting PBC items
3. `⚙️ Active Agent: process_extraction_agent` — Parsing chronological process steps & gateways
4. `🛡️ Active Agent: risk_control_agent` — Mapping inherent risks & identifying mitigating controls
5. `⚖️ Active Agent: change_set_agent` — Performing entity resolution against master process model

### Document Ingestion & Gap Reconciliation ([`pages/8_RAG_Documents.py`](file:///c:/projects/fieldai/pages/8_RAG_Documents.py))
When **"Parse Document & Run Reconciliation"** is clicked:
1. `📄 Active Agent: document_agent` — Ingesting document text, parsing sections, and registering chunks
2. `⚖️ Active Agent: reconciliation_agent` — Reconciling interview testimonies against documented policy criteria

### Walkthrough Preparation & Scoping ([`pages/9_Preparation_&_Scoping.py`](file:///c:/projects/fieldai/pages/9_Preparation_&_Scoping.py))
When **"⚡ Generate Bilingual Walkthrough Question Pack"** is clicked:
- `📋 Active Agent: prep_agent` — Analyzing prior open items, risk library, and formulating bilingual questions

### Continuous Testing Hub ([`pages/10_Testing_&_Analytics.py`](file:///c:/projects/fieldai/pages/10_Testing_&_Analytics.py))
During execution of testing procedures:
- `📈 Active Agent: analytics_agent` — Executing algorithm on full transaction dataset
- `🛡️ Active Agent: sod_agent` — Evaluating user privilege matrix against toxic SoD rule catalog
- `🔄 Active Agent: process_mining_agent` — Reconstructing transaction pathways and identifying bypasses
- `📑 Active Agent: evidence_agent` — Evaluating voucher attributes against audit criteria

### Findings Formulation & QA Review ([`pages/11_Findings_&_QA.py`](file:///c:/projects/fieldai/pages/11_Findings_&_QA.py))
- `⚠️ Active Agent: findings_agent` — Compiling test exceptions into formal 5 Cs findings
- `🎯 Active Agent: qa_review_agent` — Evaluating file completeness against IIA QA standards

---

## 3. Deliverable Attribution Badges Across Screens

Every screen delivering an audit artifact prominently displays a standardized attribution badge via `render_deliverable_attribution()`:

| Screen / Page | Artifact Displayed | Attributed Agent(s) |
| :--- | :--- | :--- |
| **`pages/2_Meeting_Capture.py`** | Interview Transcripts & Diarization | `transcription_agent` |
| **`pages/2_Meeting_Capture.py`** | Live Co-Pilot Interview Prompts | `copilot_agent` |
| **`pages/3_Review_Changes.py`** | Master Model Change Set & Entity Resolution | `change_set_agent` |
| **`pages/4_Process_Table.py`** | Sequential Process Steps & Role Allocation | `process_extraction_agent` |
| **`pages/5_Flowchart.py`** | Multi-Lane Swimlane Diagram & BPMN Deliverables | `flowchart_agent` |
| **`pages/6_RCM.py`** | Risk & Control Matrix & Design Adequacy Ratings | `rcm_agent` & `risk_control_agent` |
| **`pages/7_Audit_Program.py`** | Fieldwork Audit Program & Sample Sizes | `audit_program_agent` |
| **`pages/8_RAG_Documents.py`** | Said vs Documented 5-Category Gap Analysis | `reconciliation_agent` & `document_agent` |
| **`pages/8_RAG_Documents.py`** | Grounded In-Document Answers & Citations | `doc_qa_agent` |
| **`pages/9_Preparation_&_Scoping.py`** | Bilingual Walkthrough Question Pack & Scoping | `prep_agent` |
| **`pages/10_Testing_&_Analytics.py`** | Data Analytics / SoD / Process Mining Exceptions | `analytics_agent` / `sod_agent` / `process_mining_agent` |
| **`pages/11_Findings_&_QA.py`** | Structured 5 Cs Audit Observations | `findings_agent` |
| **`pages/11_Findings_&_QA.py`** | IIA Methodology Quality Assurance Review | `qa_review_agent` |
| **`pages/12_CAE_Dashboard.py`** | Executive Audit Telemetry & Heat Map Metrics | `monitoring_agent` |

---

## 4. Centralized Data Storage Architecture

All media recordings, uploaded source documents, generated deliverables, and question packs are saved both to the database and physical directory structure.

### Storage Directory Structure
Configurable via the `STORAGE_DIR` environment variable (defaults to `<project_root>/data_storage` or mounted persistent disk):

```text
data_storage/
├── recordings/                     # 🎙️ Audio and video walkthrough recordings
│   └── process_<id>/               # Isolated per audit process
│       └── 20261003_120000_sample_p2p_walkthrough.wav
├── source_documents/               # 📄 Auditee SOPs, policies, manuals, evidence files
│   └── process_<id>/
│       └── 20261003_120500_SOP-FIN-04_Procure_to_Pay.txt
├── generated_documents/            # 📊 Generated deliverables (Excel RCM, Word memos, PDFs, BPMN)
│   └── process_<id>/
│       ├── 20261003_121000_P2P_RCM_v1.1.xlsx
│       ├── 20261003_121200_P2P_Audit_Program_v1.0.xlsx
│       ├── 20261003_121400_P2P_Findings.docx
│       ├── 20261003_121600_P2P_Summary.pdf
│       ├── 20261003_121800_P2P_flow.bpmn
│       └── 20261003_122000_P2P_flow.drawio
└── question_packs/                 # 📋 Bilingual walkthrough interview packs & scoping records
    └── process_<id>/
        └── 20261003_122500_question_pack_p1_v1.1.json
```

### Storage Core API ([`core/storage.py`](file:///c:/projects/fieldai/core/storage.py))
- `get_storage_root() -> Path`: Resolves storage root and ensures category subdirectories exist.
- `save_file(filename, mime_type, data, category, process_id, created_by) -> int`:
  - Saves binary file to `STORAGE_DIR/<category>/process_<id>/<timestamp>_<filename>`.
  - Computes cryptographic SHA-256 hash for tamper evidence.
  - Inserts entry into `files` database table.
  - Writes audit log record.
  - Returns `file_id`.
- `save_generated_document(filename, mime_type, data, process_id, created_by) -> int`: Shortcut for archiving deliverables.
- `get_file(file_id: int) -> Dict[str, Any]`: Retrieves file metadata and content (reads from disk, falls back to DB blob).
- `list_storage_files(category, process_id) -> List[Dict]`: Lists all stored files with disk status and metadata.
- `get_storage_stats() -> Dict`: Computes total files, disk volume in MB, and category breakdown.

---

## 5. Centralized Data Storage Explorer ([`pages/15_Centralized_Storage.py`](file:///c:/projects/fieldai/pages/15_Centralized_Storage.py))

A dedicated explorer page provides complete transparency and management of stored files:
1. **Overview Metrics**: Total files, storage volume in MB, breakdown by category.
2. **Category Filter**: Unified view or filtered by `Recordings`, `Source Documents`, `Generated Documents`, `Question Packs`.
3. **In-Browser Preview**:
   - Audio playback for recordings
   - Text/JSON/Markdown syntax viewer for documents, XML schemas, and question packs
4. **Audit Evidence Verification**: SHA-256 checksums displayed for every file to verify audit trail integrity.
5. **Direct Ingestion Tab**: Upload files directly into any category.

---

## 6. Centralized Storage for Question Packs ([`core/prep_repo.py`](file:///c:/projects/fieldai/core/prep_repo.py))

Question packs are permanently persisted into the database and filesystem:
- **Database Table**: `question_packs` (`id`, `process_id`, `title`, `scoping_json`, `questions_json`, `version`, `created_by`, `created_at`).
- **Filesystem Mirror**: Permanent JSON archive in `data_storage/question_packs/process_<id>/`.
- **Management Tab in `pages/9_Prep.py`**:
  - Browse, preview, and load saved packs into active sessions.
  - Export packs as JSON or CSV spreadsheets.

---

## 7. Render Deployment & Persistent Storage

To retain stored files permanently across deployments on Render:
1. In the **Render Dashboard**, open your web service (`fieldai-web`).
2. Navigate to **Disks** → **Add Disk** with **Mount Path** set to `/var/data/fieldai_storage`.
3. In the **Environment** tab, set:
   ```env
   STORAGE_DIR=/var/data/fieldai_storage
   ```
4. FieldAI will automatically use the persistent disk for all recordings, documents, and deliverables.
