BATCH3_SQL = """\
CREATE TABLE IF NOT EXISTS asr_tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id TEXT UNIQUE NOT NULL,
    file_path TEXT DEFAULT '',
    transcript TEXT DEFAULT '',
    summary TEXT DEFAULT '{}',
    status TEXT DEFAULT 'pending',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_asr_task_id ON asr_tasks(task_id);

CREATE TABLE IF NOT EXISTS admission_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    hospital_name TEXT NOT NULL,
    department TEXT DEFAULT '',
    product TEXT NOT NULL,
    status TEXT DEFAULT '待提交',
    meeting_date TEXT,
    notes TEXT DEFAULT '',
    rep_id INTEGER,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_admission_rep ON admission_records(rep_id);
CREATE INDEX IF NOT EXISTS idx_admission_status ON admission_records(status);

CREATE TABLE IF NOT EXISTS quotation_approvals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    quotation_id TEXT UNIQUE NOT NULL,
    rep_id INTEGER NOT NULL,
    product TEXT NOT NULL,
    amount REAL NOT NULL,
    limit_amount REAL DEFAULT 0.0,
    status TEXT DEFAULT 'pending_approval',
    compliance_passed INTEGER DEFAULT 0,
    review_notes TEXT DEFAULT '',
    reviewed_by INTEGER,
    reviewed_at TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_qa_status ON quotation_approvals(status);
"""
