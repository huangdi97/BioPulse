from typing import Optional, List, Any
import sqlite3
from datetime import datetime, timezone

from shared.repository import BaseRepository
from shared.columns import (
    TABLE_BIDDING_INFO_COLS,
    TABLE_BIDDING_AGENT_CONFIG_COLS,
    TABLE_BIDDING_AGENT_LOG_COLS,
    TABLE_USER_BOOKMARK_COLS,
)


class BiddingRepository(BaseRepository):
    def __init__(self, db: sqlite3.Connection):
        super().__init__(db, "bidding_info", TABLE_BIDDING_INFO_COLS)

    def search(self, keyword: str, limit: int = 50) -> List[sqlite3.Row]:
        return self.db.execute(
            """SELECT * FROM bidding_info
               WHERE is_active = 1
                 AND (title LIKE ? OR hospital LIKE ? OR department LIKE ? OR summary LIKE ?)
               ORDER BY updated_at DESC LIMIT ?""",
            (f"%{keyword}%", f"%{keyword}%", f"%{keyword}%", f"%{keyword}%", limit),
        ).fetchall()

    def soft_delete(self, row_id: int) -> None:
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        self.db.execute(
            "UPDATE bidding_info SET is_active = 0, updated_at = ? WHERE id = ?",
            (now, row_id),
        )
        self.db.commit()

    def list_by_user(self, user_id: int) -> List[sqlite3.Row]:
        return self.list_all(
            conditions=["created_by = ?", "is_active = 1"],
            params=[user_id],
            order_by="updated_at DESC",
        )


class BiddingAgentRepository:
    def __init__(self, db: sqlite3.Connection):
        self.db = db

    def create_config(self, data: dict, extra: Optional[dict] = None) -> int:
        if extra:
            data = {**data, **extra}
        cols = ", ".join(data.keys())
        vals = ", ".join("?" for _ in data)
        cur = self.db.execute(
            f"INSERT INTO bidding_agent_config ({cols}) VALUES ({vals})",
            list(data.values()),
        )
        self.db.commit()
        return cur.lastrowid

    def get_config(self, config_id: int) -> Optional[sqlite3.Row]:
        return self.db.execute(
            "SELECT * FROM bidding_agent_config WHERE id = ?", (config_id,)
        ).fetchone()

    def list_configs(
        self, conditions: Optional[List[str]] = None, params: Optional[List[Any]] = None
    ) -> List[sqlite3.Row]:
        where = ""
        if conditions:
            where = " WHERE " + " AND ".join(conditions)
        return self.db.execute(
            f"SELECT * FROM bidding_agent_config{where} ORDER BY id DESC",
            params or [],
        ).fetchall()

    def search_configs(self, keyword: str, limit: int = 50) -> List[sqlite3.Row]:
        return self.db.execute(
            """SELECT * FROM bidding_agent_config
               WHERE is_active = 1
                 AND (name LIKE ? OR keywords LIKE ? OR regions LIKE ?)
               ORDER BY updated_at DESC LIMIT ?""",
            (f"%{keyword}%", f"%{keyword}%", f"%{keyword}%", limit),
        ).fetchall()

    def update_config(self, config_id: int, updates: dict) -> None:
        if not updates:
            return
        set_clause = ", ".join(f"{k}=?" for k in updates)
        self.db.execute(
            f"UPDATE bidding_agent_config SET {set_clause} WHERE id=?",
            list(updates.values()) + [config_id],
        )
        self.db.commit()

    def soft_delete_config(self, row_id: int) -> None:
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        self.db.execute(
            "UPDATE bidding_agent_config SET is_active = 0, updated_at = ? WHERE id = ?",
            (now, row_id),
        )
        self.db.commit()

    def list_configs_by_user(self, user_id: int) -> List[sqlite3.Row]:
        return self.list_configs(
            conditions=["created_by = ?", "is_active = 1"],
            params=[user_id],
        )

    def create_log(self, data: dict) -> int:
        cols = ", ".join(data.keys())
        vals = ", ".join("?" for _ in data)
        cur = self.db.execute(
            f"INSERT INTO bidding_agent_log ({cols}) VALUES ({vals})",
            list(data.values()),
        )
        self.db.commit()
        return cur.lastrowid

    def list_logs(self, page: int = 1, page_size: int = 20) -> tuple:
        total = self.db.execute(
            "SELECT COUNT(*) FROM bidding_agent_log"
        ).fetchone()[0]
        total_pages = max(1, (total + page_size - 1) // page_size)
        offset = (page - 1) * page_size
        rows = self.db.execute(
            "SELECT * FROM bidding_agent_log ORDER BY id DESC LIMIT ? OFFSET ?",
            (page_size, offset),
        ).fetchall()
        return total, total_pages, rows

    def list_logs_by_config(self, config_id: int) -> List[sqlite3.Row]:
        return self.db.execute(
            "SELECT * FROM bidding_agent_log WHERE config_id = ? ORDER BY started_at DESC",
            (config_id,),
        ).fetchall()

    def search_logs(self, keyword: str, limit: int = 50) -> List[sqlite3.Row]:
        return self.db.execute(
            """SELECT * FROM bidding_agent_log
               WHERE run_status LIKE ? OR error_message LIKE ?
               ORDER BY started_at DESC LIMIT ?""",
            (f"%{keyword}%", f"%{keyword}%", limit),
        ).fetchall()

    def get_status(self) -> dict:
        last = self.db.execute(
            "SELECT started_at FROM bidding_agent_log ORDER BY id DESC LIMIT 1"
        ).fetchone()
        stats = self.db.execute(
            """SELECT COUNT(*) as total,
                      SUM(CASE WHEN run_status='success' THEN 1 ELSE 0 END) as success
               FROM bidding_agent_log"""
        ).fetchone()
        total_runs = stats["total"] or 0
        success_count = stats["success"] or 0
        success_rate = round(success_count / total_runs * 100, 1) if total_runs > 0 else 0.0
        return {
            "last_run": last["started_at"] if last else None,
            "total_runs": total_runs,
            "success_rate": success_rate,
        }


class BookmarkRepository(BaseRepository):
    def __init__(self, db: sqlite3.Connection):
        super().__init__(db, "user_bookmark", TABLE_USER_BOOKMARK_COLS)

    def search(self, keyword: str, limit: int = 50) -> List[sqlite3.Row]:
        return self.db.execute(
            """SELECT * FROM user_bookmark
               WHERE title LIKE ? OR notes LIKE ? OR entity_type LIKE ?
               ORDER BY created_at DESC LIMIT ?""",
            (f"%{keyword}%", f"%{keyword}%", f"%{keyword}%", limit),
        ).fetchall()

    def soft_delete(self, row_id: int) -> None:
        self.db.execute("DELETE FROM user_bookmark WHERE id = ?", (row_id,))
        self.db.commit()

    def list_by_user(self, user_id: int) -> List[sqlite3.Row]:
        return self.list_all(
            conditions=["created_by = ?"],
            params=[user_id],
            order_by="created_at DESC",
        )

    def get_by_entity(self, entity_type: str, entity_id: int, user_id: int) -> Optional[sqlite3.Row]:
        return self.db.execute(
            """SELECT * FROM user_bookmark
               WHERE entity_type = ? AND entity_id = ? AND created_by = ?""",
            (entity_type, entity_id, user_id),
        ).fetchone()
