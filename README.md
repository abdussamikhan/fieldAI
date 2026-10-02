# 🛡️ FieldAI – Multi-Agent AI Audit Fieldwork Assistant

**FieldAI** turns walkthrough interview recordings, policy documents (SOPs), and transaction datasets into a fully linked, versioned set of internal audit fieldwork workpapers:

1. **Capture & Transcription** – Browser audio recording (`st.audio_input`) or file upload with mandatory consent, ElevenLabs Scribe diarization (speakers & timestamps), and near-live interview co-pilot.
2. **Master Model & Flowchart** – Sequential process table, multi-lane swim lanes (Role, Department, or System) in Graphviz, BPMN 2.0 XML, and draw.io XML with risk (`R-xx`) and control (`C-xx`) badges.
3. **Risk-Control Matrix (RCM)** – Control design adequacy rating, AI suggestions for unmitigated gaps, and mapping to frameworks (COSO 2013, COBIT 2019, ISO 27001:2022, NCA ECC, SAMA CSF).
4. **Audit Program** – Test of Design & Operating Effectiveness procedures, deterministic sample sizes from frequency-based sampling tables, and linked PBC evidence.
5. **Multi-Meeting & Documents** – Entity resolution diffing against the master model to produce change sets (v1.0 → v1.1) and 5-category said-vs-documented SOP reconciliation.
6. **Advanced Fieldwork Analytics** – Fixed unit-tested pandas algorithms (duplicate payments, split purchases, weekend postings, Benford's 1st digit, 3-way match exceptions), SoD toxic combinations, ERP event-log process mining, and continuous monitoring via Render cron jobs.
7. **Findings & CAE Dashboard** – 5 Cs audit findings draft, IIA Standards 2024 compliance review checklist, and executive risk heat maps.

---

## 🏛️ System Architecture

```text
fieldai/
├── app.py                         # Streamlit entry point (login, navigation, Ask FieldAI)
├── pages/                         # 14 Streamlit pages
│   ├── 1_Engagements.py           # Engagement and process switcher / creator
│   ├── 2_Capture.py               # Audio capture, consent gate, speaker mapping, co-pilot
│   ├── 3_Review_Changes.py        # Tracked-changes review, conflict resolver, version bump
│   ├── 4_Process_Table.py         # Editable process table with source locators
│   ├── 5_Flowchart.py             # Interactive Graphviz swim lanes & diagram exports
│   ├── 6_RCM.py                   # Risk-Control Matrix, adequacy rating, framework mapping
│   ├── 7_Audit_Program.py         # Audit tests, deterministic sampling, manager lock
│   ├── 8_Documents.py             # SOP ingestion, 5-category reconciliation, doc Q&A
│   ├── 9_Prep.py                  # Bilingual walkthrough question pack & scoping
│   ├── 10_Testing.py              # Analytics tests, SoD, process mining, evidence reader
│   ├── 11_Findings.py             # Draft 5 Cs findings, IIA methodology QA review
│   ├── 12_Dashboard.py            # CAE executive coverage & exception dashboard
│   ├── 13_Confirm.py              # Auditee confirmation portal & feedback
│   └── 14_Admin.py                # Users, libraries, AI settings, append-only audit trail
├── agents/                        # 21 agents, one file each (LangGraph nodes)
│   ├── transcription_agent.py
│   ├── summary_agent.py
│   ├── process_extraction_agent.py
│   ├── risk_control_agent.py
│   ├── change_set_agent.py
│   ├── document_agent.py
│   ├── reconciliation_agent.py
│   ├── flowchart_agent.py
│   ├── rcm_agent.py
│   ├── audit_program_agent.py
│   ├── prep_agent.py
│   ├── copilot_agent.py
│   ├── knowledge_agent.py
│   ├── doc_qa_agent.py
│   ├── analytics_agent.py
│   ├── evidence_agent.py
│   ├── sod_agent.py
│   ├── process_mining_agent.py
│   ├── monitoring_agent.py
│   ├── findings_agent.py
│   └── qa_review_agent.py
├── graphs/                        # LangGraph StateGraph orchestration
│   ├── state.py                   # FieldAIState TypedDict
│   ├── orchestrator.py            # Supervisor router & intent classifier
│   ├── meeting_graph.py           # Core meeting walkthrough pipeline
│   ├── document_graph.py          # Document parsing & reconciliation pipeline
│   ├── deliverables_graph.py      # Flowchart & RCM rebuild pipeline
│   ├── prep_graph.py              # Preparation & near-live co-pilot
│   ├── testing_graph.py           # Fieldwork test execution pipeline
│   └── reporting_graph.py         # Findings & QA review pipeline
├── core/                          # Foundation utilities
│   ├── config.py                  # Environment config
│   ├── schemas.py                 # Pydantic models
│   ├── db.py                      # PostgreSQL (Render) & SQLite dev connector
│   ├── auth.py                    # Bcrypt auth & role-based access control
│   ├── storage.py                 # Binary file storage (BYTEA) with SHA256
│   ├── jobs.py                    # Background job queue runner
│   ├── audit_log.py               # Append-only audit trail
│   ├── llm.py                     # DeepSeek client with JSON mode & retry
│   ├── stt.py                     # ElevenLabs Scribe STT with OpenAI fallback
│   └── model_repo.py              # Master model code allocation & versioning
├── analytics/library.py           # 9 fixed pandas analytics tests
├── exports/                       # Excel (.xlsx), Word (.docx), PDF, BPMN, draw.io
├── db/                            # schema.sql and seed.sql
├── jobs/run_monitoring.py         # Scheduled recurring monitoring cron script
├── sample_data/                   # Realistic sample P2P files for immediate testing
├── tests/                         # Pytest test suite (12 unit tests passing)
├── worker.py                      # Background worker service
├── Dockerfile                     # Container definition (Graphviz, Tesseract OCR, ffmpeg)
├── render.yaml                    # Render Blueprint (DB, Web, Worker, Cron, Secrets)
└── requirements.txt               # Dependencies
```

---

## 🚀 Quick Start (Local Development)

### 1. Clone & Setup Environment
```bash
cd c:\projects\fieldai
python -m venv venv
# Windows:
.\venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

pip install -r requirements.txt
```

### 2. Configure Environment (`.env`)
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Default configuration uses local SQLite (`fieldai.db`) and automatically seeds all standard risk/control libraries and default admin user.

### 3. Run the Unit Test Suite
```bash
python -m pytest tests/
```
All 12 unit tests will execute and validate analytics, schema integrity, and model repository operations.

### 4. Launch Streamlit UI
```bash
streamlit run app.py
```
Open your browser at `http://localhost:8501`.
- **Default Username:** `admin`
- **Default Password:** `admin123`

---

## ☁️ Production Deployment on Render

FieldAI is designed for **one-click deployment on Render** using `render.yaml` (Render Blueprint).

### Step-by-Step Render Deployment Guide

1. **Create Accounts:**
   - [GitHub](https://github.com)
   - [Render](https://render.com)
   - [DeepSeek Platform](https://platform.deepseek.com) (for `DEEPSEEK_API_KEY`)
   - [ElevenLabs](https://elevenlabs.io) (for `ELEVENLABS_API_KEY`)

2. **Push Code to GitHub:**
   - Create a new private repository on GitHub (e.g. `fieldai`).
   - Push this codebase to GitHub:
     ```bash
     git add .
     git commit -m "Initial commit of FieldAI"
     git branch -M main
     git remote add origin https://github.com/your-username/fieldai.git
     git push -u origin main
     ```

3. **Deploy with Render Blueprint:**
   - Log into [Render Dashboard](https://dashboard.render.com).
   - Click **New +** → **Blueprint**.
   - Select your `fieldai` GitHub repository.
   - Render automatically parses `render.yaml` and sets up:
     - `fieldai-db`: PostgreSQL Database (starter plan)
     - `fieldai-web`: Streamlit Web Service (Docker container)
     - `fieldai-worker`: Background Worker (Docker container)
     - `fieldai-monitoring`: Weekly Cron Job (re-runs recurring controls)
     - `fieldai-secrets`: Environment Group
   - When prompted, provide your API keys:
     - `DEEPSEEK_API_KEY`: Your DeepSeek API key (`sk-...`)
     - `ELEVENLABS_API_KEY`: Your ElevenLabs API key
     - `ADMIN_PASSWORD`: A secure admin password for first login
   - Click **Apply**. Render will automatically build the Docker image, run migrations, seed reference data, and deploy the services.

4. **Access the App:**
   - Click on the `fieldai-web` service in Render.
   - Open its `.onrender.com` URL.
   - Log in with username `admin` and your chosen admin password.

---

## 🧪 Testing with Built-in Sample Data

The `sample_data/` folder provides realistic Procure-to-Pay (P2P) materials ready for testing:
1. **Walkthrough Audio / Transcript:** `sample_data/p2p_walkthrough_transcript.txt`
2. **SOP Document:** `sample_data/p2p_sop_procurement.txt`
3. **Transaction Extract:** `sample_data/invoices_extract.csv`
4. **User Access Matrix:** `sample_data/user_access_matrix.csv`
5. **ERP Event Log:** `sample_data/erp_event_log.csv`

In the Streamlit UI:
- Open **Capture** page and check *"load built-in sample Procure-to-Pay walkthrough audio"* to generate the baseline process table, flowchart, and RCM.
- Open **Documents** page and check *"load built-in sample P2P Procurement SOP"* to generate the 5-category reconciliation report.
- Open **Testing** page to run duplicate payment detection, SoD toxic role combinations, and ERP event-log process mining.
