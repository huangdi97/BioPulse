"""数据库模块，管理 SQLite/PostgreSQL 连接、Schema 初始化与迁移。"""

import os
import sqlite3

from shared.config import settings
from shared.database import SQLiteDatabase

from .schema_sql import PG_SCHEMA_SQL, SCHEMA_SQL

_BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_PATH = os.path.join(_BASE_DIR, "data", "opportunity.db")
DATABASE_URL = settings.opportunity_database_url


class OpportunityDatabase(SQLiteDatabase):
    def __init__(self):
        super().__init__(
            db_path=DB_PATH,
            database_url=DATABASE_URL,
            schema_sql=SCHEMA_SQL,
            pg_schema_sql=PG_SCHEMA_SQL,
        )

    def _run_migrations(self, conn: sqlite3.Connection) -> None:
        self._ensure_columns(conn, "opportunity", [("heat_score", "INTEGER DEFAULT 0")])


_db = OpportunityDatabase()
get_db = _db.get_db
init_db = _db.init_db
