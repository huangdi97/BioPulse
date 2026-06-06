import sqlite3
from datetime import datetime, timezone
from typing import List, Optional

from shared.columns import (
    TABLE_BIDDING_AGENT_CONFIG_COLS,
    TABLE_BIDDING_AGENT_LOG_COLS,
    TABLE_BIDDING_INFO_COLS,
    TABLE_USER_BOOKMARK_COLS,
)
from shared.repository import BaseRepository


class BiddingInfoRepository(BaseRepository):
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


class UserBookmarkRepository(BaseRepository):
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


class BiddingAgentConfigRepository(BaseRepository):
    def __init__(self, db: sqlite3.Connection):
        super().__init__(db, "bidding_agent_config", TABLE_BIDDING_AGENT_CONFIG_COLS)

    def search(self, keyword: str, limit: int = 50) -> List[sqlite3.Row]:
        return self.db.execute(
            """SELECT * FROM bidding_agent_config
               WHERE is_active = 1
                 AND (name LIKE ? OR keywords LIKE ? OR regions LIKE ?)
               ORDER BY updated_at DESC LIMIT ?""",
            (f"%{keyword}%", f"%{keyword}%", f"%{keyword}%", limit),
        ).fetchall()

    def soft_delete(self, row_id: int) -> None:
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        self.db.execute(
            "UPDATE bidding_agent_config SET is_active = 0, updated_at = ? WHERE id = ?",
            (now, row_id),
        )
        self.db.commit()

    def list_by_user(self, user_id: int) -> List[sqlite3.Row]:
        return self.list_all(
            conditions=["created_by = ?", "is_active = 1"],
            params=[user_id],
            order_by="updated_at DESC",
        )


class BiddingAgentLogRepository(BaseRepository):
    def __init__(self, db: sqlite3.Connection):
        super().__init__(db, "bidding_agent_log", TABLE_BIDDING_AGENT_LOG_COLS)

    def search(self, keyword: str, limit: int = 50) -> List[sqlite3.Row]:
        return self.db.execute(
            """SELECT * FROM bidding_agent_log
               WHERE run_status LIKE ? OR error_message LIKE ?
               ORDER BY started_at DESC LIMIT ?""",
            (f"%{keyword}%", f"%{keyword}%", f"%{keyword}%", limit),
        ).fetchall()

    def soft_delete(self, row_id: int) -> None:
        self.db.execute("DELETE FROM bidding_agent_log WHERE id = ?", (row_id,))
        self.db.commit()

    def list_by_config(self, config_id: int) -> List[sqlite3.Row]:
        return self.list_all(
            conditions=["config_id = ?"],
            params=[config_id],
            order_by="started_at DESC",
        )
