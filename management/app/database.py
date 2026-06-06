"""管理端数据库模块，管理配置、视图偏好与角色缓存。"""

import os
import sqlite3
from typing import Generator

_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(os.path.dirname(_BASE_DIR), "data", "management.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS management_config (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS view_preferences (
    user_id TEXT NOT NULL,
    view_type TEXT NOT NULL,
    config TEXT NOT NULL DEFAULT '{}',
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    PRIMARY KEY (user_id, view_type)
);

CREATE TABLE IF NOT EXISTS role_cache (
    user_id TEXT PRIMARY KEY,
    role TEXT NOT NULL,
    permissions TEXT NOT NULL DEFAULT '[]',
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);
"""


def get_db() -> Generator:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    try:
        yield conn
    finally:
        conn.close()


def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.executescript(SCHEMA)
    conn.commit()
    conn.close()
