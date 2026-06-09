"""管理端数据库模块，管理配置、视图偏好与角色缓存。"""

import os

from shared.database import SQLiteDatabase

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


class ManagementDatabase(SQLiteDatabase):
    def __init__(self):
        super().__init__(db_path=DB_PATH, schema_sql=SCHEMA)


_db = ManagementDatabase()
get_db = _db.get_db
init_db = _db.init_db
