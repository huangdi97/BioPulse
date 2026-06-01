import sqlite3
from datetime import datetime, timezone
from typing import List, Optional

from shared.columns import (
    TABLE_BIDDING_AGENT_CONFIG_COLS,
    TABLE_BIDDING_AGENT_LOG_COLS,
    TABLE_BIDDING_INFO_COLS,
    TABLE_CONTACT_RECORD_COLS,
    TABLE_OPPORTUNITY_COLS,
    TABLE_PAPER_INTEGRITY_COLS,
    TABLE_RESEARCH_TRAIL_COLS,
    TABLE_TREND_ANALYSIS_COLS,
    TABLE_USER_BOOKMARK_COLS,
)
from shared.repository import BaseRepository


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


class ContactRecordRepository(BaseRepository):
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


class ResearchTrailRepository(BaseRepository):
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


class PaperIntegrityRepository(BaseRepository):
    def __init__(self, db: sqlite3.Connection):
        super().__init__(db, "paper_integrity", TABLE_PAPER_INTEGRITY_COLS)

    def search(self, keyword: str, limit: int = 50) -> List[sqlite3.Row]:
        return self.db.execute(
            """SELECT * FROM paper_integrity
               WHERE is_active = 1
                 AND (title LIKE ? OR pubmed_id LIKE ? OR doi LIKE ? OR concerns LIKE ?)
               ORDER BY updated_at DESC LIMIT ?""",
            (f"%{keyword}%", f"%{keyword}%", f"%{keyword}%", f"%{keyword}%", limit),
        ).fetchall()

    def soft_delete(self, row_id: int) -> None:
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        self.db.execute(
            "UPDATE paper_integrity SET is_active = 0, updated_at = ? WHERE id = ?",
            (now, row_id),
        )
        self.db.commit()

    def list_by_user(self, user_id: int) -> List[sqlite3.Row]:
        return self.list_all(
            conditions=["created_by = ?", "is_active = 1"],
            params=[user_id],
            order_by="updated_at DESC",
        )

    def get_by_pubmed_id(self, pubmed_id: str) -> Optional[sqlite3.Row]:
        return self.db.execute(
            "SELECT * FROM paper_integrity WHERE pubmed_id = ? AND is_active = 1",
            (pubmed_id,),
        ).fetchone()


class TrendAnalysisRepository(BaseRepository):
    def __init__(self, db: sqlite3.Connection):
        super().__init__(db, "trend_analysis", TABLE_TREND_ANALYSIS_COLS)

    def search(self, keyword: str, limit: int = 50) -> List[sqlite3.Row]:
        return self.db.execute(
            """SELECT * FROM trend_analysis
               WHERE topic LIKE ? OR result LIKE ? OR analysis_type LIKE ?
               ORDER BY analyzed_at DESC LIMIT ?""",
            (f"%{keyword}%", f"%{keyword}%", f"%{keyword}%", limit),
        ).fetchall()

    def soft_delete(self, row_id: int) -> None:
        self.db.execute("DELETE FROM trend_analysis WHERE id = ?", (row_id,))
        self.db.commit()

    def list_by_user(self, user_id: int) -> List[sqlite3.Row]:
        return self.list_all(
            conditions=["created_by = ?"],
            params=[user_id],
            order_by="analyzed_at DESC",
        )


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


class StatsRepository:
    def __init__(self, db: sqlite3.Connection):
        self.db = db
        self.table = "opportunity"

    def _build_where(
        self,
        conditions: list,
        params: list,
        start_date: str | None,
        end_date: str | None,
    ) -> None:
        if start_date:
            conditions.append("created_at >= ?")
            params.append(start_date)
        if end_date:
            conditions.append("created_at <= ?")
            params.append(end_date)

    def _where_clause(self, start_date: str | None, end_date: str | None) -> tuple[str, list]:
        conditions = ["is_active = 1"]
        params: list = []
        self._build_where(conditions, params, start_date, end_date)
        return "WHERE " + " AND ".join(conditions), params

    def get_totals(self, start_date: str | None = None, end_date: str | None = None):
        where, params = self._where_clause(start_date, end_date)
        row = self.db.execute(
            f"SELECT COUNT(*), COALESCE(SUM(estimated_value), 0) FROM {self.table} {where}",
            params,
        ).fetchone()
        return row[0], row[1]

    def get_by_stage(self, start_date: str | None = None, end_date: str | None = None) -> List[sqlite3.Row]:
        where, params = self._where_clause(start_date, end_date)
        return self.db.execute(
            f"SELECT stage, COUNT(*), COALESCE(SUM(estimated_value), 0) FROM {self.table} {where} GROUP BY stage",
            params,
        ).fetchall()

    def get_by_product(self, start_date: str | None = None, end_date: str | None = None) -> List[sqlite3.Row]:
        where, params = self._where_clause(start_date, end_date)
        return self.db.execute(
            f"SELECT product, COUNT(*), COALESCE(SUM(estimated_value), 0) FROM {self.table} {where} AND product IS NOT NULL GROUP BY product",
            params,
        ).fetchall()
