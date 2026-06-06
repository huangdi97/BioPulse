"""数据库模块，提供数据库连接、建表与迁移功能。"""

import os
import sqlite3
from typing import Generator

import psycopg2

from shared.config import settings
from shared.db import PGCompatConnection

from .schema_sql import PG_SCHEMA_SQL, SCHEMA_SQL

_BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_PATH = os.path.join(_BASE_DIR, "data", "assistant.db")
DATABASE_URL = settings.ASSISTANT_DATABASE_URL


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
    if DATABASE_URL.startswith("postgresql://") or DATABASE_URL.startswith("postgres://"):
        conn = PGCompatConnection(psycopg2.connect(DATABASE_URL))
        conn.executescript(PG_SCHEMA_SQL)
        conn.commit()
        conn.close()
    else:
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        conn = sqlite3.connect(DB_PATH)
        conn.executescript(SCHEMA_SQL)
        conn.commit()
        conn.close()
        migrate_db()
