import os
import sqlite3
from typing import Generator

import psycopg2

from shared.db import PGCompatConnection

_BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_PATH = os.path.join(_BASE_DIR, "data", "sales_coach.db")
DATABASE_URL = os.getenv("DATABASE_URL", "")

SCHEMA = """
CREATE TABLE IF NOT EXISTS training_module (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT,
    category TEXT,
    content TEXT,
    difficulty TEXT DEFAULT 'beginner',
    is_active INTEGER DEFAULT 1,
    created_by INTEGER,
    created_at TEXT,
    updated_at TEXT
);

CREATE TABLE IF NOT EXISTS coach_session (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    module_id INTEGER NOT NULL REFERENCES training_module(id),
    trainee_name TEXT,
    score INTEGER,
    feedback TEXT,
    strengths TEXT,
    improvements TEXT,
    session_date TEXT,
    session_type TEXT DEFAULT 'roleplay',
    scenario_id INTEGER,
    dialogue_log TEXT,
    role TEXT,
    compliance_violations INTEGER DEFAULT 0,
    auto_assessment TEXT,
    reflection_report TEXT,
    created_by INTEGER,
    created_at TEXT
);

CREATE TABLE IF NOT EXISTS coach_scenario (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    role_setting TEXT,
    goal TEXT,
    difficulty TEXT DEFAULT 'medium',
    category TEXT,
    content TEXT,
    tips TEXT,
    is_active INTEGER DEFAULT 1,
    created_by INTEGER,
    created_at TEXT,
    updated_at TEXT
);

CREATE TABLE IF NOT EXISTS education_assessment (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    trainee_name TEXT NOT NULL,
    assessment_date TEXT,
    current_level TEXT DEFAULT 'beginner',
    target_level TEXT DEFAULT 'intermediate',
    strengths TEXT,
    weaknesses TEXT,
    recommended_modules TEXT,
    notes TEXT,
    is_active INTEGER DEFAULT 1,
    created_by INTEGER,
    created_at TEXT,
    updated_at TEXT
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


_NEW_COACH_SESSION_COLS = [
    ("session_type", "TEXT DEFAULT 'roleplay'"),
    ("scenario_id", "INTEGER"),
    ("dialogue_log", "TEXT"),
    ("role", "TEXT"),
    ("compliance_violations", "INTEGER DEFAULT 0"),
    ("auto_assessment", "TEXT"),
    ("reflection_report", "TEXT"),
]


def _migrate_coach_session(conn: sqlite3.Connection) -> None:
    existing = {
        row[1] for row in conn.execute("PRAGMA table_info(coach_session)").fetchall()
    }
    for col_name, col_def in _NEW_COACH_SESSION_COLS:
        if col_name not in existing:
            conn.execute(f"ALTER TABLE coach_session ADD COLUMN {col_name} {col_def}")


def init_db() -> None:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.executescript(SCHEMA)
    _migrate_coach_session(conn)
    conn.commit()
    conn.close()
