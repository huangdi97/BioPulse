"""数据库 SCHEMA SQL 字符串，包含 SQLite 和 PostgreSQL 两个版本。"""

_BASE_TABLES = """
CREATE TABLE IF NOT EXISTS hcp (
    id {pk},
    name TEXT NOT NULL,
    hospital TEXT NOT NULL,
    department TEXT,
    title TEXT,
    specialty TEXT,
    phone TEXT,
    wechat TEXT,
    email TEXT,
    level TEXT DEFAULT 'C',
    is_active INTEGER DEFAULT 1,
    created_by INTEGER,
    created_at TEXT,
    updated_at TEXT
);

CREATE TABLE IF NOT EXISTS visit_record (
    id {pk},
    hcp_id INTEGER NOT NULL REFERENCES hcp(id),
    visit_type TEXT,
    summary TEXT,
    detail TEXT,
    feedback TEXT,
    next_action TEXT,
    mood TEXT,
    is_completed INTEGER DEFAULT 1,
    visit_date TEXT,
    created_by INTEGER,
    created_at TEXT
);

CREATE TABLE IF NOT EXISTS task (
    id {pk},
    hcp_id INTEGER REFERENCES hcp(id),
    title TEXT NOT NULL,
    description TEXT,
    priority TEXT DEFAULT 'normal',
    status TEXT DEFAULT 'pending',
    due_date TEXT,
    created_by INTEGER,
    created_at TEXT
);

CREATE TABLE IF NOT EXISTS health_radar (
    id {pk},
    patient_name TEXT NOT NULL,
    age INTEGER,
    gender TEXT,
    diagnosis TEXT,
    risk_factors TEXT,
    medication_history TEXT,
    score INTEGER DEFAULT 50,
    assessment_date TEXT,
    notes TEXT,
    is_active INTEGER DEFAULT 1,
    created_by INTEGER,
    created_at TEXT,
    updated_at TEXT
);

CREATE TABLE IF NOT EXISTS surgery_reminder (
    id {pk},
    patient_name TEXT NOT NULL,
    surgery_type TEXT,
    surgery_date TEXT,
    hospital TEXT,
    department TEXT,
    surgeon_name TEXT,
    pre_op_notes TEXT,
    post_op_notes TEXT,
    status TEXT DEFAULT 'scheduled',
    reminder_before INTEGER DEFAULT 1,
    last_notified_at TEXT,
    notification_status TEXT DEFAULT 'pending',
    is_active INTEGER DEFAULT 1,
    created_by INTEGER,
    created_at TEXT,
    updated_at TEXT
);

CREATE TABLE IF NOT EXISTS knowledge_base (
    id {pk},
    title TEXT NOT NULL,
    category TEXT,
    content TEXT NOT NULL,
    tags TEXT,
    source TEXT,
    difficulty TEXT DEFAULT 'medium',
    is_active INTEGER DEFAULT 1,
    created_by INTEGER,
    created_at TEXT,
    updated_at TEXT
);

CREATE TABLE IF NOT EXISTS hcp_location (
    id {pk},
    hcp_id INTEGER NOT NULL REFERENCES hcp(id),
    address TEXT NOT NULL,
    latitude REAL,
    longitude REAL,
    is_primary INTEGER DEFAULT 1,
    notes TEXT,
    is_active INTEGER DEFAULT 1,
    created_by INTEGER,
    created_at TEXT,
    updated_at TEXT
);

CREATE TABLE IF NOT EXISTS sync_queue (
    id {pk},
    client_id TEXT NOT NULL,
    action TEXT NOT NULL,
    entity_type TEXT NOT NULL,
    entity_id INTEGER,
    payload TEXT NOT NULL,
    status TEXT DEFAULT 'pending',
    client_created_at TEXT NOT NULL,
    synced_at TEXT,
    created_by INTEGER,
    created_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_sync_client ON sync_queue(client_id, status);
CREATE INDEX IF NOT EXISTS idx_sync_status ON sync_queue(status);

CREATE TABLE IF NOT EXISTS media_file (
    id {pk},
    file_type TEXT NOT NULL,
    original_name TEXT,
    storage_path TEXT NOT NULL,
    mime_type TEXT,
    file_size INTEGER,
    transcript TEXT,
    analysis_result TEXT,
    is_active INTEGER DEFAULT 1,
    created_by INTEGER,
    created_at TEXT
);
"""

_SQLITE_ONLY = """
CREATE VIRTUAL TABLE IF NOT EXISTS knowledge_fts USING fts5(
    title, content, tags,
    content=knowledge_base,
    content_rowid=id
);

CREATE TRIGGER IF NOT EXISTS knowledge_ai AFTER INSERT ON knowledge_base BEGIN
    INSERT INTO knowledge_fts(rowid, title, content, tags)
    VALUES (new.id, new.title, new.content, new.tags);
END;

CREATE TRIGGER IF NOT EXISTS knowledge_ad AFTER DELETE ON knowledge_base BEGIN
    INSERT INTO knowledge_fts(knowledge_fts, rowid, title, content, tags)
    VALUES ('delete', old.id, old.title, old.content, old.tags);
END;

CREATE TRIGGER IF NOT EXISTS knowledge_au AFTER UPDATE ON knowledge_base BEGIN
    INSERT INTO knowledge_fts(knowledge_fts, rowid, title, content, tags)
    VALUES ('delete', old.id, old.title, old.content, old.tags);
    INSERT INTO knowledge_fts(rowid, title, content, tags)
    VALUES (new.id, new.title, new.content, new.tags);
END;
"""

SCHEMA_SQL = _BASE_TABLES.replace("{pk}", "INTEGER PRIMARY KEY AUTOINCREMENT") + _SQLITE_ONLY
PG_SCHEMA_SQL = _BASE_TABLES.replace("{pk}", "SERIAL PRIMARY KEY")
