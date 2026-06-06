"""数据库模块，提供数据库连接、建表与迁移功能。"""

import os
import sqlite3
from typing import Generator

import psycopg2

from shared.config import settings
from shared.db import PGCompatConnection

_BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_PATH = os.path.join(_BASE_DIR, "data", "assistant.db")
DATABASE_URL = settings.DATABASE_URL

SCHEMA = """
CREATE TABLE IF NOT EXISTS hcp (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
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
    id INTEGER PRIMARY KEY AUTOINCREMENT,
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
    id INTEGER PRIMARY KEY AUTOINCREMENT,
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
    id INTEGER PRIMARY KEY AUTOINCREMENT,
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
    id INTEGER PRIMARY KEY AUTOINCREMENT,
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
    id INTEGER PRIMARY KEY AUTOINCREMENT,
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

CREATE TABLE IF NOT EXISTS hcp_location (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
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
    id INTEGER PRIMARY KEY AUTOINCREMENT,
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
    id INTEGER PRIMARY KEY AUTOINCREMENT,
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


def get_db() -> Generator:
    if DATABASE_URL.startswith("postgresql://") or DATABASE_URL.startswith("postgres://"):
        conn = PGCompatConnection(psycopg2.connect(DATABASE_URL))
        try:
            yield conn
        finally:
            conn.close()
    else:
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        try:
            yield conn
        finally:
            conn.close()


def migrate_db() -> None:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    for col in (
        "last_notified_at TEXT",
        "notification_status TEXT DEFAULT 'pending'",
    ):
        try:
            c.execute(f"ALTER TABLE surgery_reminder ADD COLUMN {col}")
        except sqlite3.OperationalError:
            pass
    conn.commit()
    conn.close()


def init_db() -> None:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.executescript(SCHEMA)
    conn.commit()
    conn.close()
    migrate_db()
