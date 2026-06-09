"""数据库模块，管理SQLite/PostgreSQL连接、表初始化及迁移。"""

import os
import sqlite3

from shared.config import settings
from shared.database import SQLiteDatabase

_BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_PATH = os.path.join(_BASE_DIR, "data", "sales_coach.db")
DATABASE_URL = settings.sales_coach_database_url

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

PG_SCHEMA = """
CREATE TABLE IF NOT EXISTS training_module (
    id SERIAL PRIMARY KEY,
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
    id SERIAL PRIMARY KEY,
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
    id SERIAL PRIMARY KEY,
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
    id SERIAL PRIMARY KEY,
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

_NEW_COACH_SESSION_COLS = [
    ("session_type", "TEXT DEFAULT 'roleplay'"),
    ("scenario_id", "INTEGER"),
    ("dialogue_log", "TEXT"),
    ("role", "TEXT"),
    ("compliance_violations", "INTEGER DEFAULT 0"),
    ("auto_assessment", "TEXT"),
    ("reflection_report", "TEXT"),
]


class SalesCoachDatabase(SQLiteDatabase):
    def __init__(self):
        super().__init__(
            db_path=DB_PATH,
            database_url=DATABASE_URL,
            schema_sql=SCHEMA,
            pg_schema_sql=PG_SCHEMA,
        )

    def _run_migrations(self, conn: sqlite3.Connection) -> None:
        self._ensure_columns(conn, "coach_session", _NEW_COACH_SESSION_COLS)


_db = SalesCoachDatabase()
get_db = _db.get_db
init_db = _db.init_db
