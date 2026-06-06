import os
import sqlite3
from typing import Generator

import psycopg2

from shared.config import settings
from shared.db import PGCompatConnection

from .schema_sql import PG_SCHEMA_SQL, SCHEMA_SQL

_BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_PATH = os.path.join(_BASE_DIR, "data", "opportunity.db")
DATABASE_URL = settings.OPPORTUNITY_DATABASE_URL


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
        try:
            conn.execute("ALTER TABLE opportunity ADD COLUMN heat_score INTEGER DEFAULT 0")
            conn.commit()
        except sqlite3.OperationalError:
            pass  # 兼容操作：列已存在时跳过
        conn.close()
