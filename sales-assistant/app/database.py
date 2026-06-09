"""数据库模块：SQLite/PostgreSQL连接管理、表结构初始化与迁移。"""

import os

from shared.config import settings
from shared.database import SQLiteDatabase

from .schema_sql import PG_SCHEMA_SQL, SCHEMA_SQL

_BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_PATH = os.path.join(_BASE_DIR, "data", "sales_assistant.db")
DATABASE_URL = settings.sales_assistant_database_url


class SalesAssistantDatabase(SQLiteDatabase):
    def __init__(self):
        super().__init__(
            db_path=DB_PATH,
            database_url=DATABASE_URL,
            schema_sql=SCHEMA_SQL,
            pg_schema_sql=PG_SCHEMA_SQL,
        )


_db = SalesAssistantDatabase()
get_db = _db.get_db
init_db = _db.init_db
