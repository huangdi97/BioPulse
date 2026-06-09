"""数据库模块，提供数据库连接、建表与迁移功能。"""

import os
import sqlite3

from shared.config import settings
from shared.database import SQLiteDatabase

from .schema_sql import PG_SCHEMA_SQL, SCHEMA_SQL

_BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_PATH = os.path.join(_BASE_DIR, "data", "assistant.db")
DATABASE_URL = settings.assistant_database_url


class AssistantDatabase(SQLiteDatabase):
    def __init__(self):
        super().__init__(
            db_path=DB_PATH,
            database_url=DATABASE_URL,
            schema_sql=SCHEMA_SQL,
            pg_schema_sql=PG_SCHEMA_SQL,
        )

    def _run_migrations(self, conn: sqlite3.Connection) -> None:
        for col_def in (
            "last_notified_at TEXT",
            "notification_status TEXT DEFAULT 'pending'",
        ):
            col_name = col_def.split()[0]
            existing = {row[1] for row in conn.execute("PRAGMA table_info(surgery_reminder)").fetchall()}
            if col_name not in existing:
                conn.execute(f"ALTER TABLE surgery_reminder ADD COLUMN {col_def}")


_db = AssistantDatabase()
get_db = _db.get_db
init_db = _db.init_db
