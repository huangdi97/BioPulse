"""科研数据库服务层。"""

import os
import sqlite3

from cloud.app.research_database import RESEARCH_DB_PATH

_TEST_RESEARCH_DB_PATH = None


def _get_research_db_path() -> str:
    return _TEST_RESEARCH_DB_PATH or RESEARCH_DB_PATH


def set_test_research_db_path(path: str):
    global _TEST_RESEARCH_DB_PATH
    _TEST_RESEARCH_DB_PATH = path


class ResearchService:
    @staticmethod
    def get_research_db() -> sqlite3.Connection:
        db_path = _get_research_db_path()
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        return conn

    @staticmethod
    def log_audit(
        event_type: str,
        entity_type: str,
        entity_id: int,
        old_value: str | None = None,
        new_value: str | None = None,
        operator: str = "",
    ) -> None:
        conn = ResearchService.get_research_db()
        try:
            conn.execute(
                "INSERT INTO research_audit_log (event_type, entity_type, entity_id, old_value, new_value, operator, timestamp) "
                "VALUES (?, ?, ?, ?, ?, ?, datetime('now'))",
                (event_type, entity_type, entity_id, old_value, new_value, operator),
            )
            conn.commit()
        finally:
            conn.close()
