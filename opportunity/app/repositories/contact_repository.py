from typing import List
import sqlite3
from datetime import datetime, timezone

from shared.repository import BaseRepository
from shared.columns import (
    TABLE_CONTACT_RECORD_COLS,
    TABLE_OPPORTUNITY_COLS,
    TABLE_RESEARCH_TRAIL_COLS,
)


class ContactRepository(BaseRepository):
    def __init__(self, db: sqlite3.Connection):
        super().__init__(db, "contact_record", TABLE_CONTACT_RECORD_COLS)

    def search(self, keyword: str, limit: int = 50) -> List[sqlite3.Row]:
        return self.db.execute(
            """SELECT * FROM contact_record
               WHERE summary LIKE ? OR detail LIKE ? OR contact_type LIKE ?
               ORDER BY contact_date DESC LIMIT ?""",
            (f"%{keyword}%", f"%{keyword}%", f"%{keyword}%", limit),
        ).fetchall()

    def soft_delete(self, row_id: int) -> None:
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        self.db.execute(
            "UPDATE contact_record SET is_active = 0, updated_at = ? WHERE id = ?",
            (now, row_id),
        )
        self.db.commit()

    def list_by_opportunity(self, opportunity_id: int) -> List[sqlite3.Row]:
        return self.list_all(
            conditions=["opportunity_id = ?"],
            params=[opportunity_id],
            order_by="contact_date DESC",
        )

    def list_by_user(self, user_id: int) -> List[sqlite3.Row]:
        return self.list_all(
            conditions=["created_by = ?"],
            params=[user_id],
            order_by="contact_date DESC",
        )


class OpportunityRepository(BaseRepository):
    def __init__(self, db: sqlite3.Connection):
        super().__init__(db, "opportunity", TABLE_OPPORTUNITY_COLS)

    def search(self, keyword: str, limit: int = 50) -> List[sqlite3.Row]:
        return self.db.execute(
            """SELECT * FROM opportunity
               WHERE is_active = 1
                 AND (name LIKE ? OR hcp_name LIKE ? OR hospital LIKE ? OR product LIKE ?)
               ORDER BY updated_at DESC LIMIT ?""",
            (f"%{keyword}%", f"%{keyword}%", f"%{keyword}%", f"%{keyword}%", limit),
        ).fetchall()

    def soft_delete(self, row_id: int) -> None:
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        self.db.execute(
            "UPDATE opportunity SET is_active = 0, updated_at = ? WHERE id = ?",
            (now, row_id),
        )
        self.db.commit()

    def list_by_user(self, user_id: int) -> List[sqlite3.Row]:
        return self.list_all(
            conditions=["created_by = ?", "is_active = 1"],
            params=[user_id],
            order_by="updated_at DESC",
        )


class ResearchRepository(BaseRepository):
    def __init__(self, db: sqlite3.Connection):
        super().__init__(db, "research_trail", TABLE_RESEARCH_TRAIL_COLS)

    def search(self, keyword: str, limit: int = 50) -> List[sqlite3.Row]:
        return self.db.execute(
            """SELECT * FROM research_trail
               WHERE is_active = 1
                 AND (hcp_name LIKE ? OR topic LIKE ? OR paper_title LIKE ? OR journal LIKE ?)
               ORDER BY updated_at DESC LIMIT ?""",
            (f"%{keyword}%", f"%{keyword}%", f"%{keyword}%", f"%{keyword}%", limit),
        ).fetchall()

    def soft_delete(self, row_id: int) -> None:
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        self.db.execute(
            "UPDATE research_trail SET is_active = 0, updated_at = ? WHERE id = ?",
            (now, row_id),
        )
        self.db.commit()

    def list_by_user(self, user_id: int) -> List[sqlite3.Row]:
        return self.list_all(
            conditions=["created_by = ?", "is_active = 1"],
            params=[user_id],
            order_by="updated_at DESC",
        )
