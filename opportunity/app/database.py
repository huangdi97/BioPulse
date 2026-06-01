import os
import sqlite3
from typing import Generator

import psycopg2

from shared.db import PGCompatConnection

_BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_PATH = os.path.join(_BASE_DIR, "data", "opportunity.db")
DATABASE_URL = os.getenv("DATABASE_URL", "")

SCHEMA = """
CREATE TABLE IF NOT EXISTS opportunity (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    hcp_name TEXT,
    hospital TEXT,
    department TEXT,
    product TEXT,
    estimated_value REAL,
    stage TEXT DEFAULT 'lead',
    probability INTEGER DEFAULT 10,
    expected_close_date TEXT,
    notes TEXT,
    is_active INTEGER DEFAULT 1,
    heat_score INTEGER DEFAULT 0,
    created_by INTEGER,
    created_at TEXT,
    updated_at TEXT
);

CREATE TABLE IF NOT EXISTS contact_record (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    opportunity_id INTEGER NOT NULL REFERENCES opportunity(id),
    contact_type TEXT,
    summary TEXT,
    detail TEXT,
    contact_date TEXT,
    created_by INTEGER,
    created_at TEXT
);

CREATE TABLE IF NOT EXISTS bidding_info (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    hospital TEXT,
    department TEXT,
    product_category TEXT,
    budget REAL,
    publish_date TEXT,
    deadline TEXT,
    status TEXT DEFAULT 'new',
    source_url TEXT,
    summary TEXT,
    analysis TEXT,
    notes TEXT,
    is_active INTEGER DEFAULT 1,
    created_by INTEGER,
    created_at TEXT,
    updated_at TEXT
);

CREATE TABLE IF NOT EXISTS research_trail (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    hcp_name TEXT NOT NULL,
    topic TEXT NOT NULL,
    paper_title TEXT,
    authors TEXT,
    journal TEXT,
    pub_date TEXT,
    pubmed_id TEXT,
    url TEXT,
    summary TEXT,
    relevance INTEGER DEFAULT 5,
    is_active INTEGER DEFAULT 1,
    created_by INTEGER,
    created_at TEXT,
    updated_at TEXT
);

CREATE TABLE IF NOT EXISTS user_bookmark (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_type TEXT NOT NULL,
    entity_id INTEGER NOT NULL,
    title TEXT,
    notes TEXT,
    created_by INTEGER,
    created_at TEXT,
    UNIQUE(entity_type, entity_id, created_by)
);

CREATE TABLE IF NOT EXISTS paper_integrity (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pubmed_id TEXT,
    doi TEXT,
    title TEXT,
    integrity_score INTEGER DEFAULT 50,
    retraction_warning INTEGER DEFAULT 0,
    concerns TEXT,
    flags TEXT,
    checked_at TEXT,
    check_count INTEGER DEFAULT 0,
    is_active INTEGER DEFAULT 1,
    created_by INTEGER,
    created_at TEXT,
    updated_at TEXT
);

CREATE TABLE IF NOT EXISTS trend_analysis (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    topic TEXT NOT NULL,
    analysis_type TEXT NOT NULL,
    period TEXT,
    data_summary TEXT,
    result TEXT,
    confidence TEXT DEFAULT 'medium',
    analyzed_at TEXT,
    created_by INTEGER,
    created_at TEXT
);

CREATE TABLE IF NOT EXISTS bidding_agent_config (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    keywords TEXT,
    regions TEXT,
    auto_parse INTEGER DEFAULT 1,
    auto_notify INTEGER DEFAULT 1,
    notify_to TEXT,
    schedule_interval INTEGER DEFAULT 360,
    is_active INTEGER DEFAULT 1,
    created_by INTEGER,
    created_at TEXT,
    updated_at TEXT
);

CREATE TABLE IF NOT EXISTS bidding_agent_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    config_id INTEGER REFERENCES bidding_agent_config(id),
    run_status TEXT,
    items_found INTEGER DEFAULT 0,
    items_parsed INTEGER DEFAULT 0,
    error_message TEXT,
    started_at TEXT,
    completed_at TEXT,
    created_at TEXT
);
"""


def get_db() -> Generator:
    if DATABASE_URL.startswith("postgresql://") or DATABASE_URL.startswith(
        "postgres://"
    ):
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


def init_db() -> None:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.executescript(SCHEMA)
    try:
        conn.execute("ALTER TABLE opportunity ADD COLUMN heat_score INTEGER DEFAULT 0")
        conn.commit()
    except sqlite3.OperationalError:
        pass
    conn.close()
