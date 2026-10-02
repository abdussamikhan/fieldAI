-- FieldAI Database Schema
-- Compatible with PostgreSQL (Render) and SQLite (Local development)

CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'Auditor', -- Auditor, Manager, Admin, Auditee
    active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS engagements (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    entity VARCHAR(255) NOT NULL,
    period VARCHAR(100) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'In Progress', -- In Progress, Completed, Archived
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS processes (
    id SERIAL PRIMARY KEY,
    engagement_id INTEGER NOT NULL REFERENCES engagements(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    code_prefix VARCHAR(50) NOT NULL DEFAULT 'P2P',
    current_version VARCHAR(20) NOT NULL DEFAULT 'v1.0',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS sources (
    id SERIAL PRIMARY KEY,
    process_id INTEGER NOT NULL REFERENCES processes(id) ON DELETE CASCADE,
    kind VARCHAR(50) NOT NULL, -- 'meeting', 'document'
    title VARCHAR(255) NOT NULL,
    storage_path VARCHAR(500),
    language VARCHAR(20) DEFAULT 'en', -- 'en', 'ar', 'mixed'
    consent_recorded BOOLEAN NOT NULL DEFAULT FALSE,
    participants TEXT,
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS transcript_segments (
    id SERIAL PRIMARY KEY,
    source_id INTEGER NOT NULL REFERENCES sources(id) ON DELETE CASCADE,
    speaker_label VARCHAR(100) DEFAULT 'Speaker 1',
    speaker_name VARCHAR(100),
    start_s REAL NOT NULL DEFAULT 0.0,
    end_s REAL NOT NULL DEFAULT 0.0,
    text TEXT NOT NULL,
    redacted BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS steps (
    id SERIAL PRIMARY KEY,
    process_id INTEGER NOT NULL REFERENCES processes(id) ON DELETE CASCADE,
    step_code VARCHAR(50) NOT NULL,
    order_num INTEGER NOT NULL DEFAULT 1,
    description TEXT NOT NULL,
    responsible_role VARCHAR(150),
    responsible_person VARCHAR(150),
    department VARCHAR(150),
    system VARCHAR(150),
    inputs TEXT,
    outputs TEXT,
    frequency VARCHAR(50),
    documents TEXT,
    is_decision BOOLEAN DEFAULT FALSE,
    confidence REAL DEFAULT 1.0,
    status VARCHAR(50) DEFAULT 'active', -- active, withdrawn
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS risks (
    id SERIAL PRIMARY KEY,
    process_id INTEGER NOT NULL REFERENCES processes(id) ON DELETE CASCADE,
    risk_code VARCHAR(50) NOT NULL,
    description TEXT NOT NULL,
    inherent_rating VARCHAR(50) DEFAULT 'Medium', -- High, Medium, Low
    ai_suggested BOOLEAN DEFAULT FALSE,
    library_ref VARCHAR(100),
    confidence REAL DEFAULT 1.0,
    status VARCHAR(50) DEFAULT 'active', -- active, withdrawn
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS controls (
    id SERIAL PRIMARY KEY,
    process_id INTEGER NOT NULL REFERENCES processes(id) ON DELETE CASCADE,
    control_code VARCHAR(50) NOT NULL,
    description TEXT NOT NULL,
    control_type VARCHAR(50) DEFAULT 'preventive', -- preventive, detective
    nature VARCHAR(50) DEFAULT 'automated', -- manual, automated, IT-dependent
    frequency VARCHAR(50) DEFAULT 'per transaction', -- annual, quarterly, monthly, weekly, daily, per transaction
    owner VARCHAR(150),
    key_control BOOLEAN DEFAULT TRUE,
    design_rating VARCHAR(50) DEFAULT 'Adequate', -- Adequate, Partially adequate, Inadequate
    criteria_ref TEXT,
    ai_suggested BOOLEAN DEFAULT FALSE,
    status VARCHAR(50) DEFAULT 'active', -- active, withdrawn
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS risk_control_links (
    risk_id INTEGER NOT NULL REFERENCES risks(id) ON DELETE CASCADE,
    control_id INTEGER NOT NULL REFERENCES controls(id) ON DELETE CASCADE,
    PRIMARY KEY (risk_id, control_id)
);

CREATE TABLE IF NOT EXISTS step_entity_links (
    step_id INTEGER NOT NULL REFERENCES steps(id) ON DELETE CASCADE,
    entity_type VARCHAR(20) NOT NULL, -- 'risk', 'control'
    entity_id INTEGER NOT NULL,
    PRIMARY KEY (step_id, entity_type, entity_id)
);

CREATE TABLE IF NOT EXISTS item_sources (
    id SERIAL PRIMARY KEY,
    entity VARCHAR(50) NOT NULL, -- 'step', 'risk', 'control'
    entity_id INTEGER NOT NULL,
    source_id INTEGER NOT NULL REFERENCES sources(id) ON DELETE CASCADE,
    locator VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS versions (
    id SERIAL PRIMARY KEY,
    process_id INTEGER NOT NULL REFERENCES processes(id) ON DELETE CASCADE,
    version_label VARCHAR(50) NOT NULL,
    snapshot_json TEXT NOT NULL,
    change_log TEXT,
    approved_by INTEGER REFERENCES users(id),
    approved_at TIMESTAMP,
    locked BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS change_sets (
    id SERIAL PRIMARY KEY,
    process_id INTEGER NOT NULL REFERENCES processes(id) ON DELETE CASCADE,
    source_id INTEGER REFERENCES sources(id) ON DELETE SET NULL,
    status VARCHAR(50) DEFAULT 'draft', -- draft, reviewed, applied
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS change_items (
    id SERIAL PRIMARY KEY,
    change_set_id INTEGER NOT NULL REFERENCES change_sets(id) ON DELETE CASCADE,
    entity VARCHAR(50) NOT NULL, -- step, risk, control, link
    action VARCHAR(50) NOT NULL, -- Added, Changed, Confirmed, Contradicted, Removed
    target_code VARCHAR(50),
    before_json TEXT,
    after_json TEXT,
    evidence_json TEXT,
    conflict_with TEXT,
    decision VARCHAR(50) DEFAULT 'pending', -- pending, accepted, rejected, edited
    resolution_note TEXT
);

CREATE TABLE IF NOT EXISTS open_items (
    id SERIAL PRIMARY KEY,
    process_id INTEGER NOT NULL REFERENCES processes(id) ON DELETE CASCADE,
    question TEXT NOT NULL,
    origin VARCHAR(100) DEFAULT 'Meeting Walkthrough',
    status VARCHAR(50) DEFAULT 'open', -- open, closed
    raised_in_source INTEGER REFERENCES sources(id) ON DELETE SET NULL,
    closed_in_source INTEGER REFERENCES sources(id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS pbc_requests (
    id SERIAL PRIMARY KEY,
    process_id INTEGER NOT NULL REFERENCES processes(id) ON DELETE CASCADE,
    item TEXT NOT NULL,
    owner VARCHAR(150),
    due_date VARCHAR(50),
    status VARCHAR(50) DEFAULT 'requested', -- requested, received, overdue
    linked_test_id INTEGER,
    document_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS documents (
    id SERIAL PRIMARY KEY,
    source_id INTEGER NOT NULL REFERENCES sources(id) ON DELETE CASCADE,
    doc_type VARCHAR(100) DEFAULT 'SOP', -- SOP, Policy, Manual, Org Chart, RCM
    owner VARCHAR(150),
    version VARCHAR(50) DEFAULT '1.0',
    effective_date VARCHAR(50),
    approval_status VARCHAR(50) DEFAULT 'Approved',
    received_on VARCHAR(50),
    outdated_flag BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS doc_chunks (
    id SERIAL PRIMARY KEY,
    document_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    page INTEGER DEFAULT 1,
    section VARCHAR(255),
    text TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS recon_items (
    id SERIAL PRIMARY KEY,
    process_id INTEGER NOT NULL REFERENCES processes(id) ON DELETE CASCADE,
    document_id INTEGER REFERENCES documents(id) ON DELETE SET NULL,
    category VARCHAR(100) NOT NULL, -- Matches, Documented-not-described, Described-not-documented, Conflicting detail, Outdated document
    item_code VARCHAR(50),
    doc_ref TEXT,
    meeting_ref TEXT,
    note TEXT,
    suggested_action TEXT,
    decision VARCHAR(50) DEFAULT 'pending', -- pending, accepted, rejected
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS tests (
    id SERIAL PRIMARY KEY,
    process_id INTEGER NOT NULL REFERENCES processes(id) ON DELETE CASCADE,
    test_code VARCHAR(50) NOT NULL,
    control_code VARCHAR(50) NOT NULL,
    objective TEXT NOT NULL,
    test_type VARCHAR(50) DEFAULT 'ToE', -- ToD, ToE, analytics
    procedure TEXT NOT NULL,
    sample_size INTEGER DEFAULT 25,
    sample_basis VARCHAR(255) DEFAULT 'Standard frequency-based table',
    evidence_pbc TEXT,
    attributes_json TEXT,
    performer VARCHAR(150),
    reviewer VARCHAR(150),
    wp_ref VARCHAR(100),
    result VARCHAR(50) DEFAULT 'Untested', -- Untested, Pass, Exception, Inconclusive
    exception_note TEXT,
    status VARCHAR(50) DEFAULT 'draft', -- draft, approved, locked
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS test_runs (
    id SERIAL PRIMARY KEY,
    test_id INTEGER NOT NULL REFERENCES tests(id) ON DELETE CASCADE,
    run_type VARCHAR(50) NOT NULL, -- analytics, sod, process_mining, evidence
    parameters_json TEXT,
    result_summary TEXT,
    exceptions_json TEXT,
    exceptions_count INTEGER DEFAULT 0,
    run_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    recurring BOOLEAN DEFAULT FALSE,
    status VARCHAR(50) DEFAULT 'completed'
);

CREATE TABLE IF NOT EXISTS findings (
    id SERIAL PRIMARY KEY,
    process_id INTEGER NOT NULL REFERENCES processes(id) ON DELETE CASCADE,
    finding_code VARCHAR(50) NOT NULL,
    title VARCHAR(255) NOT NULL,
    condition_text TEXT NOT NULL,
    criteria_text TEXT NOT NULL,
    cause_text TEXT NOT NULL,
    effect_text TEXT NOT NULL,
    recommendation_text TEXT NOT NULL,
    rating VARCHAR(50) DEFAULT 'Medium', -- High, Medium, Low
    linked_tests TEXT,
    linked_controls TEXT,
    status VARCHAR(50) DEFAULT 'draft', -- draft, approved
    approved_by INTEGER REFERENCES users(id),
    approved_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS review_notes (
    id SERIAL PRIMARY KEY,
    process_id INTEGER NOT NULL REFERENCES processes(id) ON DELETE CASCADE,
    target_entity VARCHAR(50),
    target_id INTEGER,
    note TEXT NOT NULL,
    raised_by INTEGER REFERENCES users(id),
    status VARCHAR(50) DEFAULT 'open', -- open, addressed, closed
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS risk_library (
    id SERIAL PRIMARY KEY,
    category VARCHAR(100) NOT NULL,
    risk_code VARCHAR(50) NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    inherent_rating_hint VARCHAR(50) DEFAULT 'Medium'
);

CREATE TABLE IF NOT EXISTS control_library (
    id SERIAL PRIMARY KEY,
    category VARCHAR(100) NOT NULL,
    control_code VARCHAR(50) NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    control_type VARCHAR(50) DEFAULT 'preventive',
    nature VARCHAR(50) DEFAULT 'automated',
    frequency_hint VARCHAR(50) DEFAULT 'per transaction'
);

CREATE TABLE IF NOT EXISTS framework_controls (
    id SERIAL PRIMARY KEY,
    framework_name VARCHAR(100) NOT NULL, -- COSO 2013, COBIT 2019, ISO 27001:2022, NCA ECC, SAMA CSF
    requirement_code VARCHAR(50) NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    mapped_control_category VARCHAR(100)
);

CREATE TABLE IF NOT EXISTS sampling_table (
    id SERIAL PRIMARY KEY,
    frequency VARCHAR(100) NOT NULL,
    risk_level VARCHAR(50) NOT NULL,
    sample_size INTEGER NOT NULL,
    rationale TEXT
);

CREATE TABLE IF NOT EXISTS sod_rules (
    id SERIAL PRIMARY KEY,
    rule_code VARCHAR(50) NOT NULL,
    function_a VARCHAR(150) NOT NULL,
    function_b VARCHAR(150) NOT NULL,
    risk_description TEXT NOT NULL,
    severity VARCHAR(50) DEFAULT 'High'
);

CREATE TABLE IF NOT EXISTS analytics_library (
    id SERIAL PRIMARY KEY,
    test_id VARCHAR(50) NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    required_fields_json TEXT NOT NULL,
    logic_code VARCHAR(100) NOT NULL
);

CREATE TABLE IF NOT EXISTS audit_log (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    action VARCHAR(100) NOT NULL,
    entity VARCHAR(100) NOT NULL,
    entity_id INTEGER,
    details_json TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS files (
    id SERIAL PRIMARY KEY,
    filename VARCHAR(255) NOT NULL,
    mime_type VARCHAR(100) NOT NULL,
    size_bytes INTEGER NOT NULL,
    data BYTEA,
    sha256 VARCHAR(64) NOT NULL,
    created_by INTEGER REFERENCES users(id),
    delete_after TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS jobs (
    id SERIAL PRIMARY KEY,
    job_type VARCHAR(100) NOT NULL,
    payload_json TEXT NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'queued', -- queued, running, waiting_review, done, failed
    progress INTEGER NOT NULL DEFAULT 0,
    message TEXT,
    thread_id VARCHAR(255),
    created_by INTEGER REFERENCES users(id),
    started_at TIMESTAMP,
    finished_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS question_packs (
    id SERIAL PRIMARY KEY,
    process_id INTEGER NOT NULL REFERENCES processes(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    scoping_json TEXT,
    questions_json TEXT NOT NULL,
    version VARCHAR(50) DEFAULT 'v1.0',
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
