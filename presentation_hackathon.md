---
marp: true
theme: default
paginate: true
header: "FieldAI | Hackathon Pitch"
footer: "Sami Associates · FieldAI Multi-Agent Fieldwork Assistant"
backgroundColor: #0f172a
color: #f8fafc
style: |
  section {
    font-family: 'Inter', sans-serif;
    padding: 40px 60px;
    background: radial-gradient(circle at top right, #1e293b 0%, #0f172a 100%);
    color: #f8fafc;
  }
  h1 {
    color: #38bdf8;
    font-size: 2.2em;
    margin-bottom: 0.2em;
  }
  h2 {
    color: #38bdf8;
    font-size: 1.6em;
    border-bottom: 2px solid #38bdf8;
    padding-bottom: 8px;
    margin-bottom: 20px;
  }
  h3 {
    color: #94a3b8;
    font-size: 1.1em;
  }
  strong {
    color: #38bdf8;
  }
  .highlight {
    background-color: rgba(56, 189, 248, 0.12);
    border-left: 4px solid #38bdf8;
    padding: 12px 16px;
    border-radius: 4px;
    margin-top: 15px;
  }
  .grid-2 {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 24px;
  }
  .card {
    background: rgba(30, 41, 59, 0.7);
    border: 1px solid #334155;
    border-radius: 8px;
    padding: 16px;
  }
  ul {
    font-size: 0.95em;
    line-height: 1.5;
  }
  footer {
    font-size: 0.55em;
    color: #64748b;
  }
---

<!-- _class: lead -->
<!-- _paginate: false -->

# FieldAI
### Autonomous Multi-Agent Fieldwork & Process Intelligence
**Hackathon Project Presentation**

*Turning Hours of Messy Walkthrough Interviews & SOPs into Verifiable Audit Workpapers in Minutes*

Presented by: **Sami Associates**

<!--
Presenter Notes:
- Hook the audience: Every company undergoes audits, but the fieldwork process is stuck in the 1990s.
- Today we're showing FieldAI: an autonomous multi-agent system that solves this with real-time AI agents.
-->

---

## The Problem: The Fieldwork Bottleneck

Auditing complex operational processes is notoriously manual and error-prone:

<div class="grid-2">
<div class="card">

### ⏳ 50%+ Fieldwork Time Wasted
* Auditors spend days manually transcribing audio walkthroughs.
* Re-typing step narratives, drawing Visio flowcharts, and compiling RCMs.
</div>

<div class="card">

### 🧩 The "Say vs. Do" Gap
* What employees **say** in interviews frequently contradicts written **SOPs**.
* Identifying hidden divergence is manually exhausting and often missed.
</div>
</div>

<div class="highlight">
<strong>The Broken Link:</strong> In traditional audit files, findings lack direct, verifiable citations back to exact spoken audio timestamps or policy clauses.
</div>

<!--
Presenter Notes:
- Auditors aren't spending time analyzing risks; they're spending it formatting tables and transcribing audio.
- The biggest audit risks hide in operational divergence: what staff actually do vs what the manual says.
-->

---

## The Solution: Meet FieldAI

**FieldAI** is an end-to-end multi-agent assistant built for enterprise audit fieldwork.

* **🎙️ Walkthrough Ingestion:** Upload multi-speaker audio recordings; extracts speech with speaker diarization & exact timestamps.
* **📄 Procedural Intelligence:** Ingests PDFs, Word manuals, and SOPs; parses hierarchical clauses automatically.
* **🔍 Divergence & Gap Engine:** Reconciles interview transcripts against written policies across 5 discrepancy categories.
* **⚡ One-Click Workpaper Synthesis:** Generates standardized Process Tables, Mermaid Flowcharts, RCMs, and Audit Programs with 100% source citations.

<!--
Presenter Notes:
- FieldAI doesn't just summarize text. It behaves like a senior audit team.
- Everything is bi-directionally linked to ground truth for compliance.
-->

---

## System Architecture: 21 Collaborative Agents

Powered by **LangGraph StateGraph** across 6 specialized sub-graphs:

```
[Audio Walkthrough + SOP Documents]
               │
               ▼
┌────────────────────────────────────────────────────────┐
│  Orchestrator Agent (Master Control & Routing)        │
└──────────────┬─────────────────────────┬───────────────┘
               ▼                         ▼
   ┌───────────────────────┐ ┌───────────────────────┐
   │ Transcription & Diar. │ │ Document QA & Clause  │
   │ (ElevenLabs + Agent)  │ │ Extractor Agents      │
   └───────────┬───────────┘ └───────────┬───────────┘
               └──────────────┬──────────┘
                              ▼
   ┌─────────────────────────────────────────────────┐
   │ Gap & Divergence Detection Agent                │
   │ (Say vs. Do Operational Reconciliation)         │
   └──────────────────────────┬──────────────────────┘
                              ▼
   ┌─────────────────────────────────────────────────┐
   │ Deliverables: Process Flow · RCM · Audit Tests  │
   └─────────────────────────────────────────────────┘
```

<!--
Presenter Notes:
- Instead of one monolithic prompt, we split the workflow into 21 focused micro-agents.
- Each agent has strict schemas, deterministic validation, and human-in-the-loop review checkpoints.
-->

---

## Live Workflow: From Raw Input to RCM

<div class="grid-2">
<div class="card">

### 1. Ingest & Transcribe
* Records interview (P2P, Payroll, Inventory).
* Audio diarized and tagged with timestamps (`[04:12]`).

### 2. Extract & Compare
* SOP clauses extracted into JSON nodes.
* Compares spoken steps vs. policy rules.
</div>

<div class="card">

### 3. Generate Workpapers
* **Flowchart:** Mermaid visual of actual vs expected flow.
* **RCM:** Auto-maps Risks (R-01) to Controls (C-01).

### 4. Continuous Analytics
* Runs deterministic analytics: duplicate payments, split POs, & toxic SoD role conflicts.
</div>
</div>

<!--
Presenter Notes:
- Walk through a 30-second user journey:
  Upload 1 interview + 1 SOP PDF -> Press Generate -> Inspect RCM and instant flag on split POs under approval limit.
-->

---

## Tech Stack & Engineering Highlights

Designed for security, determinism, and production scale:

* **Orchestration:** LangGraph (StateGraph multi-agent acyclic routing)
* **Frontend:** Streamlit 15-page interactive auditor workstation
* **Speech Intelligence:** ElevenLabs Scribe API (Speaker diarization & timestamping)
* **LLM Engine:** DeepSeek Flash (fast, deterministic reasoning & structured outputs)
* **Database & Jobs:** PostgreSQL with asynchronous task queues & state snapshots
* **Analytics Engine:** Native Pandas / SQL substantive audit tests (SoD & AP testing)

<div class="highlight">
<strong>Enterprise Ready:</strong> Containerized via Docker with local & cloud deployment support on Render.
</div>

<!--
Presenter Notes:
- We chose LangGraph because auditing requires deterministic state machines and rollback capability.
- ElevenLabs handles noisy audio, while DeepSeek generates strictly typed JSON for the RCM.
-->

---

## Impact & What's Next

<div class="grid-2">
<div class="card">

### 🏆 Hackathon Results
* **> 50% Cycle Time Reduction:** Eliminates 3–5 days of administrative documentation per audit.
* **Zero Guesswork:** 100% of generated test steps link back to source audio or text.
* **Instant Gap Discovery:** Uncovers unwritten workarounds in minutes.
</div>

<div class="card">

### 🚀 Future Roadmap
* **Offline-First Sync:** Support fieldwork in remote client sites without internet.
* **Live Voice Co-Pilot:** Real-time interview probing questions during active walkthroughs.
* **ERP Connectors:** Direct API ingest from SAP / NetSuite logs.
</div>
</div>

---

<!-- _class: lead -->

# Thank You! 🎯
### FieldAI: Reimagining Audit Fieldwork with Multi-Agent AI

**Questions & Live Demo**

*Built by Sami Associates*
